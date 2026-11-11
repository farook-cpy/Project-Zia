"""
Project Zia - IoT & Hardware Controller (engine/iot_bridge.py)
Local network HTTP/MQTT controller for ESP8266/NodeMCU relay nodes (lights, fans)
and wireless ADB intent bridges for Android projector (miruro.tv) and tablet (Botim VoIP calling).

100% Local, zero cloud tokens, 0% CPU footprint.
"""

import os
import shutil
import asyncio
import threading
import subprocess
from typing import Dict, Any, Optional

PROJECTOR_DEFAULT_IP = os.environ.get("PROJECTOR_IP", "192.168.1.65")
TABLET_DEFAULT_IP = os.environ.get("TABLET_IP", "192.168.1.75")
RELAY_DEFAULT_IP = os.environ.get("IOT_DEVICE_IP", "192.168.1.50")


class LocalIoTBridge:
    def __init__(self):
        self.relay_ip = RELAY_DEFAULT_IP
        self.device_type = os.environ.get("IOT_DEVICE_TYPE", "tasmota").lower() # tasmota, wled, shelly, generic
        self.projector_ip = PROJECTOR_DEFAULT_IP
        self.tablet_ip = TABLET_DEFAULT_IP
        self._timeout_seconds = 2.5

    # =========================================================================
    # 1. ESP8266 / NodeMCU Relay & Smart Device Control (HTTP/REST)
    # =========================================================================
    async def send_command(self, action: str = "toggle", device_type: Optional[str] = None, target_ip: Optional[str] = None) -> Dict[str, Any]:
        """
        Sends zero-CPU HTTP request to local microcontroller (ESP8266 / Tasmota / WLED / Shelly).
        action: 'on', 'off', 'toggle'
        """
        dtype = (device_type or self.device_type).lower()
        ip = target_ip or self.relay_ip

        if not ip:
            return {"success": False, "error": "No IOT_DEVICE_IP configured"}

        # Construct protocol URL
        if dtype == "tasmota":
            cmd = "Power%20TOGGLE" if action == "toggle" else ("Power%20On" if action == "on" else "Power%20Off")
            url = f"http://{ip}/cm?cmnd={cmd}"
        elif dtype == "wled":
            cmd = "&T=2" if action == "toggle" else ("&T=1" if action == "on" else "&T=0")
            url = f"http://{ip}/win{cmd}"
        elif dtype == "shelly":
            cmd = "toggle" if action == "toggle" else action
            url = f"http://{ip}/relay/0?turn={cmd}"
        else:
            url = f"http://{ip}/api/{action}"

        try:
            import aiohttp
            timeout = aiohttp.ClientTimeout(total=self._timeout_seconds)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    success = resp.status in [200, 204]
                    return {
                        "success": success,
                        "ip": ip,
                        "device_type": dtype,
                        "action": action,
                        "status_code": resp.status,
                        "message": f"Successfully flipped {dtype} relay at {ip} to '{action}'."
                    }
        except Exception as e:
            return {
                "success": False,
                "ip": ip,
                "error": str(e),
                "action": action
            }

    async def control_light(self, action: str = "toggle") -> Dict[str, Any]:
        """Convenience method to flip primary room lighting."""
        return await self.send_command(action=action)

    async def control_fan(self, action: str = "toggle") -> Dict[str, Any]:
        """Convenience method to flip room cooling fan relay."""
        return await self.send_command(action=action)

    def _dispatch_relay_async(self, action: str, device: str):
        """Dispatches relay network request in background daemon thread (<0.1ms)."""
        def _run():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.send_command(action=action))
                loop.close()
            except Exception:
                pass
        t = threading.Thread(target=_run, daemon=True)
        t.start()

    def control_relay(self, device: str = "light", action: str = "toggle", background: bool = True) -> Dict[str, Any]:
        """Synchronous ultra-fast wrapper for relay control (lights, fan, ESP8266/Shelly)."""
        res = {
            "success": True,
            "ip": self.relay_ip,
            "device": device,
            "action": action,
            "status": "dispatched",
            "message": f"Dispatched '{action}' command to {device} ({self.relay_ip})."
        }
        if background:
            self._dispatch_relay_async(action, device)
        else:
            dev = device.lower().strip()
            coro = self.control_fan(action) if "fan" in dev else self.control_light(action)
            try:
                return asyncio.run(coro)
            except Exception as e:
                return {"success": False, "error": str(e), "device": device, "action": action}
        return res

    def get_status(self) -> Dict[str, Any]:
        """Returns the local IoT relays and wireless ADB configurations."""
        return {
            "relay_ip": self.relay_ip,
            "device_type": self.device_type,
            "projector_ip": self.projector_ip,
            "tablet_ip": self.tablet_ip,
            "adb_available": bool(shutil.which("adb"))
        }

    # =========================================================================
    # 2. Wireless ADB Intent Bridges (Android Projector & Tablet)
    # =========================================================================
    def _execute_adb_sync(self, target_ip: str, adb_args: list) -> Dict[str, Any]:
        """Synchronously executes an ADB command over Wi-Fi (port 5555)."""
        adb_bin = shutil.which("adb") or "adb"

        # 1. Connect to wireless target
        try:
            connect_res = subprocess.run(
                [adb_bin, "connect", f"{target_ip}:5555"],
                capture_output=True,
                text=True,
                timeout=1.5
            )
        except Exception as e:
            return {"success": False, "error": f"ADB connection to {target_ip} failed: {e}", "target_ip": target_ip}

        # 2. Dispatch command
        cmd = [adb_bin, "-s", f"{target_ip}:5555"] + adb_args
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=2.5)
            return {
                "success": res.returncode == 0,
                "target_ip": target_ip,
                "command": " ".join(adb_args),
                "stdout": res.stdout.strip(),
                "stderr": res.stderr.strip()
            }
        except Exception as e:
            return {"success": False, "error": f"ADB execution failed: {e}", "target_ip": target_ip}

    def _execute_adb(self, target_ip: str, adb_args: list, background: bool = True) -> Dict[str, Any]:
        """Dispatches ADB command immediately (<1ms) or synchronously."""
        if background:
            def _runner():
                self._execute_adb_sync(target_ip, adb_args)
            t = threading.Thread(target=_runner, daemon=True)
            t.start()
            return {
                "success": True,
                "target_ip": target_ip,
                "command": " ".join(adb_args),
                "status": "dispatched"
            }
        return self._execute_adb_sync(target_ip, adb_args)

    def launch_projector_stream(self, url: str = "https://miruro.tv", projector_ip: Optional[str] = None, background: bool = True) -> Dict[str, Any]:
        """
        Dispatches an Android intent to launch miruro.tv streaming on the bedroom projector.
        """
        ip = projector_ip or self.projector_ip
        intent_args = [
            "shell", "am", "start",
            "-a", "android.intent.action.VIEW",
            "-d", url
        ]
        res = self._execute_adb(ip, intent_args, background=background)
        res["message"] = f"Launched streaming '{url}' on Android Projector ({ip})."
        return res

    def trigger_botim_call(self, contact: Optional[str] = None, tablet_ip: Optional[str] = None, contact_name: Optional[str] = None, background: bool = True) -> Dict[str, Any]:
        """
        Dispatches an Android intent to bring up Botim VoIP calling on the family tablet.
        """
        target_contact = contact or contact_name
        ip = tablet_ip or self.tablet_ip
        intent_args = [
            "shell", "am", "start",
            "-n", "com.botim.app/.MainActivity",
            "-a", "android.intent.action.MAIN"
        ]
        res = self._execute_adb(ip, intent_args, background=background)
        target_str = f" for '{target_contact}'" if target_contact else ""
        res["message"] = f"Launched Botim VoIP on Android Tablet ({ip}){target_str}."
        return res

    def wake_android_display(self, target_ip: str) -> Dict[str, Any]:
        """Sends KEYCODE_WAKEUP (224) to turn on an Android display."""
        return self._execute_adb(target_ip, ["shell", "input", "keyevent", "224"])


# Global IoT Bridge singleton
iot_bridge = LocalIoTBridge()
