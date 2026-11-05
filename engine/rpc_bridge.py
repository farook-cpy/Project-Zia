"""
Project Zia - Client-Server RPC Bridge for Remote MacBook Actions
Runs on the Sony Xperia 1 III server node.
Dispatches remote hardware executions, health inspections, volume controls, and
Linux Mint desktop notifications (notify-send) to the MacBook client listener (mac_agent.py).
"""

import os
import sys
import time
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

DEFAULT_MAC_PORT = 5001
RPC_SECRET = os.environ.get("RPC_SECRET", "zia_palakkad_xperia_secure_key_888")


class RemoteMacRPCBridge:
    """
    JSON-RPC 2.0 Client Bridge connecting Xperia server to the MacBook agent.
    """

    def __init__(self, default_host: str = "127.0.0.1", port: int = DEFAULT_MAC_PORT):
        self.mac_host = os.environ.get("MAC_HOST", default_host)
        self.mac_port = int(os.environ.get("MAC_PORT", port))
        self.secret = RPC_SECRET
        self.last_seen: float = 0.0

    def register_client(self, ip_address: str, port: int = DEFAULT_MAC_PORT) -> Dict[str, Any]:
        """Dynamically registers or updates the MacBook's IP address on LAN."""
        self.mac_host = ip_address
        self.mac_port = port
        self.last_seen = time.time()
        print(f"\033[92m[RPCBridge] MacBook agent registered at {self.mac_host}:{self.mac_port}\033[0m")
        return {
            "success": True,
            "mac_host": self.mac_host,
            "mac_port": self.mac_port,
            "registered_at": self.last_seen
        }

    def call_rpc(self, method: str, params: Optional[Dict[str, Any]] = None, timeout: int = 12) -> Dict[str, Any]:
        """
        Sends a standard JSON-RPC 2.0 payload to the MacBook agent.
        """
        if params is None:
            params = {}

        url = f"http://{self.mac_host}:{self.mac_port}/rpc"
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": int(time.time() * 1000)
        }

        try:
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=req_data,
                headers={
                    "Content-Type": "application/json",
                    "X-Zia-Secret": self.secret
                }
            )
            with urllib.request.urlopen(req, timeout=timeout) as response:
                resp_text = response.read().decode("utf-8")
                self.last_seen = time.time()
                data = json.loads(resp_text)
                if "error" in data:
                    return {"success": False, "error": data["error"].get("message", "RPC Error")}
                return {"success": True, "result": data.get("result", {})}

        except urllib.error.URLError as e:
            return {
                "success": False,
                "error": f"MacBook agent unreachable at {self.mac_host}:{self.mac_port} ({e.reason}). Ensure mac_agent.py is running on your MacBook.",
                "offline": True
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # -------------------------------------------------------------------------
    # Remote High-Level Helper Methods
    # -------------------------------------------------------------------------
    def execute_remote_command(self, command: str, timeout: int = 15) -> Dict[str, Any]:
        """Executes a terminal command remotely on the MacBook."""
        res = self.call_rpc("system.exec", {"command": command, "timeout": timeout}, timeout=timeout + 2)
        if res.get("success"):
            return res["result"]
        return res

    def get_remote_mac_health(self) -> Dict[str, Any]:
        """Queries CPU %, core temperatures, RAM, and battery from MacBook."""
        res = self.call_rpc("system.health", timeout=5)
        if res.get("success"):
            return res["result"]
        return res

    def send_remote_notification(self, title: str, message: str) -> Dict[str, Any]:
        """Flashes a desktop notification banner on the MacBook (Linux Mint notify-send)."""
        res = self.call_rpc("ui.notify", {"title": title, "message": message}, timeout=5)
        if res.get("success"):
            return res["result"]
        return res

    def remote_volume(self, action: str = "up", step: int = 5) -> Dict[str, Any]:
        """Adjusts master audio volume on the remote MacBook."""
        res = self.call_rpc("audio.volume", {"action": action, "step": step}, timeout=5)
        if res.get("success"):
            return res["result"]
        return res

    def remote_lock_session(self) -> Dict[str, Any]:
        """Locks the remote MacBook desktop session."""
        res = self.call_rpc("system.lock", timeout=5)
        if res.get("success"):
            return res["result"]
        return res

    def is_mac_online(self) -> bool:
        """Checks if the MacBook agent is currently reachable on the LAN."""
        res = self.call_rpc("ping", timeout=2)
        return bool(res.get("success"))


# Global RPC bridge singleton
rpc_bridge = RemoteMacRPCBridge()

