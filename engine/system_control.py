import sys
import os
import time
import subprocess
import shutil
import json
from pathlib import Path
import psutil

_pyautogui = None

def _get_pyautogui():
    global _pyautogui
    if _pyautogui is None:
        try:
            import pyautogui
            _pyautogui = pyautogui
        except Exception:
            _pyautogui = None
    return _pyautogui

# ---------------------------------------------------------------------------
# Android / Termux platform detection helpers
# ---------------------------------------------------------------------------

def _is_android() -> bool:
    """Returns True when running inside Termux on Android."""
    return (
        os.path.isdir("/data/data/com.termux")
        or os.environ.get("TERMUX_MODE", "") == "1"
        or os.environ.get("PLATFORM", "") == "android"
    )

def _termux_cmd(cmd: list[str], timeout: int = 5) -> dict:
    """
    Runs a Termux:API CLI command (e.g. termux-battery-status).
    Returns {"success": bool, "output": str, "json": dict|None}.
    """
    if not shutil.which(cmd[0]):
        return {"success": False, "output": f"{cmd[0]} not found", "json": None}
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        raw = res.stdout.strip()
        parsed = None
        try:
            parsed = json.loads(raw)
        except Exception:
            pass
        return {"success": res.returncode == 0, "output": raw, "json": parsed}
    except subprocess.TimeoutExpired:
        return {"success": False, "output": f"{cmd[0]} timed out", "json": None}
    except Exception as exc:
        return {"success": False, "output": str(exc), "json": None}


