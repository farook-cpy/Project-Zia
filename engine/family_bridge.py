"""
Project Zia - Family Notification & OTP Queue Bridge (engine/family_bridge.py)
Local network webhook sink and secure local queue for SMS/App notifications forwarded
from family Android devices (Samsung Galaxy phones, tablets).

Features:
1. Automated regex extraction of OTP / SMS verification codes.
2. Local disk persistence in data/family_notifications.json (Zero cloud storage).
3. Query interfaces for natural language voice lookups ("What is the OTP?").
4. Sender & device tagging (e.g., "Dad's Samsung", "Bank SMS").
"""

import re
import json
import time
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
QUEUE_FILE = DATA_DIR / "family_notifications.json"


class FamilyNotificationBridge:
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.notifications: List[Dict[str, Any]] = []
        self._load_queue()

    def _load_queue(self):
        if QUEUE_FILE.exists():
            try:
                with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                    self.notifications = json.load(f)
            except Exception:
                self.notifications = []
        else:
            self.notifications = []

    def _save_queue(self):
        try:
            with open(QUEUE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.notifications[-100:], f, indent=2)
        except Exception as e:
            print(f"[FamilyBridge] Save error: {e}")

    def extract_otp(self, text: str) -> Optional[str]:
        """
        Extracts 4 to 8 digit OTP/verification code from notification text.
        """
        # Look for explicit OTP markers first
        m = re.search(r'(?:otp|code|pin|verification|secret)[^\d]*(\d{4,8})\b', text, re.IGNORECASE)
        if m:
            return m.group(1)

        # General standalone 4-8 digit numbers
        m2 = re.search(r'\b(\d{4,8})\b', text)
        if m2:
            return m2.group(1)

        return None

    def enqueue_notification(
        self,
        device: str,
        app_name: str,
        message: str,
        sender: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Enqueues an incoming notification forwarded via local webhook.
        """
        with self._lock:
            now = time.time()
            otp_code = self.extract_otp(message)
            is_otp = bool(otp_code)

            entry = {
                "id": f"notif_{int(now)}_{len(self.notifications)}",
                "timestamp": now,
                "formatted_time": time.strftime("%H:%M:%S", time.localtime(now)),
                "device": device or "Samsung Galaxy",
                "app": app_name or "SMS",
                "sender": sender or "Unknown",
                "message": message,
                "is_otp": is_otp,
                "otp_code": otp_code
            }

            self.notifications.append(entry)
            self._save_queue()

            return {
                "success": True,
                "enqueued_id": entry["id"],
                "is_otp": is_otp,
                "otp_code": otp_code,
                "device": entry["device"]
            }

    def get_latest_otp(self, service: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieves the most recent OTP received across family devices.
        """
        with self._lock:
            for item in reversed(self.notifications):
                if item.get("is_otp") and item.get("otp_code"):
                    if not service or service.lower() in item.get("message", "").lower() or service.lower() in item.get("sender", "").lower():
                        age_sec = int(time.time() - item["timestamp"])
                        res = dict(item)
                        res["age_seconds"] = age_sec
                        res["age_human"] = f"{age_sec // 60}m ago" if age_sec >= 60 else f"{age_sec}s ago"
                        return res
            return None

    def list_recent_otps(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Returns the list of recent OTPs with sender and age."""
        with self._lock:
            otps = []
            for item in reversed(self.notifications):
                if item.get("is_otp"):
                    copy_item = dict(item)
                    copy_item["age_seconds"] = int(time.time() - item["timestamp"])
                    otps.append(copy_item)
                    if len(otps) >= limit:
                        break
            return otps

    def list_all(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Returns the recent notification feed."""
        with self._lock:
            return list(reversed(self.notifications[-limit:]))

    def clear(self):
        """Clears the local notification queue."""
        with self._lock:
            self.notifications = []
            self._save_queue()


# Singleton instance
family_bridge = FamilyNotificationBridge()
