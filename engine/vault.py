import os
import sys
import json
import base64
import hashlib
import shutil
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
VAULT_FILE = BASE_DIR / "data" / "vault.enc"

class EncryptedVault:
    """
    Secure Local Credential & API Key Vault.
    Bridges to system keyring (libsecret/secret-tool on Linux) with a machine-bound
    PBKDF2 encrypted local fallback for zero-dependency operation.
    """
    def __init__(self):
        self._key = self._derive_machine_key()
        VAULT_FILE.parent.mkdir(parents=True, exist_ok=True)

    def _derive_machine_key(self) -> bytes:
        """Derives a deterministic 256-bit machine-specific key."""
        unique_id = ""
        try:
            if sys.platform == "linux":
                # Linux machine-id
                for p in ["/etc/machine-id", "/var/lib/dbus/machine-id"]:
                    if os.path.exists(p):
                        unique_id = open(p).read().strip()
                        break
            elif sys.platform == "win32":
                import subprocess
                cmd = "Get-CimInstance -Class Win32_ComputerSystemProduct | Select-Object -ExpandProperty UUID"
                res = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True)
                unique_id = res.stdout.strip()
        except Exception:
            pass

        if not unique_id:
            unique_id = os.getenv("COMPUTERNAME", os.getenv("HOSTNAME", "ZiaDefaultHost"))

        salt = b"ProjectZiaVaultSalt2026"
        return hashlib.pbkdf2_hmac("sha256", unique_id.encode("utf-8"), salt, 100000)

    def _encrypt(self, raw_bytes: bytes) -> str:
        # Keystream XOR with SHA256-derived stream
        h = hashlib.sha256(self._key + b"StreamKey").digest()
        enc = bytes([b ^ h[i % len(h)] for i, b in enumerate(raw_bytes)])
        return base64.b64encode(enc).decode("utf-8")

    def _decrypt(self, enc_str: str) -> bytes:
        raw_enc = base64.b64decode(enc_str.encode("utf-8"))
        h = hashlib.sha256(self._key + b"StreamKey").digest()
        return bytes([b ^ h[i % len(h)] for i, b in enumerate(raw_enc)])

    def _load_data(self) -> dict:
        if not VAULT_FILE.exists():
            return {}
        try:
            content = VAULT_FILE.read_text(encoding="utf-8").strip()
            if not content:
                return {}
            dec = self._decrypt(content)
            return json.loads(dec.decode("utf-8"))
        except Exception:
            return {}

    def _save_data(self, data: dict):
        raw = json.dumps(data).encode("utf-8")
        enc = self._encrypt(raw)
        VAULT_FILE.write_text(enc, encoding="utf-8")

    def store_credential(self, service: str, key_name: str, secret_value: str) -> dict:
        """Stores a credential or API key in the encrypted vault."""
        service = service.lower().strip()
        key_name = key_name.strip()

        # Try system secret-tool on Linux first
        if sys.platform == "linux" and shutil.which("secret-tool"):
            try:
                cmd = f"secret-tool store --label='Zia_{service}_{key_name}' service '{service}' user '{key_name}'"
                proc = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, text=True)
                proc.communicate(input=secret_value)
            except Exception:
                pass

        data = self._load_data()
        if service not in data:
            data[service] = {}
        data[service][key_name] = secret_value
        self._save_data(data)

        return {"success": True, "service": service, "key": key_name, "message": f"Credential '{key_name}' for '{service}' safely encrypted."}

    def get_credential(self, service: str, key_name: str = None) -> dict:
        """Retrieves a credential from the vault."""
        service = service.lower().strip()

        # Try system secret-tool on Linux
        if sys.platform == "linux" and shutil.which("secret-tool") and key_name:
            try:
                res = subprocess.run(f"secret-tool lookup service '{service}' user '{key_name}'", shell=True, capture_output=True, text=True)
                val = res.stdout.strip()
                if val:
                    return {"success": True, "service": service, "key": key_name, "value": val}
            except Exception:
                pass

        data = self._load_data()
        if service not in data:
            return {"success": False, "error": f"No credentials stored for service '{service}'."}

        svc_keys = data[service]
        if key_name:
            if key_name in svc_keys:
                return {"success": True, "service": service, "key": key_name, "value": svc_keys[key_name]}
            return {"success": False, "error": f"Key '{key_name}' not found under service '{service}'."}

        return {"success": True, "service": service, "keys": list(svc_keys.keys())}

    def list_services(self) -> dict:
        """Lists all stored services and keys without revealing secret values."""
        data = self._load_data()
        summary = {}
        for svc, keys in data.items():
            summary[svc] = list(keys.keys())
        return {"services": summary, "count": len(summary)}

    def delete_credential(self, service: str, key_name: str = None) -> dict:
        """Deletes a key or an entire service from the vault."""
        service = service.lower().strip()
        data = self._load_data()
        if service not in data:
            return {"success": False, "error": f"Service '{service}' not found."}

        if key_name:
            if key_name in data[service]:
                del data[service][key_name]
                if not data[service]:
                    del data[service]
                self._save_data(data)
                return {"success": True, "message": f"Removed key '{key_name}' from '{service}'."}
            return {"success": False, "error": f"Key '{key_name}' not found under '{service}'."}

        del data[service]
        self._save_data(data)
        return {"success": True, "message": f"Deleted service '{service}' from vault."}

encrypted_vault = EncryptedVault()

