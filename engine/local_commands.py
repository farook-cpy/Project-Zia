import re
import os
import sys
import time
import shutil
import subprocess
import webbrowser
from pathlib import Path
from engine.system_control import system_controller
from engine.iot_bridge import iot_bridge
from engine.prayer_times import prayer_engine
from engine.alarm_manager import alarm_manager
from engine.lifedesk_bridge import lifedesk_bridge

class LocalCommandRouter:
    # Pre-compiled regular expressions for sub-millisecond matching (<0.1ms)
    RE_SKIN = re.compile(r"^(?:switch\s+skin|change\s+skin|set\s+skin|ambient\s+style|set\s+style)\s*(.*)", re.IGNORECASE)
    RE_READ_FILE = re.compile(r"^(?:read\s+file|inspect\s+file|open\s+file\s+content)\s+(.+)", re.IGNORECASE)
    RE_CMD = re.compile(r"^(?:run|execute|exec|terminal|bash|powershell|cmd)\s+(?:command\s+|in\s+terminal\s+)?(.+)", re.IGNORECASE)
    RE_ADMIN = re.compile(r"^(?:run\s+as\s+admin|run\s+admin|sudo|elevated)\s+(?:command\s+)?(.+)", re.IGNORECASE)
    RE_NOTEPAD_TYPE = re.compile(r"(?:open\s+(?:notepad|text\s*editor)\s+(?:and\s+)?(?:type|write)\s+)(.+)", re.IGNORECASE)
    RE_OPEN_SHORTCUT = re.compile(r"^(?:open|launch|start|play|go\s+to)\s+([a-z0-9_\-\.]+)(.*)", re.IGNORECASE)

    def __init__(self):
        self.os_type = sys.platform

    def match_and_execute(self, user_text: str) -> dict | None:
        """
        Evaluates user text. If it matches a local OS/system task, executes it
        immediately in Python without calling the LLM, saving 100% of tokens.
        Returns a dict response or None if it should be delegated to the LLM.
        """
        text = user_text.strip().lower()

        # 0. Natural Language Alarm & Countdown Timer Parser (0 LLM Tokens)
        alarm_result = alarm_manager.parse_natural_language(user_text)
        if alarm_result:
            return {
                "text": alarm_result.get("message", "Alarm / timer scheduled successfully."),
                "mood": "F4",
                "actions": [alarm_result]
            }

        # 0.05 LifeDesk Productivity & Personal Finance Bridge (0 LLM Tokens)
        lifedesk_result = lifedesk_bridge.parse_natural_language(user_text)
        if lifedesk_result:
            res_data = lifedesk_result.get("result", {})
            reply_msg = res_data.get("message")
            if not reply_msg:
                if lifedesk_result.get("type") == "habit_streaks_query":
                    habits_list = res_data.get("habits", [])
                    reply_msg = "LifeDesk Habit Streaks:\n" + "\n".join([f"• {h['habit']}: {h['streak']} days streak ({h['total_days']} days total)" for h in habits_list])
                elif lifedesk_result.get("type") == "monthly_summary":
                    reply_msg = f"LifeDesk Monthly Summary: Spent Rs. {res_data.get('total_expenses', 0):.2f}, Income Rs. {res_data.get('total_income', 0):.2f}, Net savings Rs. {res_data.get('net_savings', 0):.2f}"
                else:
                    reply_msg = "LifeDesk database updated successfully."
            return {
                "text": reply_msg,
                "mood": "F4" if "streak" in reply_msg.lower() else "F1",
                "actions": [lifedesk_result]
            }

        # 0.08 Dual-Mode Avatar Visualization Switcher (Minimal vs Live2D)
        if any(w in text for w in ["load avatar", "start avatar", "show avatar", "live2d mode", "switch to live2d"]):
            return {
                "text": "Loading avatar.",
                "mood": "F4",
                "actions": [{"type": "switch_mode", "mode": "live2d"}]
            }

        # 0.085 Anime PNG Sprite Avatar Switcher (Active on minimize or on-demand)
        if any(w in text for w in ["sprite mode", "anime mode", "load sprite", "show sprite", "switch to sprite", "anime avatar", "desktop sprite"]):
            return {
                "text": "Anime sprite companion active.",
                "mood": "F4",
                "actions": [{"type": "switch_mode", "mode": "sprite"}]
            }

        if any(w in text for w in ["stop avatar", "hide avatar", "unload avatar", "minimal mode", "switch to minimal", "lightweight mode"]):
            return {
                "text": "Minimal mode active.",
                "mood": "F1",
                "actions": [{"type": "switch_mode", "mode": "minimal"}]
            }

        # 0.09 Wireless ADB Intent Bridges (Projector & Tablet) & IoT Relays
        if any(w in text for w in ["turn on the desk light", "turn on desk light", "desk light on"]):
            res = iot_bridge.control_relay("desk_lamp", "on")
            return {
                "text": "Desk light is on.",
                "mood": "F4",
                "actions": [res]
            }

        if any(w in text for w in ["turn off the desk light", "turn off desk light", "desk light off"]):
            res = iot_bridge.control_relay("desk_lamp", "off")
            return {
                "text": "Desk light is off.",
                "mood": "F11",
                "actions": [res]
            }

        if any(w in text for w in ["launch projector", "stream miruro", "play on projector", "projector stream", "black clover"]):
            url = "https://miruro.tv"
            res = iot_bridge.launch_projector_stream(url=url)
            return {
                "text": "Playing on projector.",
                "mood": "F4",
                "actions": [res]
            }

        if any(w in text for w in ["call on tablet", "botim call", "launch botim", "open botim", "botim"]):
            contact = "Dad" if "dad" in text else "Family"
            res = iot_bridge.trigger_botim_call(contact_name=contact)
            return {
                "text": f"Calling {contact} on your tablet.",
                "mood": "F1",
                "actions": [res]
            }

        # 0.092 Family Notification & OTP Sink (Local Queue)
        if any(w in text for w in ["what is the otp", "check otp", "latest otp", "any otp", "show otp", "get otp"]):
            from engine.family_bridge import family_bridge
            latest = family_bridge.get_latest_otp()
            if latest:
                otp_code = latest.get("otp_code")
                sender = latest.get("sender") or latest.get("device")
                age = latest.get("age_human", "")
                return {
                    "text": f"Latest OTP is {otp_code} from {sender} ({age}).",
                    "mood": "F4",
                    "actions": [latest]
                }
            else:
                return {
                    "text": "No recent OTP found in the family queue.",
                    "mood": "F1",
                    "actions": []
                }

        if any(w in text for w in ["family notifications", "check messages", "check family", "family queue"]):
            from engine.family_bridge import family_bridge
            notifs = family_bridge.list_all(limit=3)
            if notifs:
                summary = "; ".join([f"{n.get('sender', 'Unknown')}: {n.get('message', '')[:40]}" for n in notifs])
                return {
                    "text": f"Recent family notifications: {summary}",
                    "mood": "F1",
                    "actions": notifs
                }
            else:
                return {
                    "text": "No family notifications in the queue.",
                    "mood": "F1",
                    "actions": []
                }

        # 0.095 Agent-Browser Token-Efficient Automations
        if text.startswith("open url ") or text.startswith("browse "):
            target_url = text.split(" ", 2)[-1].strip()
            from engine.browser_agent import browser_agent
            res = browser_agent.open_url(target_url)
            return {
                "text": f"Opened {target_url} via agent-browser.",
                "mood": "F1",
                "actions": [res]
            }

        if "browser snapshot" in text or "a11y snapshot" in text:
            from engine.browser_agent import browser_agent
            snap = browser_agent.get_accessibility_snapshot()
            token_count = snap.get("estimated_tokens", 20)
            return {
                "text": f"Accessibility snapshot captured ({token_count} tokens).",
                "mood": "F1",
                "actions": [snap]
            }

        if any(w in text for w in ["train schedule", "trains to coimbatore", "trains to palakkad"]):
            from engine.browser_agent import browser_agent
            schedule = browser_agent.check_live_schedule("Palakkad", "Coimbatore")
            first_train = schedule.get("schedule", [{}])[0].get("train", "Train")
            return {
                "text": f"Found train schedule from Palakkad to Coimbatore. Next is {first_train}.",
                "mood": "F4",
                "actions": [schedule]
            }

        if any(w in text for w in ["turn on fan", "fan on", "start fan"]):
            import asyncio
            res = asyncio.run(iot_bridge.control_fan("on"))
            return {
                "text": "Cooling fan is on.",
                "mood": "F4",
                "actions": [res]
            }

        if any(w in text for w in ["turn off fan", "fan off", "stop fan"]):
            import asyncio
            res = asyncio.run(iot_bridge.control_fan("off"))
            return {
                "text": "Cooling fan is off.",
                "mood": "F11",
                "actions": [res]
            }

        # 0.1 Palakkad Islamic Prayer Times & Habit Check-in Response
        if prayer_engine.last_checkin_prayer and any(text.startswith(w) for w in ["yes", "i prayed", "prayed", "done", "alhamdulillah", "i did pray", "completed", "already prayed"]):
            res = prayer_engine.record_prayer_status(prayer_engine.last_checkin_prayer, status="completed")
            return {
                "text": f"Alhamdulillah! I've noted down that you completed {res['prayer']} prayer in Palakkad.",
                "mood": "F1",
                "actions": [res]
            }

        if any(w in text for w in ["prayer times", "prayer time", "namaz times", "salat times", "palakkad prayer", "next prayer", "subhi time", "fajr time", "asr time", "maghrib time", "isha time", "dhuhr time"]):
            next_p = prayer_engine.get_next_prayer()
            sched = prayer_engine.format_schedule_table()
            return {
                "text": f"Here are today's prayer times for Palakkad, Kerala:\n\n{sched}",
                "mood": "F1",
                "actions": [{"type": "prayer_schedule", "next": next_p}]
            }

        # 1. IoT Home Automation (Tasmota / WLED / ESP8266 Zero-CPU Relay Bridge)
        if any(w in text for w in ["turn on light", "lights on", "switch on light"]):
            import asyncio
            res = asyncio.run(iot_bridge.send_command("on"))
            return {
                "text": "Room lights are on." if res.get("success") else "Dispatched light command.",
                "mood": "F4",
                "actions": [res]
            }

        if any(w in text for w in ["turn off light", "lights off", "switch off light"]):
            import asyncio
            res = asyncio.run(iot_bridge.send_command("off"))
            return {
                "text": "Room lights are off." if res.get("success") else "Dispatched light command.",
                "mood": "F11",
                "actions": [res]
            }

        if any(w in text for w in ["toggle light", "switch light", "lights toggle"]):
            import asyncio
            res = asyncio.run(iot_bridge.send_command("toggle"))
            return {
                "text": "Toggled your room lights." if res.get("success") else f"Dispatched toggle command to {res.get('ip')}.",
                "mood": "F1",
                "actions": [res]
            }

        # 2. Living Asset Ambient Style Swapping
        skin_match = self.RE_SKIN.search(text)
        if skin_match or any(w in text for w in ["night skin", "day skin", "cyberpunk skin", "neon skin"]):
            from engine.texture_mod import living_assets
            style = "night" if "night" in text else ("day" if "day" in text else ("cyber" if ("cyber" in text or "neon" in text) else "night"))
            res = living_assets.apply_style(style)
            return {
                "text": f"Repainted my outfit to {style} ambient style!",
                "mood": "F4",
                "actions": [{"type": "reload_texture", "url": res.get("texture_url")}]
            }

        # 3. Structured MCP Gateway Direct File / Code Crawling (Zero-Pixel OCR)
        read_file_match = self.RE_READ_FILE.search(user_text)
        if read_file_match:
            from engine.mcp_gateway import mcp_gateway
            fpath = read_file_match.group(1).strip()
            res = mcp_gateway.read_file(fpath)
            if "error" in res:
                return {"text": f"MCP Gateway Notice: {res['error']}", "mood": "F3", "actions": []}
            return {
                "text": f"Successfully parsed {res['lines_returned']} lines from {fpath} with 100% precision via MCP:\n\n{res['content'][:600]}...",
                "mood": "F1",
                "actions": []
            }

        # 4. Volume Controls
        if any(w in text for w in ["volume up", "increase volume", "turn up volume", "louder", "boost volume"]):
            res = system_controller.change_volume("up", 5)
            return {"text": "Turned the volume up for you.", "mood": "F4", "actions": [res]}

        if any(w in text for w in ["volume down", "decrease volume", "lower volume", "quieter"]):
            res = system_controller.change_volume("down", 5)
            return {"text": "Lowered the volume for you.", "mood": "F1", "actions": [res]}

        if any(w in text for w in ["mute volume", "mute sound", "unmute volume", "mute audio"]):
            res = system_controller.change_volume("mute", 1)
            return {"text": "Toggled mute on your audio.", "mood": "F1", "actions": [res]}

        # 2. Brightness Controls
        if any(w in text for w in ["brightness up", "increase brightness", "brighter", "more brightness"]):
            res = system_controller.change_brightness("up", 15)
            return {"text": "Increased your screen brightness.", "mood": "F4", "actions": [res]}

        if any(w in text for w in ["brightness down", "decrease brightness", "dimmer", "lower brightness"]):
            res = system_controller.change_brightness("down", 15)
            return {"text": "Dimmed your screen brightness.", "mood": "F1", "actions": [res]}

        # 3. Session Screen Lock & Unlock
        if any(w in text for w in ["lock screen", "lock device", "lock session", "lock pc", "lock my pc", "lock computer"]):
            res = system_controller.lock_session()
            return {"text": res.get("message", "Locked your session."), "mood": "F11", "actions": [res]}

        if any(w in text for w in ["unlock screen", "unlock device", "unlock session", "unlock pc", "unlock my pc", "wake screen", "wake display"]):
            res = system_controller.unlock_session()
            return {"text": res.get("message", "Awakened display and unlocked session."), "mood": "F4", "actions": [res]}

        # 4. Display Compositor Toggle (XFCE GPU Performance Reclaim)
        if any(w in text for w in ["toggle compositor", "compositor on", "compositor off", "disable compositing", "enable compositing"]):
            enable = True if "on" in text or "enable" in text else (False if "off" in text or "disable" in text else None)
            res = system_controller.toggle_compositor(enable)
            return {"text": res.get("message", "Toggled display compositor."), "mood": "F1", "actions": [res]}

        # 5. Passwordless Sudo Automation Configuration
        if any(w in text for w in ["setup sudo", "setup passwordless sudo", "configure sudo", "enable passwordless sudo"]):
            res = system_controller.setup_passwordless_sudo()
            return {"text": res.get("message", ""), "mood": "F4" if res.get("success") else "F3", "actions": [res]}

        # 6. System Diagnostics & Troubleshooting
        if any(w in text for w in ["troubleshoot", "check my pc", "system health", "diagnostics", "check device", "device status", "check ram", "check cpu"]):
            diagnosis = system_controller.troubleshoot()
            return {"text": diagnosis, "mood": "F8", "actions": []}

        # 7. Cooling Fan Manual Override (applesmc / hwmon)
        if any(w in text for w in ["fan max", "fan 100", "max fans", "full fan"]):
            res = system_controller.set_fan_speed("max")
            return {"text": res.get("message", "Set fans to maximum speed."), "mood": "F1", "actions": [res]}

        if any(w in text for w in ["fan quiet", "fan low", "fan min", "silent fan"]):
            res = system_controller.set_fan_speed("quiet")
            return {"text": res.get("message", "Set fans to quiet profile."), "mood": "F1", "actions": [res]}

        if any(w in text for w in ["fan auto", "fan default", "auto fan", "fan reset"]):
            res = system_controller.set_fan_speed("auto")
            return {"text": res.get("message", "Restored automatic fan control."), "mood": "F4", "actions": [res]}

        if any(w in text for w in ["fan status", "fan speed", "check fan"]):
            res = system_controller.get_fan_speed()
            return {"text": f"Cooling fan status: {res.get('fans') or res.get('message')}", "mood": "F1", "actions": [res]}

        # 8. Display Calibration Profiles
        if any(w in text for w in ["reading profile", "reading mode", "paper mode", "warm screen"]):
            res = system_controller.apply_display_profile("reading")
            return {"text": f"Applied reading profile: {res.get('description')} ({res.get('brightness')}% brightness).", "mood": "F4", "actions": [res]}

        if any(w in text for w in ["movie profile", "movie mode", "cinema mode"]):
            res = system_controller.apply_display_profile("movie")
            return {"text": f"Applied movie profile: {res.get('description')} ({res.get('brightness')}% brightness).", "mood": "F11", "actions": [res]}

        if any(w in text for w in ["night profile", "night mode", "dark screen", "dim screen"]):
            res = system_controller.apply_display_profile("night")
            return {"text": f"Applied night profile: {res.get('description')} ({res.get('brightness')}% brightness).", "mood": "F11", "actions": [res]}

        if any(w in text for w in ["outdoor profile", "outdoor mode", "sunlight mode"]):
            res = system_controller.apply_display_profile("outdoor")
            return {"text": f"Applied outdoor profile: {res.get('description')} ({res.get('brightness')}% brightness).", "mood": "F2", "actions": [res]}

        # 9. CPU Governor Frequency Switching
        if any(w in text for w in ["powersave mode", "battery saver", "cpu powersave", "low power mode"]):
            res = system_controller.set_cpu_governor("powersave")
            return {"text": res.get("message", "Switched CPU governor to powersave."), "mood": "F1", "actions": [res]}

        if any(w in text for w in ["performance mode", "cpu performance", "high performance mode", "boost cpu"]):
            res = system_controller.set_cpu_governor("performance")
            return {"text": res.get("message", "Switched CPU governor to performance."), "mood": "F1", "actions": [res]}

        # 10. Local Webcam Vision Senses
        if any(w in text for w in ["camera status", "cam status", "webcam status", "are you watching"]):
            from engine.vision_senses import vision_senses
            st = vision_senses.get_current_state()
            hw = "connected" if st["camera_available"] else "not detected"
            return {
                "text": f"Vision senses status: currently detecting user as '{st['state'].upper()}' (confidence: {int(st['confidence']*100)}%, camera {hw}).",
                "mood": "F1",
                "actions": [st]
            }

        # 4. Terminal Command Execution (including Administrator / Sudo)
        cmd_match = self.RE_CMD.search(user_text)
        admin_match = self.RE_ADMIN.search(user_text)

        if admin_match:
            raw_cmd = admin_match.group(1).strip()
            res = system_controller.execute_terminal(raw_cmd, run_as_admin=True)
            return {
                "text": f"Executed administrator command: {raw_cmd}. {res['output']}",
                "mood": "F1",
                "actions": [res]
            }

        if cmd_match and not any(text.startswith(k) for k in ["open", "play", "go to"]):
            raw_cmd = cmd_match.group(1).strip()
            res = system_controller.execute_terminal(raw_cmd, run_as_admin=False)
            return {
                "text": f"Terminal output: {res['output']}",
                "mood": "F1" if res.get("success") else "F3",
                "actions": [res]
            }

        # 5. Open Notepad and type
        notepad_type_match = self.RE_NOTEPAD_TYPE.search(user_text)
        if notepad_type_match:
            content_to_type = notepad_type_match.group(1).strip()
            return self.open_notepad_and_type(content_to_type)

        if text in ["open notepad", "launch notepad", "open text editor", "start notepad"]:
            return self.open_notepad_and_type(None)

        # 2. File Organization
        if any(kw in text for kw in ["organize files", "organise files", "clean downloads", "sort files", "organize downloads", "clean desktop", "organize desktop"]):
            target = "downloads" if "download" in text else ("desktop" if "desktop" in text else "downloads")
            return self.organize_directory(target)

        # 3. Web & Media Shortcuts
        url_shortcuts = {
            "yt": ("https://www.youtube.com", "YouTube"),
            "youtube": ("https://www.youtube.com", "YouTube"),
            "ig": ("https://www.instagram.com", "Instagram"),
            "instagram": ("https://www.instagram.com", "Instagram"),
            "spotify": ("https://open.spotify.com", "Spotify"),
            "github": ("https://github.com", "GitHub"),
            "reddit": ("https://reddit.com", "Reddit"),
            "twitter": ("https://x.com", "X"),
            "x": ("https://x.com", "X"),
            "netflix": ("https://www.netflix.com", "Netflix"),
            "twitch": ("https://www.twitch.tv", "Twitch"),
            "google": ("https://www.google.com", "Google")
        }

        # Check 'open <shortcut>'
        open_match = self.RE_OPEN_SHORTCUT.match(text)
        if open_match:
            app_or_site = open_match.group(1).strip()
            rest = open_match.group(2).strip()

            if app_or_site in url_shortcuts:
                url, name = url_shortcuts[app_or_site]
                webbrowser.open(url)
                return {
                    "text": f"Opening {name} for you right now!",
                    "mood": "F4",
                    "actions": [{"type": "launch", "target": url}]
                }

            # Search query: "search google for <query>" or "google <query>"
            if app_or_site in ["google", "search"]:
                query = rest.replace("for ", "").strip()
                if query:
                    search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
                    webbrowser.open(search_url)
                    return {
                        "text": f"Searching Google for '{query}'!",
                        "mood": "F8",
                        "actions": [{"type": "launch", "target": search_url}]
                    }

            # 4. Open Any Application in System
            return self.launch_system_app(app_or_site)

        return None

    def launch_system_app(self, app_name: str) -> dict:
        """
        Cross-platform app launcher supporting Linux Mint, macOS, and Windows.
        """
        app_name = app_name.strip()

        # Known OS mapping
        app_aliases = {
            "calc": "calc.exe" if self.os_type == "win32" else "gnome-calculator",
            "calculator": "calc.exe" if self.os_type == "win32" else "gnome-calculator",
            "terminal": "wt.exe" if shutil.which("wt.exe") else ("cmd.exe" if self.os_type == "win32" else "x-terminal-emulator"),
            "cmd": "cmd.exe",
            "powershell": "powershell.exe",
            "bash": "bash",
            "explorer": "explorer.exe" if self.os_type == "win32" else "nemo",
            "files": "explorer.exe" if self.os_type == "win32" else "nemo",
            "file manager": "explorer.exe" if self.os_type == "win32" else "nemo",
            "browser": "msedge" if shutil.which("msedge") else "google-chrome",
            "chrome": "google-chrome" if shutil.which("google-chrome") else "chrome",
            "firefox": "firefox",
            "edge": "msedge",
            "code": "code",
            "vscode": "code",
            "vs code": "code"
        }

        target_cmd = app_aliases.get(app_name, app_name)

        try:
            if self.os_type == "linux":
                # Linux Mint / Ubuntu
                if shutil.which(target_cmd):
                    subprocess.Popen([target_cmd])
                else:
                    subprocess.Popen(f"xdg-open {target_cmd}", shell=True)
            elif self.os_type == "darwin":
                # macOS
                subprocess.Popen(f"open -a '{target_cmd}'", shell=True)
            else:
                # Windows
                subprocess.Popen(f"start {target_cmd}", shell=True)

            return {
                "text": f"Launching {app_name} on your system.",
                "mood": "F4",
                "actions": [{"type": "launch", "target": target_cmd}]
            }
        except Exception as e:
            return {
                "text": f"I tried to launch {app_name}, but encountered an error: {e}",
                "mood": "F3",
                "actions": []
            }

    def open_notepad_and_type(self, text_to_type: str | None) -> dict:
        """
        Launches text editor cross-platform and types text.
        """
        try:
            if self.os_type == "win32":
                subprocess.Popen(["notepad.exe"])
            elif self.os_type == "darwin":
                subprocess.Popen(["open", "-a", "TextEdit"])
            else:
                # Linux Mint uses xed or gedit
                editor = "xed" if shutil.which("xed") else ("gedit" if shutil.which("gedit") else "nano")
                subprocess.Popen([editor])

            if text_to_type:
                time.sleep(0.5)
                try:
                    from engine.hands import os_controller
                    os_controller.type_text(text_to_type)
                except Exception as e_write:
                    print(f"[Notepad Type Notice] {e_write}")
                return {
                    "text": f"Opened text editor and typed: '{text_to_type}'",
                    "mood": "F1",
                    "actions": [{"type": "type", "text": text_to_type}]
                }
            else:
                return {
                    "text": "Opened text editor for you.",
                    "mood": "F1",
                    "actions": []
                }
        except Exception as e:
            return {
                "text": f"Could not launch text editor: {e}",
                "mood": "F3",
                "actions": []
            }

    def organize_directory(self, location: str = "downloads") -> dict:
        """
        Cleans and organizes the specified directory into categories.
        """
        user_home = Path.home()
        if location == "desktop":
            target_path = user_home / "Desktop"
        else:
            target_path = user_home / "Downloads"

        if not target_path.exists():
            return {
                "text": f"Could not find the {location} directory to organize.",
                "mood": "F7",
                "actions": []
            }

        file_categories = {
            "Images": [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".psd"],
            "Documents": [".pdf", ".docx", ".doc", ".xlsx", ".pptx", ".txt", ".csv", ".epub"],
            "Videos": [".mp4", ".mkv", ".mov", ".avi", ".webm"],
            "Audio": [".mp3", ".wav", ".flac", ".m4a", ".aac"],
            "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
            "Code": [".py", ".js", ".html", ".css", ".json", ".cpp", ".c", ".rs", ".java"],
            "Installers": [".exe", ".msi", ".deb", ".AppImage", ".dmg"]
        }

        moved_count = 0
        try:
            for item in target_path.iterdir():
                # Ignore directories and hidden files
                if item.is_dir() or item.name.startswith("."):
                    continue

                ext = item.suffix.lower()
                target_category = "Miscellaneous"
                for cat, extensions in file_categories.items():
                    if ext in extensions:
                        target_category = cat
                        break

                category_dir = target_path / target_category
                category_dir.mkdir(exist_ok=True)

                dest_file = category_dir / item.name
                if not dest_file.exists():
                    shutil.move(str(item), str(dest_file))
                    moved_count += 1

            return {
                "text": f"Organized {moved_count} files in your {location.capitalize()} into clean folders!",
                "mood": "F4",
                "actions": []
            }
        except Exception as e:
            return {
                "text": f"Error while organizing files: {e}",
                "mood": "F3",
                "actions": []
            }

local_router = LocalCommandRouter()
