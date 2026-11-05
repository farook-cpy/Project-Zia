"""
Project Zia - Unified Task, Alarm & Palakkad Prayer Scheduler
Custom-engineered for Sony Xperia 1 III server node & remote MacBook client.
Unifies:
1. Daily Islamic Prayer Times for Palakkad, Kerala (Lat 10.7867° N, Long 76.6548° E)
2. Natural language absolute alarms ("wake me at 8:00 pm") and relative countdowns ("remind me in 20 minutes")
3. Recurring maintenance cron jobs
4. Non-intrusive multi-device notification payloads (Xperia speaker + MacBook notify-send)
"""

import os
import sys
import re
import time
import json
import uuid
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional

from engine.prayer_times import prayer_engine
from engine.alarm_manager import alarm_manager
from engine.rpc_bridge import rpc_bridge
from engine.audio_bridge import audio_bridge

BASE_DIR = Path(__file__).resolve().parent.parent
TASKS_FILE = BASE_DIR / "data" / "tasks.json"


class UnifiedScheduler:
    """
    Background scheduler thread for Project Zia running 24/7 on the Xperia server.
    """

    def __init__(self):
        self.tasks = {}
        self.is_running = False
        self._thread = None
        self._lock = threading.Lock()
        self.load_tasks()
        self.start()

    def load_tasks(self):
        if TASKS_FILE.exists():
            try:
                data = json.loads(TASKS_FILE.read_text(encoding="utf-8"))
                self.tasks = data
            except Exception:
                self.tasks = {}

    def save_tasks(self):
        TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
        TASKS_FILE.write_text(json.dumps(self.tasks, indent=2), encoding="utf-8")

    # -------------------------------------------------------------------------
    # 1. Natural Language Recurring Interval Parser
    # -------------------------------------------------------------------------
    def parse_natural_interval(self, text: str) -> tuple[int, bool]:
        """
        Parses recurring phrases like 'every 2 hours', 'every 30m', 'every 45s'.
        Returns (interval_seconds, is_recurring).
        """
        text = text.lower().strip()
        is_recurring = "every" in text

        s_match = re.search(r"(\d+)\s*(?:s|sec|seconds?)", text)
        if s_match:
            return int(s_match.group(1)), is_recurring

        m_match = re.search(r"(\d+)\s*(?:m|min|minutes?)", text)
        if m_match:
            return int(m_match.group(1)) * 60, is_recurring

        h_match = re.search(r"(\d+)\s*(?:h|hr|hours?)", text)
        if h_match:
            return int(h_match.group(1)) * 3600, is_recurring

        d_match = re.search(r"(\d+)\s*(?:d|days?)", text)
        if d_match:
            return int(d_match.group(1)) * 86400, is_recurring

        return 3600, is_recurring

    # -------------------------------------------------------------------------
    # 2. Unified Natural Language Task & Alarm Dispatcher
    # -------------------------------------------------------------------------
    def schedule_from_natural_language(self, prompt: str, action_command: Optional[str] = None) -> Dict[str, Any]:
        """
        Routes natural language queries to:
        - Absolute alarms ('wake me at 8:00 pm')
        - Relative countdown timers ('remind me in 20 minutes to push code')
        - Recurring cron intervals ('every 2 hours check battery')
        """
        prompt_clean = prompt.strip()

        # Check for relative timer or absolute alarm first
        alarm_res = alarm_manager.parse_natural_language(prompt_clean)
        if alarm_res:
            return alarm_res

        # Fallback to recurring schedule
        interval_sec, is_recurring = self.parse_natural_interval(prompt_clean)
        task_id = f"cron_{uuid.uuid4().hex[:6]}"

        label = re.sub(r"(?:every|in)\s+\d+\s*(?:s|m|h|d|sec|min|hours?|days?|minutes?)", "", prompt_clean, flags=re.IGNORECASE).strip()
        label = re.sub(r"^(?:remind\s+me\s+to|schedule|run)\s+", "", label, flags=re.IGNORECASE).strip() or prompt_clean

        task = {
            "id": task_id,
            "label": label,
            "interval_sec": interval_sec,
            "is_recurring": is_recurring,
            "action_command": action_command,
            "next_run": time.time() + interval_sec,
            "created_at": time.time(),
            "runs_count": 0
        }

        with self._lock:
            self.tasks[task_id] = task
            self.save_tasks()

        timing_str = f"every {interval_sec}s" if is_recurring else f"in {interval_sec}s"
        return {
            "success": True,
            "task_id": task_id,
            "label": label,
            "interval_sec": interval_sec,
            "is_recurring": is_recurring,
            "message": f"Scheduled [{task_id}]: '{label}' ({timing_str})."
        }

    def add_schedule(self, natural_prompt: str, action_command: Optional[str] = None) -> Dict[str, Any]:
        return self.schedule_from_natural_language(natural_prompt, action_command)

    def list_schedules(self) -> List[Dict[str, Any]]:
        now = time.time()
        result = []
        with self._lock:
            for tid, t in self.tasks.items():
                secs_left = max(0, int(t["next_run"] - now))
                result.append({
                    "id": tid,
                    "label": t["label"],
                    "interval_sec": t["interval_sec"],
                    "is_recurring": t["is_recurring"],
                    "action_command": t.get("action_command"),
                    "seconds_until_next": secs_left,
                    "runs_count": t.get("runs_count", 0)
                })
        return result

    def cancel_schedule(self, task_id: str) -> Dict[str, Any]:
        with self._lock:
            if task_id in self.tasks:
                del self.tasks[task_id]
                self.save_tasks()
                return {"success": True, "message": f"Cancelled task [{task_id}]."}
        return {"success": False, "error": f"Task ID '{task_id}' not found."}

    # -------------------------------------------------------------------------
    # 3. Main Background Loop (Palakkad Prayer Checks + Due Tasks)
    # -------------------------------------------------------------------------
    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="ZiaUnifiedScheduler")
        self._thread.start()

    def _loop(self):
        while self.is_running:
            now = time.time()

            # A. Palakkad Daily Islamic Prayer Check-in
            try:
                prayer_prompt = prayer_engine.check_prayer_prompt_needed()
                if prayer_prompt:
                    p_name = prayer_prompt["prayer"]
                    p_msg = prayer_prompt["prompt"]
                    print(f"\n\033[96m[Prayer Check-in] {p_msg}\033[0m")

                    # 1. Dispatch non-intrusive notification to remote MacBook
                    rpc_bridge.send_remote_notification(f"Palakkad Prayer Time", p_msg)

                    # 2. Gentle TTS chime through Xperia speaker
                    audio_bridge.speak(f"{p_name} time in Palakkad has started.", mood="F1")
            except Exception as pe:
                pass

            # B. Due Recurring & One-Shot Tasks
            due_tasks = []
            with self._lock:
                for tid, t in list(self.tasks.items()):
                    if now >= t["next_run"]:
                        due_tasks.append((tid, dict(t)))
                        if t["is_recurring"]:
                            t["next_run"] = now + t["interval_sec"]
                            t["runs_count"] = t.get("runs_count", 0) + 1
                        else:
                            del self.tasks[tid]
                if due_tasks:
                    self.save_tasks()

            for tid, t in due_tasks:
                self._execute_due_task(t)

            time.sleep(5)

    def _execute_due_task(self, task: dict):
        label = task["label"]
        print(f"\n[Scheduler] 🔔 Triggered Task [{task['id']}]: '{label}'")

        # 1. Execute system command (remotely on MacBook if RPC connected, or local fallback)
        cmd = task.get("action_command")
        if cmd:
            try:
                if rpc_bridge.is_mac_online():
                    rpc_bridge.execute_remote_command(cmd)
                else:
                    from engine.system_control import system_controller
                    system_controller.execute_terminal(cmd)
            except Exception as e:
                print(f"[Scheduler Command Error] {e}")

        # 2. Multi-Device Notification Delivery:
        # A. MacBook desktop notification
        rpc_bridge.send_remote_notification("Project Zia Task", label)

        # B. Xperia physical speaker alert
        audio_bridge.speak(f"Reminder: {label}", mood="F4")


# Global unified scheduler singleton
scheduler = UnifiedScheduler()
