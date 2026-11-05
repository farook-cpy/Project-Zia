"""
Project Zia - Natural Language Alarm & Timer Scheduling Engine
Zero-token rule-based parser & non-blocking background scheduler.
Engineered for legacy hardware (2007 MacBook Pro / Linux Mint / cross-OS) with 0% CPU.
"""

import os
import sys
import time
import json
import re
import uuid
import threading
import subprocess
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ALARMS_FILE = DATA_DIR / "alarms.json"


class AlarmManager:
    """
    Manages relative countdown timers and absolute clock alarms.
    Persists active scheduled jobs in data/alarms.json.
    """

    def __init__(self):
        DATA_DIR.mkdir(exist_ok=True)
        self.alarms: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._active_timers: Dict[str, threading.Timer] = {}
        self._trigger_callback = None
        self.load()
        self._arm_pending_alarms()

    def set_trigger_callback(self, callback):
        """Allows server or heartbeat to register a broadcast callback."""
        self._trigger_callback = callback

    def load(self):
        with self._lock:
            if ALARMS_FILE.exists():
                try:
                    with open(ALARMS_FILE, "r", encoding="utf-8") as f:
                        self.alarms = json.load(f)
                except Exception as e:
                    print(f"[AlarmManager] Load notice: {e}")
                    self.alarms = []
            else:
                self.alarms = []

    def save(self):
        try:
            with open(ALARMS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.alarms, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[AlarmManager] Save notice: {e}")

    def _arm_pending_alarms(self):
        """Re-arms any pending alarms from persistent storage upon startup."""
        now = time.time()
        for a in list(self.alarms):
            if a["status"] == "active":
                diff = a["target_timestamp"] - now
                if diff > 0:
                    self._schedule_timer_thread(a["id"], diff)
                else:
                    # Expired while offline
                    a["status"] = "expired"
        self.save()

    def _schedule_timer_thread(self, alarm_id: str, delay_seconds: float):
        """Spawns a non-blocking background threading.Timer that fires alert."""
        timer = threading.Timer(delay_seconds, self._on_alarm_fired, args=[alarm_id])
        timer.daemon = True
        self._active_timers[alarm_id] = timer
        timer.start()

    def _on_alarm_fired(self, alarm_id: str):
        """Called when an alarm or timer timestamp is reached."""
        alarm = None
        with self._lock:
            for a in self.alarms:
                if a["id"] == alarm_id:
                    alarm = a
                    a["status"] = "fired"
                    break
            self.save()
            self._active_timers.pop(alarm_id, None)

        if not alarm:
            return

        label = alarm.get("label", "Timer")
        alarm_type = alarm.get("type", "alarm")
        print(f"\n\a\033[93m\033[1m[ALARM TRIGGERED] {alarm_type.upper()}: {label}\033[0m\n")

        # 1. Subtle system sound notification
        self._play_system_alert_sound()

        # 2. Desktop notification banner
        self._send_desktop_notification(f"Zia // {alarm_type.capitalize()}", label)

        # 3. Trigger callback for Live2D/TTS broadcast
        if self._trigger_callback:
            try:
                import asyncio
                if asyncio.iscoroutinefunction(self._trigger_callback):
                    asyncio.run(self._trigger_callback(alarm))
                else:
                    self._trigger_callback(alarm)
            except Exception:
                pass

    def _play_system_alert_sound(self):
        """Plays a lightweight subtle system chime."""
        try:
            if sys.platform == "win32":
                import winsound
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            elif sys.platform == "darwin":
                subprocess.Popen(["afplay", "/System/Library/Sounds/Glass.aiff"], stderr=subprocess.DEVNULL)
            else:
                # Linux Mint / ALSA / PulseAudio
                for player in ["paplay", "aplay"]:
                    import shutil
                    if shutil.which(player):
                        sample = "/usr/share/sounds/freedesktop/stereo/complete.oga"
                        if os.path.exists(sample):
                            subprocess.Popen([player, sample], stderr=subprocess.DEVNULL)
                            return
                # Terminal bell fallback
                sys.stdout.write("\a")
                sys.stdout.flush()
        except Exception:
            sys.stdout.write("\a")
            sys.stdout.flush()

    def _send_desktop_notification(self, title: str, message: str):
        """Displays native desktop notification banner without heavy GUI dependencies."""
        try:
            if sys.platform.startswith("linux"):
                import shutil
                if shutil.which("notify-send"):
                    subprocess.Popen([
                        "notify-send",
                        "-u", "normal",
                        "-a", "Project Zia",
                        title,
                        message
                    ], stderr=subprocess.DEVNULL)
            elif sys.platform == "darwin":
                script = f'display notification "{message}" with title "{title}"'
                subprocess.Popen(["osascript", "-e", script], stderr=subprocess.DEVNULL)
            elif sys.platform == "win32":
                # PowerShell balloon / toast fallback
                ps_cmd = f'[reflection.assembly]::loadwithpartialname("System.Windows.Forms"); [System.Windows.Forms.MessageBox]::Show("{message}", "{title}")'
                # Non-blocking PowerShell prompt
                subprocess.Popen(["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_cmd], stderr=subprocess.DEVNULL)
        except Exception:
            pass

    def set_timer(self, duration_sec: float, label: str = "Timer") -> Dict[str, Any]:
        """Sets a relative countdown timer (e.g. 20 minutes)."""
        duration_sec = max(1.0, float(duration_sec))
        now = time.time()
        target_ts = now + duration_sec
        alarm_id = f"timer_{uuid.uuid4().hex[:6]}"

        target_dt = datetime.fromtimestamp(target_ts)
        time_str = target_dt.strftime("%I:%M:%S %p")

        item = {
            "id": alarm_id,
            "type": "timer",
            "label": label.strip() or "Countdown Timer",
            "duration_sec": int(duration_sec),
            "created_at": now,
            "target_timestamp": target_ts,
            "target_time_str": time_str,
            "status": "active"
        }

        with self._lock:
            self.alarms.append(item)
            self.save()

        self._schedule_timer_thread(alarm_id, duration_sec)

        return {
            "success": True,
            "id": alarm_id,
            "label": item["label"],
            "duration_sec": int(duration_sec),
            "target_time": time_str,
            "message": f"Timer set for {int(duration_sec)}s ('{item['label']}'). Will ring at {time_str}."
        }

    def set_alarm(self, time_str: str, label: str = "Alarm") -> Dict[str, Any]:
        """
        Sets an absolute clock alarm (e.g. '8:00 pm', '07:30', '6:00 am').
        If time has already passed today, schedules for tomorrow.
        """
        parsed_dt = self._parse_clock_time(time_str)
        if not parsed_dt:
            return {"error": f"Could not parse clock time from '{time_str}'. Use format like '8:00 pm' or '19:30'."}

        now = datetime.now()
        target_dt = now.replace(hour=parsed_dt.hour, minute=parsed_dt.minute, second=0, microsecond=0)

        # If already passed today, schedule for tomorrow
        if target_dt <= now:
            target_dt += timedelta(days=1)

        target_ts = target_dt.timestamp()
        diff_sec = target_ts - time.time()
        alarm_id = f"alarm_{uuid.uuid4().hex[:6]}"

        formatted_time = target_dt.strftime("%I:%M %p")
        day_str = "tomorrow" if target_dt.date() > now.date() else "today"

        item = {
            "id": alarm_id,
            "type": "alarm",
            "label": label.strip() or "Wake Up / Reminder",
            "created_at": time.time(),
            "target_timestamp": target_ts,
            "target_time_str": formatted_time,
            "status": "active"
        }

        with self._lock:
            self.alarms.append(item)
            self.save()

        self._schedule_timer_thread(alarm_id, diff_sec)

        hours = int(diff_sec // 3600)
        minutes = int((diff_sec % 3600) // 60)
        countdown_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

        return {
            "success": True,
            "id": alarm_id,
            "label": item["label"],
            "target_time": formatted_time,
            "day": day_str,
            "countdown": countdown_str,
            "message": f"Alarm set for {formatted_time} {day_str} ({countdown_str} from now) for '{item['label']}'."
        }

    @staticmethod
    def _parse_clock_time(raw: str) -> Optional[datetime]:
        """Parses various clock formats like '8:00 pm', '8pm', '08:00', '19:45'."""
        cleaned = raw.strip().lower()
        # Clean up separators and spaces
        cleaned = re.sub(r"\s+", " ", cleaned)

        formats = [
            "%I:%M %p",
            "%I:%M%p",
            "%I %p",
            "%I%p",
            "%H:%M",
            "%H"
        ]

        for fmt in formats:
            try:
                return datetime.strptime(cleaned, fmt)
            except ValueError:
                continue

        # Regex fallback for '8.30 pm' or '8.30pm'
        m = re.match(r"^(\d{1,2})(?:[\.:](\d{2}))?\s*(am|pm)?$", cleaned)
        if m:
            hh = int(m.group(1))
            mm = int(m.group(2)) if m.group(2) else 0
            meridiem = m.group(3)
            if meridiem == "pm" and hh < 12:
                hh += 12
            elif meridiem == "am" and hh == 12:
                hh = 0
            return datetime(2000, 1, 1, hh, mm)

        return None

    def list_active(self) -> List[Dict[str, Any]]:
        """Returns all currently active alarms and timers with seconds remaining."""
        now = time.time()
        active = []
        with self._lock:
            for a in self.alarms:
                if a["status"] == "active":
                    rem = int(max(0, a["target_timestamp"] - now))
                    a_copy = dict(a)
                    a_copy["seconds_remaining"] = rem
                    hours = rem // 3600
                    minutes = (rem % 3600) // 60
                    seconds = rem % 60
                    if hours > 0:
                        a_copy["countdown"] = f"{hours}h {minutes}m"
                    elif minutes > 0:
                        a_copy["countdown"] = f"{minutes}m {seconds}s"
                    else:
                        a_copy["countdown"] = f"{seconds}s"
                    active.append(a_copy)
        return active

    def cancel(self, alarm_id: str) -> Dict[str, Any]:
        """Cancels an active alarm or timer."""
        found = False
        with self._lock:
            for a in self.alarms:
                if a["id"] == alarm_id and a["status"] == "active":
                    a["status"] = "cancelled"
                    found = True
                    break
            if found:
                self.save()
            timer = self._active_timers.pop(alarm_id, None)
            if timer:
                timer.cancel()

        if found:
            return {"success": True, "message": f"Cancelled alarm/timer [{alarm_id}]."}
        return {"error": f"Active alarm or timer [{alarm_id}] not found."}

    def parse_natural_language(self, user_text: str) -> Optional[Dict[str, Any]]:
        """
        Lightweight regex parser for relative countdowns and absolute alarms (0 LLM tokens).
        Examples:
        - 'remind me in 20 minutes to push code'
        - 'timer 5m'
        - 'set timer for 10 minutes'
        - 'wake me in 8:00 pm'
        - 'wake me at 8:00 pm'
        - 'set alarm for 6:00 am'
        """
        text = user_text.strip().lower()

        # 1. Relative Timers: "in 20 minutes", "timer 5m", "remind me in 10s"
        rel_match = re.search(
            r"(?:set\s+)?(?:timer\s+(?:for\s+)?|remind\s+me\s+in\s+|alert\s+me\s+in\s+|wake\s+me\s+in\s+)"
            r"(\d+)\s*(seconds?|sec|s|minutes?|min|m|hours?|hr|h)(?:\s+(?:to|for)?\s*(.+))?",
            text
        )
        if rel_match:
            amount = int(rel_match.group(1))
            unit = rel_match.group(2).lower()
            label = rel_match.group(3) or "Timer"

            # Clean label
            label = re.sub(r"^(to|for)\s+", "", label).strip() or "Timer"

            mult = 1
            if unit.startswith("m"):
                mult = 60
            elif unit.startswith("h"):
                mult = 3600

            duration = amount * mult
            return self.set_timer(duration, label)

        # 2. Absolute Alarms: "wake me at 8:00 pm", "alarm for 6am", "wake me in 8:00 pm"
        abs_match = re.search(
            r"(?:set\s+)?(?:alarm\s+(?:for|at)\s+|wake\s+me\s+(?:at|in)\s+|remind\s+me\s+at\s+)"
            r"(\d{1,2}(?:[\.:]\d{2})?\s*(?:am|pm)?)(?:\s+(?:to|for)?\s*(.+))?",
            text
        )
        if abs_match:
            raw_time = abs_match.group(1).strip()
            # If the user typed "wake me in 8:00 pm", it's an absolute clock time
            label = abs_match.group(2) or "Wake up"
            label = re.sub(r"^(to|for)\s+", "", label).strip() or "Alarm"
            return self.set_alarm(raw_time, label)

        return None


# Global alarm manager singleton
alarm_manager = AlarmManager()
