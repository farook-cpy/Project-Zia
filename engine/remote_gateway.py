"""
Project Zia - Remote Telegram Gateway (engine/remote_gateway.py)
Bi-directional Telegram Bot API handler for remote notifications, command processing,
and native voice note (.ogg / .mp3) audio generation via Edge-TTS when away from home.

Zero third-party bot framework bloat; uses standard HTTP requests (< 5MB RAM).
"""

import os
import sys
import time
import json
import asyncio
import threading
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
VOICE_CACHE_DIR = DATA_DIR / "voice_cache"
VOICE_CACHE_DIR.mkdir(parents=True, exist_ok=True)


class TelegramRemoteGateway:
    """Provides secure bi-directional remote Telegram bridging for Project Zia."""

    def __init__(self):
        self.bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
        self.default_chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
        self.voice_name = os.environ.get("TELEGRAM_VOICE", "en-US-AriaNeural")
        self.is_running = False
        self.last_update_id = 0
        self._thread: Optional[threading.Thread] = None

    @property
    def is_configured(self) -> bool:
        return bool(self.bot_token and self.default_chat_id)

    def get_status(self) -> Dict[str, Any]:
        """Returns the active configuration and polling status of the gateway."""
        return {
            "configured": self.is_configured,
            "running": self.is_running,
            "voice_engine": "edge_tts" if EDGE_TTS_AVAILABLE else "none",
            "voice_name": self.voice_name,
            "chat_id_set": bool(self.default_chat_id),
            "bot_token_set": bool(self.bot_token)
        }

    def handle_command(self, cmd_text: str) -> str:
        """Processes a command and returns the reply string (useful for testing & internal routing)."""
        lower = cmd_text.lower().strip()
        if lower == "/prayer":
            from engine.prayer_times import prayer_engine
            next_p = prayer_engine.get_next_prayer()
            schedule = prayer_engine.get_prayer_times()
            return f"Palakkad Prayer Times: Next is {next_p.get('prayer')} in {next_p.get('minutes_remaining')}m. Schedule: {schedule}"
        if lower == "/status":
            import psutil
            vm = psutil.virtual_memory()
            return f"Xperia 1 III Node: CPU {psutil.cpu_percent()}%, RAM {int(vm.used/(1024*1024))}MB, 2 Subagents Capped."
        return f"Processed command: {cmd_text}"

    def _api_url(self, method: str) -> str:
        return f"https://api.telegram.org/bot{self.bot_token}/{method}"

    def send_message(self, text: str, chat_id: Optional[str] = None, parse_mode: str = "Markdown") -> Dict[str, Any]:
        """Sends a text message to the specified or default Telegram chat."""
        target_chat = chat_id or self.default_chat_id
        if not self.bot_token or not target_chat:
            return {"success": False, "error": "Telegram token or chat ID not configured."}

        payload = {
            "chat_id": target_chat,
            "text": text,
            "parse_mode": parse_mode
        }

        try:
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self._api_url("sendMessage"),
                data=req_data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return {"success": data.get("ok", False), "result": data.get("result")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def send_voice_note(self, text: str, chat_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Synthesizes spoken audio using Edge-TTS and dispatches as a native
        Telegram voice note (.mp3/.ogg) directly to the user's phone.
        """
        target_chat = chat_id or self.default_chat_id
        if not self.bot_token or not target_chat:
            return {"success": False, "error": "Telegram token or chat ID not configured."}

        if not EDGE_TTS_AVAILABLE:
            # Fall back to text message
            return self.send_message(text, chat_id=target_chat)

        out_path = VOICE_CACHE_DIR / f"voice_{int(time.time())}.mp3"

        # 1. Generate audio via Edge-TTS
        try:
            async def _synthesize():
                communicate = edge_tts.Communicate(text, self.voice_name)
                await communicate.save(str(out_path))

            asyncio.run(_synthesize())
        except Exception as e:
            return {"success": False, "error": f"Edge-TTS synthesis error: {e}"}

        # 2. Upload voice note to Telegram via multipart POST
        try:
            boundary = f"----WebKitFormBoundary{os.urandom(8).hex()}"
            body_bytes = bytearray()

            # Add chat_id part
            body_bytes.extend(f"--{boundary}\r\n".encode("utf-8"))
            body_bytes.extend(b'Content-Disposition: form-data; name="chat_id"\r\n\r\n')
            body_bytes.extend(f"{target_chat}\r\n".encode("utf-8"))

            # Add caption
            clean_caption = text[:200]
            body_bytes.extend(f"--{boundary}\r\n".encode("utf-8"))
            body_bytes.extend(b'Content-Disposition: form-data; name="caption"\r\n\r\n')
            body_bytes.extend(f"{clean_caption}\r\n".encode("utf-8"))

            # Add voice file part
            audio_bytes = out_path.read_bytes()
            body_bytes.extend(f"--{boundary}\r\n".encode("utf-8"))
            body_bytes.extend(b'Content-Disposition: form-data; name="voice"; filename="voice.mp3"\r\n')
            body_bytes.extend(b'Content-Type: audio/mpeg\r\n\r\n')
            body_bytes.extend(audio_bytes)
            body_bytes.extend(b"\r\n")
            body_bytes.extend(f"--{boundary}--\r\n".encode("utf-8"))

            req = urllib.request.Request(
                self._api_url("sendVoice"),
                data=bytes(body_bytes),
                headers={
                    "Content-Type": f"multipart/form-data; boundary={boundary}",
                    "Content-Length": str(len(body_bytes))
                }
            )

            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                # Clean up cached file
                try:
                    out_path.unlink()
                except Exception:
                    pass
                return {"success": data.get("ok", False), "result": data.get("result")}

        except Exception as e:
            return {"success": False, "error": f"Telegram voice dispatch error: {e}"}

    def process_incoming_command(self, cmd_text: str, chat_id: str):
        """Processes a message received from Telegram and returns Zia's response."""
        text = cmd_text.strip()
        lower_text = text.lower()

        # Command shortcuts
        if lower_text in ["/start", "/help"]:
            help_msg = (
                "*Project Zia // Remote Telegram Gateway*\n"
                "You are securely connected to your central Xperia node.\n\n"
                "*Commands:*\n"
                "• `/status` - Xperia system health, battery & subagents\n"
                "• `/prayer` - Palakkad prayer timetable & next prayer\n"
                "• `/alarms` - List active alarms & countdowns\n"
                "• `/habits` - View habit streaks from LifeDesk\n"
                "• `/expenses` - View today's expenses & monthly summary\n"
                "• `/weather` - Live Palakkad ambient climate\n"
                "• `/voice <text>` - Reply with an Edge-TTS voice note\n"
                "• Any natural message - Query Gemini Flash AI brain"
            )
            self.send_message(help_msg, chat_id=chat_id)
            return

        if lower_text.startswith("/voice "):
            prompt_content = text[7:].strip()
            self.send_voice_note(prompt_content, chat_id=chat_id)
            return

        if lower_text == "/status":
            import psutil
            vm = psutil.virtual_memory()
            bat = psutil.sensors_battery()
            bat_pct = f"{bat.percent}%" if bat else "N/A"
            msg = (
                f"*Project Zia Node Status:*\n"
                f"• *Node:* Sony Xperia 1 III (Android Termux)\n"
                f"• *CPU Usage:* {psutil.cpu_percent()}%\n"
                f"• *RAM:* {int(vm.used / (1024*1024))}MB / {int(vm.total / (1024*1024))}MB\n"
                f"• *Battery:* {bat_pct}\n"
                f"• *Subagents:* 2 workers capped"
            )
            self.send_message(msg, chat_id=chat_id)
            return

        if lower_text == "/prayer":
            from engine.prayer_times import prayer_engine
            nxt = prayer_engine.get_next_prayer()
            sched = prayer_engine.get_prayer_times()
            times_str = "\n".join([f"• *{p['name']}:* `{p['time']}`" for p in sched.get("prayers", [])])
            msg = f"*Palakkad Prayer Schedule:*\n{times_str}\n\n*Next:* {nxt.get('name')} in {nxt.get('countdown')}"
            self.send_message(msg, chat_id=chat_id)
            return

        if lower_text == "/alarms":
            from engine.alarm_manager import alarm_manager
            alarms = alarm_manager.list_active()
            if not alarms:
                self.send_message("No active alarms or timers running.", chat_id=chat_id)
            else:
                a_str = "\n".join([f"• *{a['label']}:* in `{a['seconds_remaining'] // 60}m`" for a in alarms])
                self.send_message(f"*Active Alarms:*\n{a_str}", chat_id=chat_id)
            return

        if lower_text in ["/habits", "/streaks"]:
            from engine.lifedesk_bridge import lifedesk_bridge
            streaks = lifedesk_bridge.get_all_habit_streaks()
            h_str = "\n".join([f"• *{h['habit']}:* `{h['streak']} days streak` ({h['total_days']} total)" for h in streaks])
            self.send_message(f"*LifeDesk Habit Streaks:*\n{h_str}", chat_id=chat_id)
            return

        if lower_text in ["/expenses", "/finance"]:
            from engine.lifedesk_bridge import lifedesk_bridge
            today_tot = lifedesk_bridge.get_daily_expense_total()
            summary = lifedesk_bridge.get_monthly_summary()
            msg = (
                f"*LifeDesk Financial Ledger:*\n"
                f"• *Spent Today:* `Rs. {today_tot:.2f}`\n"
                f"• *Month Total:* `Rs. {summary['total_expenses']:.2f}`\n"
                f"• *Net Savings:* `Rs. {summary['net_savings']:.2f}`"
            )
            self.send_message(msg, chat_id=chat_id)
            return

        if lower_text == "/weather":
            from engine.ambient_intelligence import ambient_engine
            w = ambient_engine.get_weather_greeting()
            msg = f"*{w.get('location')}:*\n{w.get('greeting')}\n• Temp: `{w.get('temperature_c')}°C`"
            self.send_message(msg, chat_id=chat_id)
            return

        # Check LifeDesk natural language (e.g. "spent 50 on coffee", "logged 1h coding")
        from engine.lifedesk_bridge import lifedesk_bridge
        ld_res = lifedesk_bridge.parse_natural_language(text)
        if ld_res:
            res_data = ld_res.get("result", {})
            reply_text = res_data.get("message") or f"LifeDesk updated: {ld_res.get('type')}"
            self.send_message(f"*LifeDesk:* {reply_text}", chat_id=chat_id)
            return

        # Check Fast Local Router
        from engine.local_commands import local_router
        local_match = local_router.match_and_execute(text)
        if local_match:
            self.send_message(f"*Zia:* {local_match['text']}", chat_id=chat_id)
            return

        # Route to Gemini Flash Brain
        from engine.brain import brain_engine
        try:
            reply = asyncio.run(brain_engine.think_and_reply(user_message=text))
            reply_text = reply.get("text", "I processed your request.")
            self.send_message(f"*Zia:* {reply_text}", chat_id=chat_id)
        except Exception as e:
            self.send_message(f"*Zia Error:* {e}", chat_id=chat_id)

    def _poll_updates(self):
        """Long-polling loop for incoming Telegram messages."""
        while self.is_running:
            if not self.bot_token:
                time.sleep(10)
                continue

            try:
                url = self._api_url(f"getUpdates?offset={self.last_update_id + 1}&timeout=25")
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    if data.get("ok"):
                        for update in data.get("result", []):
                            self.last_update_id = update["update_id"]
                            msg = update.get("message", {})
                            chat_id = str(msg.get("chat", {}).get("id", ""))
                            text = msg.get("text", "")

                            # Security check: only respond to authorized chat ID if configured
                            if self.default_chat_id and chat_id != str(self.default_chat_id):
                                continue

                            if text:
                                self.process_incoming_command(text, chat_id)
            except Exception:
                time.sleep(5)

    def start_polling(self):
        """Starts background Telegram polling daemon."""
        if not self.bot_token:
            return
        if self.is_running:
            return

        self.is_running = True
        self._thread = threading.Thread(target=self._poll_updates, daemon=True)
        self._thread.start()

    def stop_polling(self):
        self.is_running = False


# Global Telegram gateway singleton
telegram_gateway = TelegramRemoteGateway()
