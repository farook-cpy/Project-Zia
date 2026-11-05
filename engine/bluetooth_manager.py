import sys
import subprocess
import shutil
import re

class BluetoothManager:
    def __init__(self):
        self.os_type = sys.platform

    def get_paired_devices(self) -> dict:
        """
        Returns list of paired Bluetooth devices cross-platform.
        """
        devices = []
        try:
            if self.os_type == "linux":
                # Linux Mint / Ubuntu bluetoothctl
                if shutil.which("bluetoothctl"):
                    res = subprocess.run(["bluetoothctl", "paired-devices"], capture_output=True, text=True, timeout=5)
                    for line in res.stdout.strip().splitlines():
                        match = re.match(r"^Device\s+([0-9A-Fa-f:]+)\s+(.+)$", line.strip())
                        if match:
                            devices.append({"mac": match.group(1), "name": match.group(2), "connected": False})
                    # Check connected info
                    info_res = subprocess.run(["bluetoothctl", "info"], capture_output=True, text=True, timeout=5)
                    for dev in devices:
                        if dev["mac"] in info_res.stdout and "Connected: yes" in info_res.stdout:
                            dev["connected"] = True
                return {"success": True, "devices": devices, "platform": "linux"}

            elif self.os_type == "win32":
                # Windows PowerShell PnP / Bluetooth query
                ps_script = """
                Get-PnpDevice -Class Bluetooth -ErrorAction SilentlyContinue | 
                Where-Object { $_.FriendlyName -notmatch 'Enumerator|Adapter|Radio|Protocol' } | 
                Select-Object Status, FriendlyName, InstanceId | ConvertTo-Json
                """
                res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, text=True, timeout=8)
                output = res.stdout.strip()
                import json
                if output:
                    try:
                        data = json.loads(output)
                        if isinstance(data, dict):
                            data = [data]
                        for item in data:
                            name = item.get("FriendlyName")
                            status = item.get("Status")
                            if name:
                                devices.append({"name": name, "status": status, "connected": status == "OK"})
                    except Exception:
                        pass
                return {"success": True, "devices": devices, "platform": "windows"}

            else:
                # macOS
                res = subprocess.run(["system_profiler", "SPBluetoothDataType"], capture_output=True, text=True, timeout=8)
                return {"success": True, "raw": res.stdout[:500], "platform": "darwin"}

        except Exception as e:
            return {"success": False, "error": str(e), "devices": []}

    def scan_devices(self, timeout_sec: int = 6) -> dict:
        """
        Scans for available Bluetooth devices in proximity.
        """
        devices = []
        try:
            if self.os_type == "linux":
                if shutil.which("bluetoothctl"):
                    # Scan for a few seconds
                    subprocess.run(["bluetoothctl", "--timeout", str(timeout_sec), "scan", "on"], capture_output=True, text=True, timeout=timeout_sec + 2)
                    res = subprocess.run(["bluetoothctl", "devices"], capture_output=True, text=True, timeout=5)
                    for line in res.stdout.strip().splitlines():
                        match = re.match(r"^Device\s+([0-9A-Fa-f:]+)\s+(.+)$", line.strip())
                        if match:
                            devices.append({"mac": match.group(1), "name": match.group(2)})
                return {"success": True, "devices": devices}

            elif self.os_type == "win32":
                # Open Windows Bluetooth picker or settings for discovery
                subprocess.Popen(["start", "ms-settings:bluetooth"], shell=True)
                return {
                    "success": True,
                    "message": "Opened Windows Bluetooth discovery panel for pairing.",
                    "devices": []
                }
            else:
                return {"success": False, "error": "Scanning not supported natively on this OS."}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def connect(self, target_identifier: str) -> dict:
        """
        Connects to a specific Bluetooth device (MAC address on Linux, Name/ID on Windows).
        """
        target = target_identifier.strip()
        try:
            if self.os_type == "linux":
                if shutil.which("bluetoothctl"):
                    res = subprocess.run(["bluetoothctl", "connect", target], capture_output=True, text=True, timeout=10)
                    output = res.stdout.strip()
                    success = "Connection successful" in output or "successful" in output.lower()
                    return {"success": success, "output": output, "target": target}
                return {"success": False, "error": "bluetoothctl not available"}

            elif self.os_type == "win32":
                # On Windows, try activating or launch settings panel
                subprocess.Popen(["start", "ms-settings:bluetooth"], shell=True)
                return {
                    "success": True,
                    "target": target,
                    "message": f"Opened Bluetooth settings to complete connection to '{target}'."
                }
            else:
                return {"success": False, "error": "Not supported on this OS"}

        except Exception as e:
            return {"success": False, "error": str(e), "target": target}

    def disconnect(self, target_identifier: str) -> dict:
        target = target_identifier.strip()
        try:
            if self.os_type == "linux":
                if shutil.which("bluetoothctl"):
                    res = subprocess.run(["bluetoothctl", "disconnect", target], capture_output=True, text=True, timeout=8)
                    return {"success": True, "output": res.stdout.strip(), "target": target}
            elif self.os_type == "win32":
                subprocess.Popen(["start", "ms-settings:bluetooth"], shell=True)
                return {"success": True, "target": target}
            return {"success": False, "error": "Not supported on this OS"}
        except Exception as e:
            return {"success": False, "error": str(e)}

bluetooth_manager = BluetoothManager()