class SystemController:
    def __init__(self):
        self.os_type = sys.platform
        self.is_android = _is_android()

    def execute_terminal(self, command: str, run_as_admin: bool = False) -> dict:
        """
        Executes terminal commands on the host OS, supporting administrator/sudo elevation.
        Uses passwordless sudo (sudo -n) or visudo rules when on Linux.
        """
        command = command.strip()
        print(f"[SystemController] Executing command (Admin={run_as_admin}): {command}")

        try:
            if self.os_type == "win32":
                if run_as_admin:
                    # Windows UAC elevation
                    ps_cmd = f"Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile', '-Command', '{command}'"
                    proc = subprocess.Popen(["powershell", "-NoProfile", "-Command", ps_cmd])
                    return {
                        "success": True,
                        "output": f"Launched elevated administrator terminal: {command}",
                        "elevated": True
                    }
                else:
                    res = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=20)
                    output = res.stdout.strip() or res.stderr.strip() or "Command completed with no output."
                    return {
                        "success": res.returncode == 0,
                        "output": output[:2000],
                        "returncode": res.returncode
                    }

            elif self.os_type == "linux":
                # Linux Mint / Ubuntu
                if run_as_admin:
                    # 1. Try passwordless non-interactive sudo (sudo -n)
                    cmd_sudo = f"sudo -n {command}"
                    res = subprocess.run(cmd_sudo, shell=True, capture_output=True, text=True, timeout=20)
                    if res.returncode == 0:
                        output = res.stdout.strip() or "Sudo command executed successfully."
                        return {"success": True, "output": output[:2000], "elevated": True}

                    # 2. If password required and pkexec available
                    if shutil.which("pkexec"):
                        cmd_pk = f"pkexec bash -c '{command}'"
                        proc = subprocess.Popen(cmd_pk, shell=True)
                        return {"success": True, "output": f"Launched via pkexec: {command}", "elevated": True}
                    else:
                        output = res.stderr.strip() or "Password required for sudo."
                        return {"success": False, "output": output, "elevated": True}
                else:
                    res = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=20)
                    output = res.stdout.strip() or res.stderr.strip() or "Command completed with no output."
                    return {"success": res.returncode == 0, "output": output[:2000], "returncode": res.returncode}

            else:
                # macOS
                if run_as_admin:
                    script = f'do shell script "{command}" with administrator privileges'
                    res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=20)
                    return {"success": res.returncode == 0, "output": res.stdout.strip() or res.stderr.strip()}
                else:
                    res = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=20)
                    return {"success": res.returncode == 0, "output": res.stdout.strip() or res.stderr.strip()}

        except subprocess.TimeoutExpired:
            return {"success": False, "output": "Command execution timed out after 20 seconds."}
        except Exception as e:
            return {"success": False, "output": f"Execution error: {str(e)}"}

    def setup_passwordless_sudo(self) -> dict:
        """
        Configures passwordless sudo for Project Zia maintenance commands via /etc/sudoers.d/zia.
        """
        if self.os_type != "linux":
            return {"success": False, "message": "Passwordless sudo is only applicable on Linux systems."}

        rule = f"{os.getenv('USER', 'ALL')} ALL=(ALL) NOPASSWD: ALL\n"
        cmd = f"echo '{rule.strip()}' | sudo tee /etc/sudoers.d/zia > /dev/null && sudo chmod 0440 /etc/sudoers.d/zia"
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return {"success": True, "message": "Successfully configured passwordless sudo in /etc/sudoers.d/zia."}

        if shutil.which("pkexec"):
            cmd_pk = f"pkexec bash -c \"echo '{rule.strip()}' > /etc/sudoers.d/zia && chmod 0440 /etc/sudoers.d/zia\""
            res_pk = subprocess.run(cmd_pk, shell=True, capture_output=True, text=True)
            if res_pk.returncode == 0:
                return {"success": True, "message": "Configured passwordless sudo via pkexec."}

        return {"success": False, "message": f"Failed to configure sudoers: {res.stderr.strip()}"}

    def lock_session(self) -> dict:
        """Locks the desktop session across Linux (XFCE/loginctl), Windows, or macOS."""
        try:
            if self.os_type == "linux":
                if shutil.which("loginctl"):
                    subprocess.run("loginctl lock-session", shell=True)
                elif shutil.which("xflock4"):
                    subprocess.run("xflock4", shell=True)
                elif shutil.which("xdg-screensaver"):
                    subprocess.run("xdg-screensaver lock", shell=True)
                return {"success": True, "message": "Desktop session locked."}
            elif self.os_type == "win32":
                subprocess.run("rundll32.exe user32.dll,LockWorkStation", shell=True)
                return {"success": True, "message": "Windows workstation locked."}
            elif self.os_type == "darwin":
                subprocess.run(["pmset", "displaysleepnow"])
                return {"success": True, "message": "macOS display put to sleep/locked."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def unlock_session(self) -> dict:
        """
        Unlocks or resumes the desktop session programmatically via system bus (loginctl/DBus).
        Wakes screen and dismisses screensaver without physical interaction.
        """
        try:
            if self.os_type == "linux":
                # 1. loginctl unlock-session
                if shutil.which("loginctl"):
                    subprocess.run("loginctl unlock-sessions || loginctl unlock-session", shell=True)
                # 2. Wake DPMS display
                if shutil.which("xset"):
                    subprocess.run("xset dpms force on", shell=True)
                # 3. Simulate key to dismiss lock screen if screensaver is active
                try:
                    ag = _get_pyautogui()
                    if ag:
                        ag.press("shift")
                except Exception:
                    pass
                return {"success": True, "message": "Session unlocked and display awakened."}
            elif self.os_type == "win32":
                # Wake display and dismiss lock wallpaper
                try:
                    ag = _get_pyautogui()
                    if ag:
                        ag.press("shift")
                        ag.press("space")
                except Exception:
                    pass
                return {"success": True, "message": "Display awakened and lock screen dismissed."}
            elif self.os_type == "darwin":
                subprocess.run(["caffeinate", "-u", "-t", "2"])
                return {"success": True, "message": "macOS display awakened and resumed."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def toggle_compositor(self, enable: bool = None) -> dict:
        """
        Toggles XFCE window compositing (xfwm4) on Linux Mint.
        Disabling compositing reclaims GPU fill-rate & VRAM on legacy Intel GMA / GeForce 8600M GT.
        """
        if self.os_type != "linux":
            return {"success": False, "message": "Display compositor toggle is designed for XFCE on Linux Mint."}

        if not shutil.which("xfconf-query"):
            return {"success": False, "message": "xfconf-query not found (non-XFCE environment)."}

        try:
            check = subprocess.run(
                ["xfconf-query", "-c", "xfwm4", "-p", "/general/use_compositing"],
                capture_output=True, text=True
            )
            current = check.stdout.strip().lower() == "true"
            target = (not current) if enable is None else bool(enable)

            subprocess.run(
                ["xfconf-query", "-c", "xfwm4", "-p", "/general/use_compositing", "-s", str(target).lower()],
                capture_output=True, text=True
            )
            state_str = "ENABLED" if target else "DISABLED (Maximum GPU Performance Mode)"
            return {"success": True, "compositor_enabled": target, "message": f"XFCE Window Compositor is now {state_str}."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def change_volume(self, action: str = "up", steps: int = 5) -> dict:
        """
        Adjusts system audio volume cross-platform.
        action: 'up', 'down', 'mute'
        """
        try:
            if self.os_type == "win32":
                key = "volumeup" if action == "up" else ("volumedown" if action == "down" else "volumemute")
                repeat = 1 if action == "mute" else max(1, steps)
                ag = _get_pyautogui()
                if ag:
                    for _ in range(repeat):
                        ag.press(key)
                return {"success": True, "action": f"volume_{action}", "steps": repeat}

            elif self.os_type == "linux":
                # PulseAudio / PipeWire on Linux Mint
                pct = f"{steps * 2}%"
                if action == "up":
                    subprocess.run(f"pactl set-sink-volume @DEFAULT_SINK@ +{pct}", shell=True)
                elif action == "down":
                    subprocess.run(f"pactl set-sink-volume @DEFAULT_SINK@ -{pct}", shell=True)
                else:
                    subprocess.run("pactl set-sink-mute @DEFAULT_SINK@ toggle", shell=True)
                return {"success": True, "action": f"volume_{action}"}

            elif self.os_type == "darwin":
                # macOS
                vol_delta = steps * 2
                sign = "+" if action == "up" else "-"
                osascript_cmd = f"set volume output volume (output volume of (get volume settings) {sign} {vol_delta})"
                subprocess.run(["osascript", "-e", osascript_cmd])
                return {"success": True, "action": f"volume_{action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def change_brightness(self, action: str = "up", amount: int = 15) -> dict:
        """
        Adjusts monitor display brightness cross-platform.
        """
        try:
            if self.os_type == "win32":
                # PowerShell WMI CIM brightness adjustment
                delta = amount if action == "up" else -amount
                ps_script = f"""
                $m = Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightness
                $curr = if ($m) {{ $m.CurrentBrightness }} else {{ 50 }}
                $target = [Math]::Max(10, [Math]::Min(100, $curr + ({delta})))
                (Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightnessMethods).WmiSetBrightness(1, $target)
                """
                subprocess.Popen(["powershell", "-NoProfile", "-Command", ps_script])
                return {"success": True, "action": f"brightness_{action}"}

            elif self.os_type == "linux":
                # Linux Mint brightnessctl or xrandr
                pct = f"{amount}%"
                sign = "+" if action == "up" else "-"
                if shutil.which("brightnessctl"):
                    subprocess.Popen(f"brightnessctl set {pct}{sign}", shell=True)
                else:
                    # xrandr fallback
                    subprocess.Popen(f"xrandr --output $(xrandr | grep ' connected' | cut -f1 -d' ') --brightness 0.8", shell=True)
                return {"success": True, "action": f"brightness_{action}"}

            elif self.os_type == "darwin":
                # macOS
                if shutil.which("brightness"):
                    val = "+0.1" if action == "up" else "-0.1"
                    subprocess.Popen(f"brightness {val}", shell=True)
                return {"success": True, "action": f"brightness_{action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # -------------------------------------------------------------
    # 11. Partition & Mount Manager
    # -------------------------------------------------------------
    def list_partitions(self) -> list:
        parts = []
        for p in psutil.disk_partitions(all=False):
            usage = None
            try:
                u = psutil.disk_usage(p.mountpoint)
                usage = {
                    "total_gb": round(u.total / (1024**3), 1),
                    "free_gb": round(u.free / (1024**3), 1),
                    "percent": u.percent
                }
            except Exception:
                pass
            parts.append({
                "device": p.device,
                "mountpoint": p.mountpoint,
                "fstype": p.fstype,
                "usage": usage
            })
        return parts

    def mount_device(self, device: str) -> dict:
        if self.os_type == "linux":
            cmd = f"udisksctl mount -b {device}" if shutil.which("udisksctl") else f"sudo -n mount {device}"
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return {"success": res.returncode == 0, "output": res.stdout.strip() or res.stderr.strip()}
        return {"success": False, "message": "Manual partition mounting is primarily handled on Linux."}

    def unmount_device(self, target: str) -> dict:
        if self.os_type == "linux":
            cmd = f"udisksctl unmount -b {target}" if shutil.which("udisksctl") else f"sudo -n umount {target}"
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return {"success": res.returncode == 0, "output": res.stdout.strip() or res.stderr.strip()}
        return {"success": False, "message": "Unmounting is primarily handled on Linux."}

    # -------------------------------------------------------------
    # 12. CPU Governor Frequency Switcher
    # -------------------------------------------------------------
    def get_cpu_governor(self) -> str:
        if self.os_type == "linux":
            gov_file = Path("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor")
            if gov_file.exists():
                return gov_file.read_text().strip()
        elif self.os_type == "win32":
            res = subprocess.run(["powercfg", "/getactivescheme"], capture_output=True, text=True)
            return res.stdout.strip().split("\n")[-1]
        return "balanced"

    def set_cpu_governor(self, governor: str = "powersave") -> dict:
        governor = governor.lower().strip()
        if self.os_type == "linux":
            valid = ["powersave", "performance", "ondemand", "conservative"]
            if governor not in valid:
                return {"success": False, "error": f"Invalid governor. Choose from: {valid}"}
            cmd = f"echo '{governor}' | sudo -n tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor"
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if res.returncode == 0:
                return {"success": True, "governor": governor, "message": f"CPU Governor set to {governor}."}
            return {"success": False, "error": res.stderr.strip() or "Requires sudo rights."}
        elif self.os_type == "win32":
            plans = {
                "powersave": "a1841308-3541-4fab-bc81-f71556f20b4a",
                "performance": "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",
                "balanced": "381b4222-f694-41f0-9685-ff5bb260df2e"
            }
            guid = plans.get(governor, plans["balanced"])
            res = subprocess.run(["powercfg", "/setactive", guid], capture_output=True, text=True)
            return {"success": res.returncode == 0, "governor": governor, "message": f"Windows Power Scheme set to {governor}."}
        return {"success": False, "message": "Not supported on this platform."}

    # -------------------------------------------------------------
    # 13. Backlight & Contrast Calibration Profiles
    # -------------------------------------------------------------
    def apply_display_profile(self, profile: str = "reading") -> dict:
        profile = profile.lower().strip()
        profiles = {
            "reading": {"brightness": 40, "gamma": "0.9:0.85:0.75", "desc": "Warm paper tint, reduces eye fatigue"},
            "movie": {"brightness": 85, "gamma": "1.05:1.05:1.1", "desc": "Punchy contrast and vibrant highlights"},
            "outdoor": {"brightness": 100, "gamma": "1.0:1.0:1.0", "desc": "Maximum luminance for sunlit rooms"},
            "night": {"brightness": 20, "gamma": "0.8:0.7:0.5", "desc": "Ultra-low luminance with blue-light reduction"}
        }
        if profile not in profiles:
            return {"success": False, "error": f"Unknown profile '{profile}'. Options: {list(profiles.keys())}"}

        cfg = profiles[profile]
        # 1. Adjust brightness
        self.change_brightness(action="up" if cfg["brightness"] > 50 else "down", amount=cfg["brightness"])

        # 2. Adjust gamma on Linux if xrandr present
        if self.os_type == "linux" and shutil.which("xrandr"):
            try:
                mon_cmd = "xrandr | grep ' connected' | cut -f1 -d' '"
                mon = subprocess.run(mon_cmd, shell=True, capture_output=True, text=True).stdout.strip().split()[0]
                subprocess.run(f"xrandr --output {mon} --gamma {cfg['gamma']}", shell=True)
            except Exception:
                pass

        return {"success": True, "profile": profile, "description": cfg["desc"], "brightness": cfg["brightness"]}

    # -------------------------------------------------------------
    # 14. Fan Speed Manual Override (MacBook Pro applesmc / hwmon)
    # -------------------------------------------------------------
    def get_fan_speed(self) -> dict:
        if self.os_type == "linux":
            # Check Apple SMC on MacBook Pro
            smc_path = Path("/sys/devices/platform/applesmc.768")
            if smc_path.exists():
                fans = []
                for f in sorted(smc_path.glob("fan*_input")):
                    rpm = f.read_text().strip()
                    fans.append(f"{f.name}: {rpm} RPM")
                return {"success": True, "fans": fans}
        return {"success": True, "message": "Fan speed managed automatically by BIOS / SMC."}

    def set_fan_speed(self, mode: str = "max") -> dict:
        mode = mode.lower().strip()
        if self.os_type == "linux":
            smc_path = Path("/sys/devices/platform/applesmc.768")
            if smc_path.exists():
                manual_file = smc_path / "fan1_manual"
                output_file = smc_path / "fan1_output"
                max_file = smc_path / "fan1_max"
                if mode == "auto":
                    subprocess.run(f"echo 0 | sudo -n tee {manual_file}", shell=True)
                    return {"success": True, "message": "Fan mode restored to auto SMC control."}
                elif mode == "max":
                    max_rpm = max_file.read_text().strip() if max_file.exists() else "6000"
                    cmd = f"echo 1 | sudo -n tee {manual_file} && echo {max_rpm} | sudo -n tee {output_file}"
                    subprocess.run(cmd, shell=True)
                    return {"success": True, "message": f"MacBook cooling fan locked to MAX ({max_rpm} RPM) to prevent thermal throttle."}
                elif mode == "quiet":
                    cmd = f"echo 1 | sudo -n tee {manual_file} && echo 2500 | sudo -n tee {output_file}"
                    subprocess.run(cmd, shell=True)
                    return {"success": True, "message": "Fan set to quiet baseline (2500 RPM)."}

        return {"success": False, "message": "Fan override requires Linux with AppleSMC or hwmon fancontrol."}

    # -------------------------------------------------------------
    # 15. Audio Sink / Route Switcher
    # -------------------------------------------------------------
    def list_audio_sinks(self) -> list:
        sinks = []
        if self.os_type == "linux" and shutil.which("pactl"):
            try:
                res = subprocess.run(["pactl", "list", "short", "sinks"], capture_output=True, text=True)
                for line in res.stdout.strip().splitlines():
                    parts = line.split()
                    if len(parts) >= 2:
                        sinks.append({"id": parts[0], "name": parts[1], "module": parts[2] if len(parts) > 2 else ""})
            except Exception:
                pass
        elif self.os_type == "win32":
            sinks = [{"id": "0", "name": "Default Windows Audio Endpoint"}]
        return sinks

    def set_audio_sink(self, sink_target: str) -> dict:
        if self.os_type == "linux" and shutil.which("pactl"):
            try:
                # Set default sink
                res = subprocess.run(f"pactl set-default-sink '{sink_target}'", shell=True, capture_output=True, text=True)
                if res.returncode == 0:
                    # Move currently playing streams to new sink
                    inputs = subprocess.run("pactl list short sink-inputs", shell=True, capture_output=True, text=True).stdout.strip().splitlines()
                    for inp in inputs:
                        if inp:
                            in_id = inp.split()[0]
                            subprocess.run(f"pactl move-sink-input {in_id} '{sink_target}'", shell=True)
                    return {"success": True, "message": f"Audio successfully rerouted to sink '{sink_target}'."}
                return {"success": False, "error": res.stderr.strip()}
            except Exception as e:
                return {"success": False, "error": str(e)}
        return {"success": False, "message": "Audio route switching is designed for PulseAudio/PipeWire on Linux."}

    # =========================================================================
    # Android / Termux — Hardware & Battery Telemetry
    # =========================================================================

    def get_battery_status(self) -> dict:
        """
        Returns battery info as a unified dict across all platforms.
        On Android (Termux), queries `termux-battery-status` for precise data
        including temperature, health, and plug type.
        On Linux/Windows, falls back to psutil.sensors_battery().
        """
        # --- Android path ---
        if self.is_android:
            result = _termux_cmd(["termux-battery-status"])
            if result["success"] and result["json"]:
                d = result["json"]
                return {
                    "percent": d.get("percentage", None),
                    "plugged_in": d.get("status", "").upper() == "CHARGING",
                    "status": d.get("status", "UNKNOWN"),
                    "health": d.get("health", "UNKNOWN"),
                    "temperature_c": d.get("temperature", None),
                    "plug_type": d.get("plugged", "UNPLUGGED"),
                    "source": "termux-battery-status",
                }
            # Termux API unavailable — still return a minimal dict
            return {"percent": None, "plugged_in": None, "status": "UNAVAILABLE",
                    "health": "UNKNOWN", "temperature_c": None, "source": "unavailable"}

        # --- Desktop path ---
        try:
            b = psutil.sensors_battery()
            if b:
                return {
                    "percent": b.percent,
                    "plugged_in": b.power_plugged,
                    "status": "CHARGING" if b.power_plugged else "DISCHARGING",
                    "health": "UNKNOWN",
                    "temperature_c": None,
                    "source": "psutil",
                }
        except Exception:
            pass
        return {"percent": None, "plugged_in": None, "status": "UNAVAILABLE",
                "health": "UNKNOWN", "temperature_c": None, "source": "unavailable"}

    def vibrate(self, duration_ms: int = 300) -> dict:
        """
        Triggers haptic vibration.
        Android: termux-vibrate  |  Windows/Linux: not supported (silent).
        """
        if self.is_android:
            result = _termux_cmd(["termux-vibrate", "-d", str(duration_ms)])
            return {"success": result["success"], "platform": "android",
                    "duration_ms": duration_ms}
        return {"success": False, "platform": self.os_type,
                "message": "Vibration not supported on this platform."}

    def get_android_volume(self) -> dict:
        """
        Reads current Android media volume via termux-volume (if available).
        """
        if self.is_android:
            result = _termux_cmd(["termux-volume"])
            if result["success"] and result["json"]:
                return {"success": True, "volumes": result["json"]}
            return {"success": False, "message": "termux-volume unavailable"}
        return {"success": False, "message": "Android-only feature."}

    def set_android_volume(self, stream: str = "music", volume: int = 70) -> dict:
        """
        Sets Android audio stream volume via termux-volume.
        stream: music | call | ring | alarm | notification | system
        volume: 0-100 (clamped to Android's 0–15 scale internally).
        """
        if self.is_android:
            result = _termux_cmd(["termux-volume", stream, str(volume)])
            return {"success": result["success"], "stream": stream, "volume": volume}
        return {"success": False, "message": "Android-only feature."}

    def get_android_wifi_info(self) -> dict:
        """Returns Wi-Fi connection info via termux-wifi-connectioninfo."""
        if self.is_android:
            result = _termux_cmd(["termux-wifi-connectioninfo"])
            if result["success"] and result["json"]:
                return {"success": True, "wifi": result["json"]}
        return {"success": False, "message": "Not on Android or termux-wifi-connectioninfo unavailable."}

    def android_tts(self, text: str, rate: float = 1.0) -> dict:
        """
        Speaks text via the Android native TTS engine through Termux:API.
        Falls back gracefully on non-Android platforms.
        """
        if self.is_android and shutil.which("termux-tts-speak"):
            result = _termux_cmd(["termux-tts-speak", "-r", str(rate), text], timeout=30)
            return {"success": result["success"], "platform": "android"}
        return {"success": False, "message": "termux-tts-speak not available."}

    def get_cpu_temperature_android(self) -> float | None:
        """
        Reads Snapdragon 888 thermal zones directly from sysfs.
        Checks /sys/class/thermal/thermal_zone*/temp (Android kernel sysfs).
        Returns the highest reading in Celsius, or None if unreadable.
        """
        if not self.is_android:
            return None
        try:
            thermal_root = Path("/sys/class/thermal")
            temps = []
            for zone in thermal_root.glob("thermal_zone*/temp"):
                try:
                    raw = zone.read_text().strip()
                    if raw.isdigit():
                        c = int(raw) / 1000.0
                        if 10 < c < 125:
                            temps.append(c)
                except Exception:
                    continue
            return max(temps) if temps else None
        except Exception:
            return None

    def apply_snapdragon_thermal_safeguard(self) -> dict:
        """
        Applies conservative CPU governor and charge-current limits on
        Snapdragon 888 to avoid thermal throttle during 24/7 operation.
        Returns a status dict.
        """
        actions = []
        if not self.is_android:
            return {"success": False, "message": "Android-only safeguard."}

        # 1. Switch CPU governor to schedutil (Snapdragon's preferred power-aware gov)
        for cpu in Path("/sys/devices/system/cpu").glob("cpu[0-9]*/cpufreq/scaling_governor"):
            try:
                cpu.write_text("schedutil")
                actions.append(f"Governor → schedutil ({cpu.parent.parent.name})")
            except Exception:
                # Requires root; silently skip
                pass

        # 2. Cap charge current
        charge_node = Path("/sys/class/power_supply/battery/constant_charge_current_max")
        if charge_node.exists() and os.access(charge_node, os.W_OK):
            try:
                charge_node.write_text("2500000")
                actions.append("Charge current capped at 2500 mA")
            except Exception:
                actions.append("Charge current cap: permission denied (needs root)")
        else:
            actions.append("Charge current cap: sysfs node not writable")

        return {
            "success": True,
            "actions": actions,
            "note": "Some governor changes require root; non-root actions applied."
        }

    # =========================================================================
    # Cross-platform get_system_health — enhanced with Android path
    # =========================================================================

    def get_system_health(self) -> dict:
        """
        Gathers comprehensive CPU, RAM, Disk, Process, and Battery diagnostics.
        On Android, enriches battery data via termux-battery-status and reads
        Snapdragon thermal zones directly from sysfs.
        """
        cpu_pct = psutil.cpu_percent(interval=0.2)
        ram = psutil.virtual_memory()

        # Disk — Android Termux home
        disk_path = str(Path.home()) if self.is_android else "/"
        try:
            disk = psutil.disk_usage(disk_path)
            disk_free_gb = round(disk.free / (1024**3), 1)
        except Exception:
            disk_free_gb = -1.0

        # Battery — unified via get_battery_status()
        battery = self.get_battery_status()

        # Top 3 CPU processes
        top_procs = []
        try:
            for p in sorted(psutil.process_iter(['name', 'cpu_percent', 'memory_percent']),
                            key=lambda p: p.info.get('cpu_percent', 0) or 0,
                            reverse=True)[:4]:
                name = p.info.get('name')
                cpu = p.info.get('cpu_percent')
                mem = p.info.get('memory_percent')
                if name and cpu is not None and mem is not None:
                    top_procs.append(f"{name} (CPU: {cpu:.1f}%, RAM: {mem:.1f}%)")
        except Exception:
            pass

        swap = psutil.swap_memory()

        # Uptime
        uptime_sec = int(time.time() - psutil.boot_time())
        hours = uptime_sec // 3600
        mins = (uptime_sec % 3600) // 60
        uptime_str = f"{hours}h {mins}m"

        # CPU Temperature — Android sysfs first, then heartbeat fallback
        cpu_temp = None
        if self.is_android:
            cpu_temp = self.get_cpu_temperature_android()
        if cpu_temp is None:
            try:
                from engine.heartbeat import heartbeat_engine
                cpu_temp = heartbeat_engine.get_cpu_temperature()
            except Exception:
                pass

        # Network ping
        ping_ok = True
        try:
            param = "-n 1" if self.os_type == "win32" else "-c 1"
            res = subprocess.run(f"ping {param} 8.8.8.8", shell=True, capture_output=True, timeout=2)
            ping_ok = (res.returncode == 0)
        except Exception:
            ping_ok = False

        return {
            "cpu_percent": cpu_pct,
            "cpu_temp": cpu_temp,
            "ram_total_gb": round(ram.total / (1024**3), 1),
            "ram_used_gb": round(ram.used / (1024**3), 1),
            "ram_percent": ram.percent,
            "swap_used_mb": round(swap.used / (1024**2), 1),
            "swap_total_mb": round(swap.total / (1024**2), 1),
            "swap_percent": swap.percent,
            "disk_free_gb": disk_free_gb,
            "uptime": uptime_str,
            "battery": battery,
            "top_processes": top_procs,
            "internet_connected": ping_ok,
            "platform": "android" if self.is_android else self.os_type,
        }

    def troubleshoot(self) -> str:
        """
        Analyzes system metrics and returns an actionable diagnosis.
        """
        health = self.get_system_health()
        issues = []
        advice = []

        if health["cpu_percent"] > 85:
            issues.append(f"High CPU load: {health['cpu_percent']}%")
            if health["top_processes"]:
                advice.append(f"Heavy processes: {', '.join(health['top_processes'][:2])}")

        if health["ram_percent"] > 85:
            issues.append(f"RAM memory bottleneck: {health['ram_percent']}% used ({health['ram_used_gb']}GB / {health['ram_total_gb']}GB)")
            advice.append("Consider closing background tabs or heavy apps.")

        if not health["internet_connected"]:
            issues.append("No internet connection detected (ping to 8.8.8.8 failed).")
            advice.append("Check your Wi-Fi or router settings.")

        if health["disk_free_gb"] != -1.0 and health["disk_free_gb"] < 5.0:
            issues.append(f"Low disk storage: only {health['disk_free_gb']}GB remaining.")
            advice.append("Run 'organize files' or clear temporary files.")

        batt = health.get("battery", {})
        if batt and batt.get("temperature_c") and batt["temperature_c"] > 42:
            issues.append(f"Battery temperature high: {batt['temperature_c']}°C (Snapdragon 888 comfort limit: 42°C)")
            advice.append("Let device cool down. Avoid charging under heavy load.")

        if not issues:
            return (
                f"Your device is running smoothly! CPU is at {health['cpu_percent']}%, "
                f"RAM usage is {health['ram_percent']}% ({health['ram_used_gb']}GB used), "
                f"and internet connectivity is healthy."
            )
        else:
            return f"Found {len(issues)} issues: " + " | ".join(issues) + ". " + " ".join(advice)


system_controller = SystemController()

