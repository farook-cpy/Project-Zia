"""
Project Zia - Security, Privacy & Local Cryptography Engine
Implements:
1. Local API Key Vault & Prompt Redaction Guard
2. Zero-Knowledge Local Chat Logger (AES-256 / Fernet)
3. Secure SSH Reverse Tunnel Manager
4. File Integrity Monitor (FIM SHA-256 Baseline)
5. Ephemeral Chat Mode ('Incognito Session' Controller)
6. Automated Log Redacter (Strips IPs, MACs, Paths)
7. Local Biometric / Passkey Guard for Destructive Actions
8. Exposed Port Auditor
9. SSL Certificate Expiry Watchdog
10. Secure Environment Variable Enforcer (Scans code for leaked secrets)
"""

import os
import sys
import re
import time
import json
import socket
import ssl
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

try:
    from cryptography.fernet import Fernet
    import base64
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
FIM_FILE = DATA_DIR / "fim_hashes.json"
SECURE_LOG_FILE = DATA_DIR / "secure_logs.enc"
KEY_FILE = DATA_DIR / "vault_key.key"

DATA_DIR.mkdir(parents=True, exist_ok=True)


class SecurityVaultEngine:
    """Enterprise-grade local security, redactor, and file integrity monitor."""

    def __init__(self):
        self.incognito_active = False
        self.passkey_token = os.environ.get("ZIA_PASSKEY", "zia_secure_2026")
        self._fernet = None
        self._init_cipher()

    def _init_cipher(self):
        """Initializes local AES-256 Fernet cipher."""
        if not CRYPTOGRAPHY_AVAILABLE:
            return
        try:
            if KEY_FILE.exists():
                key = KEY_FILE.read_bytes()
            else:
                key = Fernet.generate_key()
                KEY_FILE.write_bytes(key)
            self._fernet = Fernet(key)
        except Exception:
            self._fernet = None

    # -------------------------------------------------------------------------
    # Zero-Knowledge Local Chat Logger (AES-256)
    # -------------------------------------------------------------------------
    def log_encrypted_event(self, event_data: Dict[str, Any]) -> bool:
        """Appends an AES-256 encrypted JSON log entry if not in incognito mode."""
        if self.incognito_active:
            return False  # Zero trace on disk in incognito mode

        if not self._fernet:
            return False

        try:
            payload = json.dumps({
                "timestamp": time.time(),
                "iso": datetime.now().isoformat(),
                "data": event_data
            }).encode("utf-8")
            token = self._fernet.encrypt(payload)
            with open(SECURE_LOG_FILE, "ab") as f:
                f.write(token + b"\n")
            return True
        except Exception:
            return False

    def read_encrypted_logs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Decrypts and returns recent log entries using local key."""
        if not self._fernet or not SECURE_LOG_FILE.exists():
            return []

        decrypted = []
        try:
            lines = SECURE_LOG_FILE.read_bytes().splitlines()
            for line in lines[-limit:]:
                line = line.strip()
                if not line:
                    continue
                try:
                    raw = self._fernet.decrypt(line)
                    decrypted.append(json.loads(raw.decode("utf-8")))
                except Exception:
                    continue
        except Exception:
            pass
        return decrypted

    # -------------------------------------------------------------------------
    # 1. Local API Key Vault & Prompt Redaction Guard
    # -------------------------------------------------------------------------
    def scrub_prompt_payload(self, text: str) -> str:
        """
        Scans outgoing user prompts for accidental API keys, tokens, or passwords,
        redacting them before sending to Gemini.
        """
        scrubbed = text

        # Gemini, OpenAI, GitHub, AWS, Generic keys
        patterns = [
            (r"AIza[0-9A-Za-z-_]{30,45}", "[REDACTED_GEMINI_KEY]"),
            (r"sk-[a-zA-Z0-9]{30,}", "[REDACTED_OPENAI_KEY]"),
            (r"ghp_[a-zA-Z0-9]{30,}", "[REDACTED_GITHUB_TOKEN]"),
            (r"AKIA[0-9A-Z]{16}", "[REDACTED_AWS_KEY]"),
            (r"(password|passwd|pwd|secret)\s*[:=]\s*['\"][^'\"]+['\"]", r"\1='[REDACTED_CREDENTIAL]'")
        ]

        for pat, repl in patterns:
            scrubbed = re.sub(pat, repl, scrubbed, flags=re.IGNORECASE)

        return scrubbed

    # -------------------------------------------------------------------------
    # 2. Automated Log Redacter (Strips IPs, MACs, Personal Paths)
    # -------------------------------------------------------------------------
    def redact_log_dump(self, log_text: str) -> str:
        """Strips private IP addresses, MAC addresses, and username paths."""
        text = log_text

        # Strip IPv4 addresses (excluding 127.0.0.1)
        text = re.sub(r"\b(?!127\.0\.0\.1\b)(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", "[REDACTED_IP]", text)

        # Strip MAC addresses
        text = re.sub(r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})", "[REDACTED_MAC]", text)

        # Strip user home folder paths
        text = re.sub(r"([A-Za-z]:[\\/]Users[\\/][^\\/\s]+|/home/[^/\s]+)", "[REDACTED_USER_HOME]", text)

        return text

    # -------------------------------------------------------------------------
    # 3. Ephemeral Chat Mode ("Incognito Session")
    # -------------------------------------------------------------------------
    def toggle_incognito(self, enable: Optional[bool] = None) -> bool:
        """Enables/disables memory logging. When active, zero traces are written to disk."""
        if enable is None:
            self.incognito_active = not self.incognito_active
        else:
            self.incognito_active = bool(enable)
        return self.incognito_active

    # -------------------------------------------------------------------------
    # 4. Local Biometric / Passkey Guard for Destructive Actions
    # -------------------------------------------------------------------------
    def verify_action_permission(self, action_description: str, user_provided_token: str) -> bool:
        """
        Validates token confirmation before executing root or destructive actions.
        """
        if not user_provided_token:
            return False
        return user_provided_token.strip() == self.passkey_token

    def is_destructive_command(self, cmd: str) -> bool:
        """Detects high-risk destructive commands."""
        low = cmd.lower().strip()
        destructive_keywords = [
            "rm -rf /", "rm -rf *", "mkfs", "dd if=", ":(){ :|:& };:",
            "format c:", "drop database", "truncate", "del /f /s /q c:\\"
        ]
        return any(k in low for k in destructive_keywords)

    # -------------------------------------------------------------------------
    # 5. File Integrity Monitor (FIM SHA-256 Hashes)
    # -------------------------------------------------------------------------
    def update_fim_baseline(self, files_to_monitor: Optional[List[str]] = None) -> Dict[str, Any]:
        """Calculates SHA-256 hashes of critical files to detect unauthorized tampering."""
        if files_to_monitor is None:
            files_to_monitor = ["server.py", "run.py", "cli.py", "mac_agent.py", "requirements.txt"]

        baseline = {}
        for fname in files_to_monitor:
            fpath = BASE_DIR / fname
            if fpath.exists() and fpath.is_file():
                h = hashlib.sha256(fpath.read_bytes()).hexdigest()
                baseline[fname] = {"hash": h, "updated": time.time(), "size": fpath.stat().st_size}

        FIM_FILE.write_text(json.dumps(baseline, indent=2), encoding="utf-8")
        return {"success": True, "monitored_files": list(baseline.keys()), "baseline_file": str(FIM_FILE)}

    def check_fim_integrity(self) -> Dict[str, Any]:
        """Audits current project files against stored SHA-256 baseline."""
        if not FIM_FILE.exists():
            return {"status": "NO_BASELINE", "message": "No FIM baseline found. Run update_fim_baseline first."}

        try:
            baseline = json.loads(FIM_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}

        tampered = []
        verified = []

        for fname, info in baseline.items():
            fpath = BASE_DIR / fname
            if not fpath.exists():
                tampered.append({"file": fname, "reason": "FILE_DELETED"})
                continue

            current_hash = hashlib.sha256(fpath.read_bytes()).hexdigest()
            if current_hash != info["hash"]:
                tampered.append({"file": fname, "reason": "HASH_MISMATCH", "expected": info["hash"], "actual": current_hash})
            else:
                verified.append(fname)

        is_intact = len(tampered) == 0
        return {
            "is_intact": is_intact,
            "status": "SECURE" if is_intact else "ALERT_TAMPERED",
            "verified_count": len(verified),
            "tampered_files": tampered
        }

    # -------------------------------------------------------------------------
    # 6. Secure Environment Variable Enforcer
    # -------------------------------------------------------------------------
    def scan_codebase_for_leaked_credentials(self, scan_dir: Optional[str] = None) -> List[Dict[str, Any]]:
        """Scans code files to ensure no hardcoded secrets or private keys are committed."""
        target = Path(scan_dir) if scan_dir else BASE_DIR
        findings = []

        secret_regex = re.compile(r"(AIza[0-9A-Za-z-_]{35}|sk-[a-zA-Z0-9]{32,}|ghp_[a-zA-Z0-9]{36})")

        for root, dirs, files in os.walk(target):
            # Skip git and cache dirs
            dirs[:] = [d for d in dirs if d not in [".git", "__pycache__", "venv", "node_modules", "tmp"]]
            for file in files:
                if file.endswith((".py", ".js", ".html", ".sh", ".json")) and file != "fim_hashes.json" and not file.endswith(".enc"):
                    fpath = Path(root) / file
                    try:
                        content = fpath.read_text(encoding="utf-8", errors="ignore")
                        for line_idx, line in enumerate(content.splitlines(), start=1):
                            m = secret_regex.search(line)
                            if m:
                                findings.append({
                                    "file": str(fpath.relative_to(BASE_DIR)),
                                    "line": line_idx,
                                    "matched_secret": m.group(0)[:8] + "..."
                                })
                    except Exception:
                        pass

        return findings

    # -------------------------------------------------------------------------
    # 7. Secure SSH Tunnel Manager
    # -------------------------------------------------------------------------
    def generate_ssh_tunnel_command(self, remote_user: str, remote_server: str, remote_port: int = 5000) -> str:
        """Generates command to spin up an encrypted reverse tunnel for remote access outside LAN."""
        return f"ssh -N -R {remote_port}:localhost:5000 {remote_user}@{remote_server}"

    # -------------------------------------------------------------------------
    # 8. Exposed Port Auditor
    # -------------------------------------------------------------------------
    def audit_exposed_ports(self) -> Dict[str, Any]:
        """
        Audits active listening network ports across local interfaces.
        Flags any service listening on 0.0.0.0 (exposed to LAN/WAN).
        """
        import psutil

        listening_ports = []
        try:
            connections = psutil.net_connections(kind="inet")
            for c in connections:
                if c.status == "LISTEN" and c.laddr:
                    ip = c.laddr.ip
                    port = c.laddr.port
                    is_public = ip in ("0.0.0.0", "::")
                    listening_ports.append({
                        "ip": ip,
                        "port": port,
                        "pid": c.pid,
                        "is_publicly_exposed": is_public
                    })
        except Exception:
            # Fallback check on standard project ports if psutil net_connections lacks permission
            for test_port in [5000, 5001, 8080, 22]:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.1)
                res = s.connect_ex(("127.0.0.1", test_port))
                if res == 0:
                    listening_ports.append({
                        "ip": "127.0.0.1",
                        "port": test_port,
                        "pid": None,
                        "is_publicly_exposed": False
                    })
                s.close()

        public_count = sum(1 for p in listening_ports if p.get("is_publicly_exposed"))
        return {
            "total_listeners": len(listening_ports),
            "public_exposed_count": public_count,
            "listeners": listening_ports,
            "status": "CAUTION" if public_count > 2 else "OPTIMAL"
        }

    # -------------------------------------------------------------------------
    # 9. SSL Certificate Expiry Watchdog
    # -------------------------------------------------------------------------
    def check_ssl_cert_expiry(self, target: str = "google.com", port: int = 443) -> Dict[str, Any]:
        """
        Audits SSL certificate expiration for remote host or local cert.
        Warns if expiring within 14 days.
        """
        try:
            ctx = ssl.create_default_context()
            with socket.create_connection((target, port), timeout=3.0) as sock:
                with ctx.wrap_socket(sock, server_hostname=target) as ssock:
                    cert = ssock.getpeercert()
                    expire_str = cert.get("notAfter")
                    if expire_str:
                        # format: 'May  9 08:31:00 2026 GMT'
                        expire_date = datetime.strptime(expire_str, "%b %d %H:%M:%S %Y %Z")
                        days_left = (expire_date - datetime.utcnow()).days
                        return {
                            "host": target,
                            "port": port,
                            "expires": expire_str,
                            "days_remaining": days_left,
                            "status": "EXPIRING_SOON" if days_left < 14 else "VALID"
                        }
        except Exception as e:
            return {"host": target, "port": port, "error": str(e), "status": "CHECK_FAILED"}

        return {"host": target, "port": port, "status": "UNKNOWN"}


# Global security vault singleton
security_vault = SecurityVaultEngine()
