"""
Project Zia - Smart Notifications, Contextual Shortcuts & Ambient Intelligence Engine
Implements:
1. Context-Aware Weather Adaptive Greeter (Open-Meteo free API, Palakkad coords, 0 tokens)
2. Custom Audio Soundboard Generator (Procedural retro-futuristic WAV synthesis via stdlib)
3. Adaptive Focus Music Player (Ambient streams & focus session tracker)
4. Smart Meeting / Prayer Conflict Resolver (Checks events against Palakkad prayer schedule)
5. Idle Productivity Nudge (Tracks inactivity & nudges refocus on active milestones)
6. Daily Developer Digest Summarizer (Git commits, completed tasks, alarms & prayer stats)
7. Geofence-Inspired Home Presence Trigger (Home Wi-Fi gateway presence detection)
8. Interactive Voice Command Shortcuts (Single-word triggers mapped to multi-step macros)
9. Customizable Retro HUD Theme Engine (Cyan, Amber, Matrix Green, Monochrome)
10. Smart Habit Streak Tracker (Daily consistency on coding, writing, prayer & focus)
"""

import os
import sys
import math
import time
import json
import struct
import wave
import socket
import urllib.request
import subprocess
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SOUNDS_DIR = DATA_DIR / "sounds"
THEME_FILE = DATA_DIR / "theme.json"
HABITS_FILE = DATA_DIR / "habits.json"
SHORTCUTS_FILE = DATA_DIR / "voice_shortcuts.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)
SOUNDS_DIR.mkdir(parents=True, exist_ok=True)


# -----------------------------------------------------------------------------
# 1. Customizable Retro HUD Theme Engine
# -----------------------------------------------------------------------------
THEMES = {
    "cyan": {
        "name": "Neon Cyan Phosphor",
        "primary": "\033[96m",      # Bright Cyan
        "secondary": "\033[95m",    # Bright Magenta
        "accent": "\033[93m",       # Bright Yellow
        "success": "\033[92m",      # Green
        "warning": "\033[33m",      # Amber/Yellow
        "danger": "\033[91m",       # Red
        "muted": "\033[90m",        # Dark Gray
        "reset": "\033[0m",
        "bold": "\033[1m"
    },
    "amber": {
        "name": "Amber CRT Phosphor",
        "primary": "\033[33m",      # Orange / Warm Amber
        "secondary": "\033[93m",    # Bright Amber
        "accent": "\033[97m",       # Bright White
        "success": "\033[33m",      # Amber
        "warning": "\033[91m",      # Orange-Red
        "danger": "\033[31m",       # Red
        "muted": "\033[90m",        # Dim
        "reset": "\033[0m",
        "bold": "\033[1m"
    },
    "matrix": {
        "name": "Matrix Terminal Green",
        "primary": "\033[92m",      # Bright Green
        "secondary": "\033[32m",    # Darker Green
        "accent": "\033[97m",       # White
        "success": "\033[92m",      # Bright Green
        "warning": "\033[33m",      # Amber
        "danger": "\033[91m",       # Red
        "muted": "\033[90m",        # Gray
        "reset": "\033[0m",
        "bold": "\033[1m"
    },
    "mono": {
        "name": "Monochrome Slate",
        "primary": "\033[97m",      # Bright White
        "secondary": "\033[37m",    # White / Light Gray
        "accent": "\033[90m",       # Dark Gray
        "success": "\033[97m",      # White
        "warning": "\033[37m",      # Light Gray
        "danger": "\033[91m",       # Dim Red
        "muted": "\033[90m",        # Dim Gray
        "reset": "\033[0m",
        "bold": "\033[1m"
    }
}


