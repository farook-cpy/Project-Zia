import asyncio
import sys
import time
from datetime import datetime
import psutil
import json

from engine.system_control import system_controller, _is_android
from engine.texture_mod import living_assets
from engine.tts_engine import tts_engine
from engine.subagents import subagent_pool
from engine.vision_senses import vision_senses
from engine.prayer_times import prayer_engine
from engine.alarm_manager import alarm_manager

class AutonomousHeartbeat:
    """
    V2 Proactive Event Loop with Dedicated Thermal Watchdog Daemon.
    Monitors:
    - CPU core temperatures (lm-sensors / Android sysfs) & thermal emergency throttling (5 FPS)
    - System CPU/RAM spikes
    - User idle time & organic sleep transitions (F11 Sleep)
    - Battery critical alerts & evening time-of-day ambient skin swapping

    On Android (Termux / Snapdragon 888), reads ~/.zia_thermal.conf for
    device-specific critical/safe temperature thresholds.
    """
    def __init__(self):
        self.last_user_activity = time.time()
        self.high_cpu_count = 0
        self.battery_alerted = False
        self.is_sleeping = False
        self.current_time_period = None # 'day' or 'night'

        # Thermal Watchdog parameters — defaults safe for all hardware
        # Overridden by ~/.zia_thermal.conf on Xperia / Android
        self.CRITICAL_TEMP_C = 80.0
        self.SAFE_TEMP_C = 68.0
        self.THROTTLE_FPS = 5
        self.NORMAL_FPS = 28
        self.is_thermally_throttled = False
        self.sustained_high_load_count = 0

        # Load Xperia thermal config if present
        self._load_thermal_config()

        # Offline Vision Behavioral Senses (Vector 6)
        self.last_stress_alert_time = 0.0
        self.last_vision_state = None
        self.vision_idle_locked = False

    def _load_thermal_config(self):
        """
        Reads ~/.zia_thermal.conf (written by install_xperia.sh) to apply
        Snapdragon 888-specific thermal thresholds at runtime.
        """
        import os
        from pathlib import Path
        cfg_path = Path.home() / ".zia_thermal.conf"
        if not cfg_path.exists():
            return
        try:
            for line in cfg_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key, val = key.strip(), val.strip()
                if key == "CRITICAL_TEMP_C":
                    self.CRITICAL_TEMP_C = float(val)
                elif key == "SAFE_TEMP_C":
                    self.SAFE_TEMP_C = float(val)
                elif key == "THROTTLE_FPS":
                    self.THROTTLE_FPS = int(val)
                elif key == "NORMAL_FPS":
                    self.NORMAL_FPS = int(val)
        except Exception:
            pass

    def register_activity(self):
        """Called whenever user types, moves cursor, or sends a prompt."""
        self.last_user_activity = time.time()
        if self.is_sleeping:
            self.is_sleeping = False
            return True # Woke up
        return False

    def get_cpu_temperature(self) -> float | None:
        """
        Reads CPU core temperatures across platforms:
        1. Android (Termux): reads Snapdragon thermal zones from sysfs via
           system_controller.get_cpu_temperature_android()
        2. Linux: psutil sensors_temperatures() (lm-sensors)
        3. Windows: WMI MSAcpi_ThermalZoneTemperature fallback
        Returns the highest temperature in Celsius, or None if unreadable.
        """
        # 1. Android sysfs path (Snapdragon 888 thermal zones)
        if system_controller.is_android:
            temp = system_controller.get_cpu_temperature_android()
            if temp is not None:
                return temp

        try:
            # 2. psutil hardware sensors (lm-sensors on Linux)
            sensors = getattr(psutil, "sensors_temperatures", lambda: {})() or {}
            temps = []
            for name, entries in sensors.items():
                for entry in entries:
                    if entry.current and entry.current > 0:
                        temps.append(entry.current)
            if temps:
                return max(temps)

            # 3. Windows WMI fallback
            if sys.platform == "win32":
                import subprocess
                cmd = "Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature -ErrorAction SilentlyContinue | Select-Object -ExpandProperty CurrentTemperature"
                res = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=2)
                raw = res.stdout.strip()
                if raw and raw.isdigit():
                    # Kelvin * 10 to Celsius
                    celsius = (float(raw) / 10.0) - 273.15
                    if 10 < celsius < 115:
                        return celsius
        except Exception:
            pass
        return None

    async def run_loop(self, broadcast_callback):
        """
        Runs the proactive heartbeat & thermal watchdog check every 60 seconds.
        broadcast_callback is an async function: async def (event_dict)
        """
        print("[Heartbeat] Autonomous Proactive Event Loop V2 + Thermal Watchdog initialized.")
        try:
            vision_senses.start()
        except Exception as ve:
            print(f"[Heartbeat] Vision senses startup notice: {ve}")

        # Register non-blocking alarm trigger broadcast callback
        def _on_alarm_broadcast(alarm_dict):
            async def _send():
                try:
                    text = f"Reminder: {alarm_dict.get('label', 'Timer')}!"
                    audio = await tts_engine.generate_speech_base64(text, mood="F4")
                    await broadcast_callback({
                        "type": "proactive_response",
                        "text": text,
                        "mood": "F4",
                        "audio": audio
                    })
                except Exception:
                    pass
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_send())
            except RuntimeError:
                pass

        alarm_manager.set_trigger_callback(_on_alarm_broadcast)
        await asyncio.sleep(10) # Startup settling delay

        while True:
            await asyncio.sleep(45)

            try:
                now = datetime.now()
                idle_seconds = time.time() - self.last_user_activity

                # -------------------------------------------------------------
                # Vector 1: Dedicated Thermal Watchdog Daemon (lm-sensors)
                # -------------------------------------------------------------
                current_temp = self.get_cpu_temperature()
                cpu_pct = psutil.cpu_percent(interval=0.5)

                # Fallback to sustained high load if hardware temperature sensor is unexposed
                is_overheating = False
                if current_temp is not None:
                    is_overheating = (current_temp >= self.CRITICAL_TEMP_C)
                else:
                    if cpu_pct > 90:
                        self.sustained_high_load_count += 1
                    else:
                        self.sustained_high_load_count = 0
                    is_overheating = (self.sustained_high_load_count >= 3)

                if is_overheating and not self.is_thermally_throttled:
                    self.is_thermally_throttled = True
                    subagent_pool.set_throttled(True)

                    # Throttle UI to emergency FPS (5 on desktop, configurable on Android)
                    await broadcast_callback({
                        "type": "set_framerate",
                        "fps": self.THROTTLE_FPS,
                        "reason": "thermal_protection"
                    })

                    temp_str = f"{int(current_temp)}°C" if current_temp else f"{int(cpu_pct)}% sustained load"
                    alert_text = (
                        f"Thermal Watchdog Warning: CPU reached {temp_str}! "
                        f"Throttling subagent worker pools and dropping UI to {self.THROTTLE_FPS} FPS to prevent thermal runaway."
                    )
                    audio = await tts_engine.generate_speech_base64(alert_text)

                    await broadcast_callback({
                        "type": "proactive_response",
                        "text": alert_text,
                        "mood": "F10",
                        "audio": audio
                    })
                    continue

                elif self.is_thermally_throttled:
                    # Check if cooled down
                    is_cooled = False
                    if current_temp is not None:
                        is_cooled = (current_temp <= self.SAFE_TEMP_C)
                    else:
                        is_cooled = (cpu_pct < 60)

                    if is_cooled:
                        self.is_thermally_throttled = False
                        subagent_pool.set_throttled(False)

                        # Restore normal FPS UI
                        await broadcast_callback({
                            "type": "set_framerate",
                            "fps": self.NORMAL_FPS,
                            "reason": "thermal_normalized"
                        })

                        temp_str = f"{int(current_temp)}°C" if current_temp else "normal"
                        recovery_text = f"Thermal Watchdog: CPU cooled down to {temp_str}. Restoring full performance and {self.NORMAL_FPS} FPS UI."
                        audio = await tts_engine.generate_speech_base64(recovery_text)

                        await broadcast_callback({
                            "type": "proactive_response",
                            "text": recovery_text,
                            "mood": "F4",
                            "audio": audio
                        })
                        continue

                # -------------------------------------------------------------
                # Vector 2: User Idle Time & Organic Sleep Physics
                # -------------------------------------------------------------
                if idle_seconds > 1200 and not self.is_sleeping: # 20 minutes idle
                    self.is_sleeping = True
                    print("[Heartbeat] User idle for >20min. Shifting Zia to F11 Sleep.")
                    await broadcast_callback({
                        "type": "expression",
                        "id": "F11"
                    })
                    continue

                # -------------------------------------------------------------
                # Vector 3: CPU/RAM Load Governor (CPU > 85% or RAM > 88%)
                # -------------------------------------------------------------
                ram_pct = psutil.virtual_memory().percent
                is_resource_strained = (cpu_pct > 85 or ram_pct > 88)

                if is_resource_strained:
                    self.high_cpu_count += 1
                    # Dynamically throttle subagents to protect 2007 Core 2 Duo
                    subagent_pool.set_throttled(True)
                else:
                    self.high_cpu_count = 0
                    if not self.is_thermally_throttled:
                        subagent_pool.set_throttled(False)

                if self.high_cpu_count >= 2:
                    self.high_cpu_count = 0
                    health = system_controller.get_system_health()
                    top_proc = health["top_processes"][0] if health["top_processes"] else "background task"
                    text = f"Notice: System load spiked to {int(cpu_pct)}% CPU and {int(ram_pct)}% RAM. Load governor throttled subagent workers. Heavy task: {top_proc}."
                    audio = await tts_engine.generate_speech_base64(text)

                    await broadcast_callback({
                        "type": "proactive_response",
                        "text": text,
                        "mood": "F7",
                        "audio": audio
                    })
                    continue

                # -------------------------------------------------------------
                # Vector 4: Battery Critical Warnings
                # On Android, queries termux-battery-status for temperature too.
                # On desktop, falls back to psutil.sensors_battery().
                # -------------------------------------------------------------
                try:
                    batt = system_controller.get_battery_status()
                    batt_pct = batt.get("percent")
                    batt_plugged = batt.get("plugged_in")
                    batt_temp = batt.get("temperature_c")

                    if batt_pct is not None and not batt_plugged:
                        if batt_pct <= 15 and not self.battery_alerted:
                            self.battery_alerted = True
                            text = f"Your battery is critical at {int(batt_pct)}%! Please plug me in so we don't shut down."
                            audio = await tts_engine.generate_speech_base64(text)

                            await broadcast_callback({
                                "type": "proactive_response",
                                "text": text,
                                "mood": "F6",
                                "audio": audio
                            })
                            continue
                        elif batt_pct > 20:
                            self.battery_alerted = False

                    # Android-specific: warn on high battery temperature (Snapdragon 888)
                    if batt_temp is not None and batt_temp > 42 and not self.is_thermally_throttled:
                        health_text = (
                            f"Battery temperature is {batt_temp:.1f}°C — above the 42°C comfort zone "
                            f"for Snapdragon 888. Consider reducing screen brightness or pausing heavy tasks."
                        )
                        audio = await tts_engine.generate_speech_base64(health_text)
                        await broadcast_callback({
                            "type": "proactive_response",
                            "text": health_text,
                            "mood": "F7",
                            "audio": audio
                        })
                except Exception:
                    pass

                # -------------------------------------------------------------
                # Vector 5: Time-of-Day Ambient Transitions (Night/Day Skin Swap)
                # -------------------------------------------------------------
                is_night = (now.hour >= 20 or now.hour < 7)
                period = "night" if is_night else "day"

                if self.current_time_period is None:
                    self.current_time_period = period

                if period != self.current_time_period:
                    self.current_time_period = period
                    print(f"[Heartbeat] Time-of-day transition detected: {period.upper()}")

                    swap_res = living_assets.apply_style(period)
                    if swap_res.get("success"):
                        await broadcast_callback({
                            "type": "reload_texture",
                            "index": 0,
                            "url": swap_res["texture_url"]
                        })

                        text = "It's past 8 PM. Shifting into ambient evening mode!" if is_night else "Good morning! Shifting back to daylight style."
                        audio = await tts_engine.generate_speech_base64(text)

                        await broadcast_callback({
                            "type": "proactive_response",
                            "text": text,
                            "mood": "F4" if not is_night else "F11",
                            "audio": audio
                        })

                # -------------------------------------------------------------
                # Vector 6: Offline Computer Vision Behavioral State Triggers
                # -------------------------------------------------------------
                try:
                    v_state = vision_senses.get_current_state()
                    v_current = v_state.get("state")
                    v_duration = v_state.get("duration_sec", 0.0)

                    # State 1: Stressed (furrowed brow / micro-jitter persistent > 60s)
                    if v_current == "stressed" and v_duration >= 60.0:
                        if (time.time() - self.last_stress_alert_time) > 300.0:  # 5 min cooldown
                            self.last_stress_alert_time = time.time()
                            stress_msg = "You've been frowning at the screen for a while. Want me to clear your notification queue or play a background soundscape?"
                            audio = await tts_engine.generate_speech_base64(stress_msg, mood="F3")
                            await broadcast_callback({
                                "type": "proactive_response",
                                "text": stress_msg,
                                "mood": "F3",
                                "audio": audio
                            })
                            continue

                    # State 2: Walking / Away (absence of face persistent > 60s)
                    elif v_current == "away" and v_duration >= 60.0:
                        if not self.vision_idle_locked and not self.is_sleeping:
                            self.vision_idle_locked = True
                            self.is_sleeping = True
                            print("[Heartbeat] Vision detected user away for >60s. Engaging idle power-saving (5 FPS & F11 Sleep).")
                            await broadcast_callback({
                                "type": "set_framerate",
                                "fps": 5,
                                "reason": "vision_idle_power_saving"
                            })
                            await broadcast_callback({
                                "type": "expression",
                                "id": "F11"
                            })
                            continue

                    # User returns from away
                    elif v_current in ["neutral", "thinking"] and self.vision_idle_locked:
                        self.vision_idle_locked = False
                        self.is_sleeping = False
                        print("[Heartbeat] Vision detected user returned. Restoring active UI.")
                        await broadcast_callback({
                            "type": "set_framerate",
                            "fps": self.NORMAL_FPS,
                            "reason": "user_returned"
                        })
                        await broadcast_callback({
                            "type": "expression",
                            "id": "F1" if v_current == "neutral" else "F8"
                        })

                    # State 3: Thinking (head tilt / chin pose)
                    elif v_current == "thinking" and v_duration >= 10.0 and not self.is_sleeping:
                        if self.last_vision_state != "thinking":
                            await broadcast_callback({
                                "type": "expression",
                                "id": "F8"
                            })

                    self.last_vision_state = v_current
                except Exception as ve:
                    pass

                # -------------------------------------------------------------
                # Vector 7: Palakkad Prayer Times Daily Check-in (Palakkad, Kerala)
                # -------------------------------------------------------------
                try:
                    prayer_prompt = prayer_engine.check_prayer_prompt_needed()
                    if prayer_prompt:
                        prompt_text = prayer_prompt["prompt"]
                        print(f"\n[Heartbeat // Prayer] {prompt_text}")

                        # Softly adjust Live2D expression to calm/respectful expression (F1)
                        await broadcast_callback({
                            "type": "expression",
                            "id": "F1"
                        })

                        audio = await tts_engine.generate_speech_base64(prompt_text, mood="F1")
                        await broadcast_callback({
                            "type": "proactive_response",
                            "text": prompt_text,
                            "mood": "F1",
                            "audio": audio
                        })
                except Exception as pe:
                    pass

            except Exception as e:
                print(f"[Heartbeat Loop Error] {e}")

heartbeat_engine = AutonomousHeartbeat()
