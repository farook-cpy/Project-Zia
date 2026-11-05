#!/usr/bin/env python3
"""
Project Zia - MacBook Pro 2007 Remote Agent Listener (mac_agent.py)
Lightweight JSON-RPC 2.0 daemon running on MacBook Pro 2007 (Linux Mint XFCE, Core 2 Duo)
listening on 0.0.0.0:5001.

Provides remote control endpoints for the Xperia server node:
- system.exec: Run terminal commands (e.g. git status, updates, builds)
- system.health: Read CPU core temp, usage, RAM, and battery state
- system.notify: Flash native notify-send desktop banner
- audio.volume: Adjust ALSA / PulseAudio master volume
- system.lock: Lock desktop session via loginctl
"""

import os
import sys
import json
import time
import subprocess
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


MAC_AGENT_PORT = int(os.environ.get("MAC_PORT", 5001))
RPC_SECRET = os.environ.get("RPC_SECRET", "zia_palakkad_xperia_secure_key_888")


class MacActionExecutor:
    """Safely executes local MacBook system actions."""

    @staticmethod
    def exec_command(cmd: str, timeout: int = 15) -> dict:
        """Executes terminal commands on the MacBook and captures output."""
        try:
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
            return {
                "success": res.returncode == 0,
                "stdout": res.stdout.strip(),
                "stderr": res.stderr.strip(),
                "returncode": res.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Command timed out after {timeout} seconds.", "returncode": 124}
        except Exception as e:
            return {"success": False, "error": str(e), "returncode": 1}

    @staticmethod
    def get_health() -> dict:
        """Collects MacBook Core 2 Duo diagnostics (temp, CPU%, RAM, battery)."""
        health = {
            "platform": sys.platform,
            "device": "MacBook Pro (Linux Mint XFCE)",
            "timestamp": time.time()
        }

        if PSUTIL_AVAILABLE:
            health["cpu_percent"] = psutil.cpu_percent(interval=0.1)
            vm = psutil.virtual_memory()
            health["ram_used_mb"] = int(vm.used / (1024 * 1024))
            health["ram_total_mb"] = int(vm.total / (1024 * 1024))
            health["ram_percent"] = vm.percent

            bat = psutil.sensors_battery()
            if bat:
                health["battery_percent"] = int(bat.percent)
                health["power_plugged"] = bat.power_plugged

            # CPU Temperature (applesmc / lm-sensors)
            try:
                temps = psutil.sensors_temperatures()
                if "applesmc" in temps:
                    health["cpu_temp_c"] = temps["applesmc"][0].current
                elif "coretemp" in temps:
                    health["cpu_temp_c"] = temps["coretemp"][0].current
            except Exception:
                pass

        return health

    @staticmethod
    def send_notification(title: str, message: str) -> dict:
        """Flashes a styled desktop notification banner on the MacBook."""
        try:
            if sys.platform.startswith("linux"):
                # Use notify-send on Linux Mint / XFCE
                subprocess.run(["notify-send", "-u", "normal", "-a", "Project Zia", title, message], check=False)
                return {"success": True, "method": "notify-send"}
            elif sys.platform == "darwin":
                # AppleScript on macOS
                script = f'display notification "{message}" with title "{title}"'
                subprocess.run(["osascript", "-e", script], check=False)
                return {"success": True, "method": "osascript"}
            elif sys.platform == "win32":
                # PowerShell toast fallback
                ps_cmd = f'[System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms"); [System.Windows.Forms.MessageBox]::Show("{message}", "{title}")'
                subprocess.Popen(["powershell", "-NoProfile", "-Command", ps_cmd])
                return {"success": True, "method": "powershell_msgbox"}
            return {"success": False, "error": "Unsupported platform for desktop notifications"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def set_volume(action: str, step: int = 5) -> dict:
        """Adjusts MacBook master audio volume via pactl, amixer, or PowerShell."""
        action = action.lower().strip()
        try:
            if sys.platform.startswith("linux"):
                if action == "up":
                    cmd = f"pactl set-sink-volume @DEFAULT_SINK@ +{step}%"
                elif action == "down":
                    cmd = f"pactl set-sink-volume @DEFAULT_SINK@ -{step}%"
                elif action == "mute":
                    cmd = "pactl set-sink-mute @DEFAULT_SINK@ toggle"
                else:
                    return {"error": f"Unknown volume action: {action}"}
                subprocess.run(cmd, shell=True, check=False)
                return {"success": True, "action": action, "step": step}
            elif sys.platform == "darwin":
                # AppleScript volume on macOS
                if action == "up":
                    subprocess.run(["osascript", "-e", "set volume output volume ((output volume of (get volume settings)) + 5)"], check=False)
                elif action == "down":
                    subprocess.run(["osascript", "-e", "set volume output volume ((output volume of (get volume settings)) - 5)"], check=False)
                return {"success": True, "action": action}
        except Exception as e:
            return {"success": False, "error": str(e)}
        return {"success": True, "action": action}

    @staticmethod
    def lock_session() -> dict:
        """Locks the MacBook XFCE desktop session."""
        try:
            if sys.platform.startswith("linux"):
                subprocess.run(["loginctl", "lock-session"], check=False)
                return {"success": True, "action": "lock-session"}
            elif sys.platform == "darwin":
                subprocess.run(["pmset", "displaysleepnow"], check=False)
                return {"success": True, "action": "displaysleepnow"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        return {"success": True}


def handle_rpc_request(req: dict) -> dict:
    """Dispatches a JSON-RPC 2.0 dictionary directly."""
    method = req.get("method", "")
    params = req.get("params", {})
    req_id = req.get("id", 1)

    result = {}
    error = None

    if method == "system.exec":
        cmd = params.get("command", "")
        timeout = params.get("timeout", 15)
        result = MacActionExecutor.exec_command(cmd, timeout)

    elif method == "system.health":
        result = MacActionExecutor.get_health()

    elif method in ["ui.notify", "system.notify"]:
        title = params.get("title", "Project Zia")
        message = params.get("message", "")
        result = MacActionExecutor.send_notification(title, message)

    elif method in ["audio.volume", "system.volume"]:
        action = params.get("action", "up")
        step = params.get("step", 5)
        result = MacActionExecutor.set_volume(action, step)

    elif method == "system.lock":
        result = MacActionExecutor.lock_session()

    elif method == "ping":
        result = {"status": "pong", "time": time.time()}

    else:
        error = {"code": -32601, "message": f"Method '{method}' not found."}

    response = {
        "jsonrpc": "2.0",
        "id": req_id
    }
    if error:
        response["error"] = error
    else:
        response["result"] = result
    return response


class MacAgentHTTPHandler(BaseHTTPRequestHandler):
    """Secure JSON-RPC 2.0 HTTP request handler for the MacBook agent."""

    def _send_json(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_GET(self):
        if self.path in ["/", "/ping"]:
            self._send_json({"status": "online", "service": "Zia MacBook Remote Agent", "version": "1.0"})
        elif self.path == "/health":
            self._send_json(MacActionExecutor.get_health())
        else:
            self._send_json({"error": "Endpoint not found"}, status=404)

    def do_POST(self):
        # 1. Verify Secret Token Header
        auth_header = self.headers.get("X-Zia-Secret", "")
        if RPC_SECRET and auth_header != RPC_SECRET:
            self._send_json({"jsonrpc": "2.0", "error": {"code": -32600, "message": "Unauthorized: Invalid X-Zia-Secret token"}}, status=401)
            return

        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            req = json.loads(post_data.decode("utf-8"))
        except Exception:
            self._send_json({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error: Invalid JSON"}}, status=400)
            return

        response = handle_rpc_request(req)
        status = 200 if "result" in response else 400
        self._send_json(response, status=status)

    def log_message(self, format, *args):
        # Suppress routine log noise for quiet background execution
        pass


def auto_register_with_xperia(xperia_url: str):
    """Background helper to announce MacBook presence to the Xperia server node."""
    import urllib.request
    try:
        reg_url = f"{xperia_url.rstrip('/')}/api/rpc/register"
        req_data = json.dumps({"agent_port": MAC_AGENT_PORT, "secret": RPC_SECRET}).encode("utf-8")
        req = urllib.request.Request(
            reg_url,
            data=req_data,
            headers={"Content-Type": "application/json", "X-Zia-Secret": RPC_SECRET}
        )
        urllib.request.urlopen(req, timeout=3)
        print(f"\033[92m[MacAgent] Successfully registered with Xperia server at {xperia_url}!\033[0m")
    except Exception:
        # Xperia server might not be booted yet; non-blocking
        pass


def main():
    print("\033[96m\033[1m======================================================================")
    print(" PROJECT ZIA // MACBOOK PRO 2007 REMOTE AGENT LISTENER")
    print(f" Listening on 0.0.0.0:{MAC_AGENT_PORT} (Linux Mint XFCE Core 2 Duo Node)")
    print("======================================================================\033[0m")

    # If Xperia URL provided in env, auto-register
    xperia_url = os.environ.get("XPERIA_SERVER_URL")
    if xperia_url:
        t = threading.Thread(target=auto_register_with_xperia, args=(xperia_url,), daemon=True)
        t.start()

    server = HTTPServer(("0.0.0.0", MAC_AGENT_PORT), MacAgentHTTPHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[MacAgent] Listener shutdown.")
        server.server_close()


if __name__ == "__main__":
    main()