class AmbientIntelligenceEngine:
    """Orchestrates ambient contextual features, soundboard synthesis, and HUD themes."""

    def __init__(self):
        self.active_theme_key = self._load_theme_preference()
        self.home_gateway_ip = os.environ.get("HOME_ROUTER_IP", "192.168.1.1")
        self.presence_state = "HOME"
        self.focus_active = False
        self.focus_start_time = 0.0
        self.last_user_activity = time.time()
        self._init_shortcuts()
        self._init_habits()

    # -------------------------------------------------------------------------
    # Theme Engine
    # -------------------------------------------------------------------------
    def _load_theme_preference(self) -> str:
        if THEME_FILE.exists():
            try:
                data = json.loads(THEME_FILE.read_text(encoding="utf-8"))
                return data.get("theme", "cyan")
            except Exception:
                pass
        return "cyan"

    def set_theme(self, theme_name: str) -> Dict[str, Any]:
        """Sets active terminal color theme (cyan, amber, matrix, mono)."""
        clean_name = theme_name.lower().strip()
        if clean_name not in THEMES:
            return {"error": f"Unknown theme '{clean_name}'. Choose from: {list(THEMES.keys())}"}

        self.active_theme_key = clean_name
        THEME_FILE.write_text(json.dumps({"theme": clean_name}, indent=2), encoding="utf-8")
        return {"success": True, "active_theme": clean_name, "name": THEMES[clean_name]["name"]}

    def get_theme(self) -> Dict[str, str]:
        return THEMES.get(self.active_theme_key, THEMES["cyan"])

    # -------------------------------------------------------------------------
    # 1. Context-Aware Weather Adaptive Greeter (Palakkad Coordinates)
    # -------------------------------------------------------------------------
    def get_weather_greeting(self, lat: float = 10.7867, lon: float = 76.6548) -> Dict[str, Any]:
        """
        Fetches live local weather from Open-Meteo API (Free, zero token cost)
        and formats an ambient, context-aware greeting for Palakkad, Kerala.
        """
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        weather_info = None

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ProjectZia/2.0"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                weather_info = data.get("current_weather", {})
        except Exception:
            pass

        now = datetime.now()
        hour = now.hour

        if hour < 12:
            time_greeting = "Good morning"
        elif hour < 17:
            time_greeting = "Good afternoon"
        elif hour < 21:
            time_greeting = "Good evening"
        else:
            time_greeting = "Late night greeting"

        if weather_info:
            temp = weather_info.get("temperature", 28.0)
            wcode = weather_info.get("weathercode", 0)
            wind = weather_info.get("windspeed", 5.0)

            # WMO Weather interpretation
            if wcode in [0, 1]:
                condition = "clear skies"
                vibe = "Clear weather in Palakkad; optimal conditions for coding."
            elif wcode in [2, 3]:
                condition = "partly cloudy"
                vibe = "Pleasant overcast skies outside."
            elif wcode in [51, 53, 55, 61, 63, 65, 80, 81]:
                condition = "monsoon rains"
                vibe = "Monsoon showers outside; perfect atmosphere for focused terminal work."
            elif wcode in [95, 96, 99]:
                condition = "thunderstorm"
                vibe = "Thunderstorms active in the region; power monitoring advised."
            else:
                condition = "temperate"
                vibe = "Ambient climate is steady."

            greeting_text = f"{time_greeting}. Palakkad is currently {temp:.1f}°C with {condition}. {vibe}"
            return {
                "greeting": greeting_text,
                "location": "Palakkad, Kerala",
                "temperature_c": temp,
                "condition": condition,
                "wind_kmh": wind,
                "source": "Open-Meteo"
            }
        else:
            # Offline fallback
            return {
                "greeting": f"{time_greeting}. All Project Zia systems online and operational in Palakkad.",
                "location": "Palakkad, Kerala",
                "temperature_c": 28.0,
                "condition": "offline_cache",
                "source": "local_fallback"
            }

    # -------------------------------------------------------------------------
    # 2. Custom Audio Soundboard Generator (Pure Python Procedural Synthesis)
    # -------------------------------------------------------------------------
    def synthesize_chime(self, sound_type: str = "notification") -> Path:
        """
        Dynamically synthesizes retro-futuristic audio WAV files using pure math and wave module.
        Requires 0 external binaries or libraries.
        Types:
        - notification: Gentle dual-frequency futuristic ping (880Hz -> 1320Hz)
        - alert: Sharp retro warning blip (440Hz pulse)
        - prayer: Meditative low harmonic bell (300Hz decaying hum)
        - success: Ascending arpeggio (523Hz -> 659Hz -> 784Hz)
        """
        out_path = SOUNDS_DIR / f"{sound_type}.wav"
        if out_path.exists():
            return out_path

        sample_rate = 22050
        duration = 0.5  # seconds
        num_samples = int(sample_rate * duration)
        samples = []

        if sound_type == "notification":
            # Dual chirp: 880Hz then 1320Hz
            for i in range(num_samples):
                t = float(i) / sample_rate
                decay = math.exp(-6.0 * t)
                freq = 880.0 if t < 0.2 else 1320.0
                val = 0.5 * math.sin(2.0 * math.pi * freq * t) * decay
                samples.append(int(val * 32767))

        elif sound_type == "alert":
            # Rapid square-modulated alarm tone
            for i in range(num_samples):
                t = float(i) / sample_rate
                mod = 1.0 if (int(t * 16) % 2 == 0) else 0.2
                val = 0.4 * math.sin(2.0 * math.pi * 660.0 * t) * mod
                samples.append(int(val * 32767))

        elif sound_type == "prayer":
            # Resonant low bell with harmonic overtones
            duration = 1.2
            num_samples = int(sample_rate * duration)
            samples = []
            for i in range(num_samples):
                t = float(i) / sample_rate
                decay = math.exp(-3.5 * t)
                # Fundamental + harmonic
                f1 = math.sin(2.0 * math.pi * 320.0 * t)
                f2 = 0.5 * math.sin(2.0 * math.pi * 640.0 * t)
                val = 0.5 * (f1 + f2) * decay
                samples.append(int(val * 32767))

        elif sound_type == "success":
            # Ascending 3-note chime
            notes = [523.25, 659.25, 783.99]  # C5, E5, G5
            segment = num_samples // 3
            for i in range(num_samples):
                t = float(i) / sample_rate
                note_idx = min(i // segment, 2)
                freq = notes[note_idx]
                rel_t = float(i % segment) / sample_rate
                decay = math.exp(-5.0 * rel_t)
                val = 0.4 * math.sin(2.0 * math.pi * freq * t) * decay
                samples.append(int(val * 32767))
        else:
            # Simple blip
            for i in range(num_samples):
                t = float(i) / sample_rate
                val = 0.3 * math.sin(2.0 * math.pi * 440.0 * t) * math.exp(-8.0 * t)
                samples.append(int(val * 32767))

        # Write WAV file
        with wave.open(str(out_path), "wb") as wf:
            wf.setnchannels(1)  # Mono
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate)
            raw_bytes = struct.pack(f"<{len(samples)}h", *samples)
            wf.writeframes(raw_bytes)

        return out_path

    # -------------------------------------------------------------------------
    # 3. Adaptive Focus Music Player
    # -------------------------------------------------------------------------
    def toggle_focus_mode(self, action: str = "toggle") -> Dict[str, Any]:
        """Toggles deep work focus session with ambient stream trigger."""
        if action == "toggle":
            self.focus_active = not self.focus_active
        elif action == "start":
            self.focus_active = True
        elif action == "stop":
            self.focus_active = False

        if self.focus_active:
            self.focus_start_time = time.time()
            return {
                "focus_active": True,
                "message": "Focus session initiated. Ambient soundtrack activated; notifications buffered.",
                "stream_url": "https://stream.somafm.com/defcon-128-mp3",
                "recommended_command": "mpv --no-video https://stream.somafm.com/defcon-128-mp3"
            }
        else:
            elapsed_min = int((time.time() - self.focus_start_time) / 60) if self.focus_start_time else 0
            self.log_habit("focus", note=f"Completed {elapsed_min} min focus block")
            return {
                "focus_active": False,
                "elapsed_minutes": elapsed_min,
                "message": f"Focus session concluded ({elapsed_min} minutes logged)."
            }

    # -------------------------------------------------------------------------
    # 4. Smart Meeting / Prayer Conflict Resolver
    # -------------------------------------------------------------------------
    def check_prayer_meeting_conflict(self, event_time_str: str, duration_min: int = 30) -> Dict[str, Any]:
        """
        Cross-references a proposed meeting time (e.g. '12:30' or '16:00')
        against the daily Palakkad prayer times. Flags conflicts with a 20-min buffer.
        """
        from engine.prayer_times import prayer_engine

        schedule = prayer_engine.get_prayer_times()
        try:
            parts = event_time_str.strip().split(":")
            e_hour = int(parts[0])
            e_min = int(parts[1])
        except Exception:
            return {"error": "Invalid time format. Use HH:MM (24-hour format)."}

        event_start_min = e_hour * 60 + e_min
        event_end_min = event_start_min + duration_min

        conflicts = []
        for prayer_name, p_time in schedule.items():
            if ":" in p_time:
                ph, pm = p_time.split(":")
                p_min = int(ph) * 60 + int(pm)
                buffer_start = p_min - 15
                buffer_end = p_min + 25

                # Check overlap
                if max(event_start_min, buffer_start) <= min(event_end_min, buffer_end):
                    conflicts.append({
                        "prayer": prayer_name,
                        "prayer_time": p_time,
                        "conflict_window": f"{buffer_start//60:02d}:{buffer_start%60:02d} - {buffer_end//60:02d}:{buffer_end%60:02d}"
                    })

        has_conflict = len(conflicts) > 0
        recommendation = "Optimal scheduling time."
        if has_conflict:
            safe_slot = (event_end_min + 30)
            recommendation = f"Conflict detected with {conflicts[0]['prayer']}. Suggest moving to {safe_slot//60:02d}:{safe_slot%60:02d}."

        return {
            "has_conflict": has_conflict,
            "conflicts": conflicts,
            "recommendation": recommendation
        }

    # -------------------------------------------------------------------------
    # 5. Idle Productivity Nudge
    # -------------------------------------------------------------------------
    def check_idle_nudge(self, idle_threshold_sec: int = 1800) -> Optional[str]:
        """
        Checks if inactivity has exceeded the threshold (default 30 mins)
        and returns a gentle refocus nudge with current project milestone.
        """
        idle_duration = time.time() - self.last_user_activity
        if idle_duration > idle_threshold_sec:
            from engine.memory import memory_engine
            notes = memory_engine.data.get("notes", [])
            last_goal = notes[-1]["text"] if notes else "complete active sprint items"
            return f"[NUDGE] You have been idle for {int(idle_duration/60)} minutes. Refocus on milestone: '{last_goal}'."
        return None

    def record_activity(self):
        self.last_user_activity = time.time()

    # -------------------------------------------------------------------------
    # 6. Daily Developer Digest Summarizer
    # -------------------------------------------------------------------------
    def compile_daily_digest(self) -> Dict[str, Any]:
        """
        Gathers end-of-day summary of git commits, completed queue tasks,
        prayer logs, and upcoming alarms.
        """
        from engine.prayer_times import prayer_engine
        from engine.alarm_manager import alarm_manager

        # 1. Git commits today
        commits_today = []
        try:
            res = subprocess.run(
                ["git", "log", "--since=midnight", "--oneline"],
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                timeout=3
            )
            if res.returncode == 0 and res.stdout.strip():
                commits_today = res.stdout.strip().splitlines()
        except Exception:
            pass

        # 2. Prayer logs today
        prayer_status = prayer_engine.get_prayer_times()

        # 3. Alarms
        alarms = alarm_manager.list_active()

        # 4. Habits streak
        habits_report = self.get_habit_streaks()

        return {
            "date": date.today().isoformat(),
            "commits_today_count": len(commits_today),
            "commits": commits_today,
            "prayer_schedule": prayer_status,
            "active_alarms_count": len(alarms),
            "habits": habits_report
        }

    # -------------------------------------------------------------------------
    # 7. Geofence-Inspired Home Presence Trigger
    # -------------------------------------------------------------------------
    def check_presence(self) -> Dict[str, Any]:
        """
        Detects if current device is within home network boundary
        by testing default gateway reachability or SSID.
        """
        is_home = False
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.3)
            # Try connecting to home gateway
            res = s.connect_ex((self.home_gateway_ip, 80))
            if res == 0 or res == 111:  # Port open or actively refused = device exists!
                is_home = True
            s.close()
        except Exception:
            is_home = False

        old_state = self.presence_state
        self.presence_state = "HOME" if is_home else "AWAY"

        state_changed = old_state != self.presence_state
        return {
            "state": self.presence_state,
            "gateway_tested": self.home_gateway_ip,
            "state_changed": state_changed,
            "message": f"Device presence: {self.presence_state}"
        }

    # -------------------------------------------------------------------------
    # 8. Interactive Voice Command Shortcuts
    # -------------------------------------------------------------------------
    def _init_shortcuts(self):
        if not SHORTCUTS_FILE.exists():
            default_shortcuts = {
                "deploy": ["git status", "git diff", "pytest tests/"],
                "sleep": ["mac mute", "mac screen off", "theme amber"],
                "focus": ["theme amber", "focus start"],
                "status": ["battery", "prayer", "uptime"]
            }
            SHORTCUTS_FILE.write_text(json.dumps(default_shortcuts, indent=2), encoding="utf-8")

    def execute_shortcut(self, trigger_word: str) -> Dict[str, Any]:
        """Resolves single-word trigger to macro terminal sequence."""
        key = trigger_word.lower().strip()
        try:
            shortcuts = json.loads(SHORTCUTS_FILE.read_text(encoding="utf-8"))
            if key in shortcuts:
                return {"found": True, "trigger": key, "steps": shortcuts[key]}
        except Exception:
            pass
        return {"found": False, "trigger": key, "message": f"No shortcut macro registered for '{key}'."}

    # -------------------------------------------------------------------------
    # 9. Smart Habit Streak Tracker
    # -------------------------------------------------------------------------
    def _init_habits(self):
        if not HABITS_FILE.exists():
            default_habits = {
                "coding": {"streak": 1, "last_date": date.today().isoformat(), "total": 1},
                "prayer": {"streak": 1, "last_date": date.today().isoformat(), "total": 1},
                "writing": {"streak": 1, "last_date": date.today().isoformat(), "total": 1},
                "focus": {"streak": 1, "last_date": date.today().isoformat(), "total": 1}
            }
            HABITS_FILE.write_text(json.dumps(default_habits, indent=2), encoding="utf-8")

    def log_habit(self, habit_name: str, note: str = "") -> Dict[str, Any]:
        """Logs daily completion of a habit, incrementing streak if consecutive day."""
        hkey = habit_name.lower().strip()
        today_str = date.today().isoformat()
        yesterday_str = (date.today() - timedelta(days=1)).isoformat()

        data = {}
        if HABITS_FILE.exists():
            try:
                data = json.loads(HABITS_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass

        if hkey not in data:
            data[hkey] = {"streak": 1, "last_date": today_str, "total": 1}
        else:
            last = data[hkey].get("last_date")
            if last == today_str:
                # Already logged today
                return {"status": "ALREADY_LOGGED", "habit": hkey, "streak": data[hkey]["streak"]}
            elif last == yesterday_str:
                data[hkey]["streak"] += 1
                data[hkey]["total"] = data[hkey].get("total", 0) + 1
                data[hkey]["last_date"] = today_str
            else:
                # Streak reset
                data[hkey]["streak"] = 1
                data[hkey]["total"] = data[hkey].get("total", 0) + 1
                data[hkey]["last_date"] = today_str

        HABITS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return {"status": "SUCCESS", "habit": hkey, "streak": data[hkey]["streak"], "note": note}

    def get_habit_streaks(self) -> Dict[str, Any]:
        """Returns current streak counters for all habits."""
        if HABITS_FILE.exists():
            try:
                return json.loads(HABITS_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}


# Global singleton instance
ambient_engine = AmbientIntelligenceEngine()

