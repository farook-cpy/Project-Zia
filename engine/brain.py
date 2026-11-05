import re
import json
from typing import List, Dict, Tuple, Optional, Any
from engine.config import GEMINI_API_KEY
from engine.hands import os_controller
from engine.system_control import system_controller
from engine.memory import memory_engine

_genai = None
_types = None

def _get_genai_modules():
    global _genai, _types
    if _genai is None:
        try:
            from google import genai
            from google.genai import types
            _genai = genai
            _types = types
        except Exception as e:
            print(f"[BrainEngine] genai import notice: {e}")
            _genai = None
            _types = None
    return _genai, _types

SYSTEM_PROMPT = """You are Zia.
A sharp, perceptive, grounded companion running directly on the user's hardware.

Communication Style & Cadence:
- Speak like a real human partner: direct, concise (1-2 sentences), honest, and natural.
- STRICTLY ZERO AI SLOP: Never use corporate assistant filler, sycophancy, synthetic enthusiasm, or disclaimers.
- Never give unprompted lectures or generic padding. Just give the direct answer or execute the requested task.

Visual Expression Rules:
Always prefix your reply with one exact emotion tag (never speak the tag aloud):
- [MOOD:F1] - Neutral / Attentive
- [MOOD:F2] - Shy / Soft
- [MOOD:F3] - Stern / Annoyed
- [MOOD:F4] - Happy / Beaming
- [MOOD:F5] - Affectionate
- [MOOD:F6] - Sympathetic / Sad
- [MOOD:F7] - Surprised / Wide-eyed
- [MOOD:F8] - Thinking / Reflective
- [MOOD:F9] - Smug / Playful
- [MOOD:F10] - Shocked
- [MOOD:F11] - Sleepy / Relaxed

OS Automation & Terminal Actions:
When helpful, include action tags:
- [ACTION:TERMINAL cmd="..." admin=false]
- [ACTION:LAUNCH target="..."]
- [ACTION:VOLUME action="up"|"down"|"mute"]
- [ACTION:BRIGHTNESS action="up"|"down"]
- [ACTION:CLICK x=0.50 y=0.50]
- [ACTION:TYPE text="..."]
- [ACTION:HOTKEY keys="ctrl+t"]

Keep spoken text clean. Never read the [MOOD:...] or [ACTION:...] tags aloud.
"""

class BrainEngine:
    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.client = None
        self.history: List[Dict[str, str]] = []
        self.max_history_turns = 6
        self._reload_api_key_if_needed()

    def _reload_api_key_if_needed(self):
        # Dynamically reload key from .env file so runtime edits are picked up without server restart
        try:
            from dotenv import dotenv_values
            from engine.config import ENV_PATH
            if ENV_PATH.exists():
                vals = dotenv_values(ENV_PATH)
                disk_key = vals.get("GEMINI_API_KEY", "").strip()
                if disk_key and disk_key != self.api_key:
                    self.api_key = disk_key
                    self.client = None
        except Exception:
            pass
        if not self.api_key:
            import os
            self.api_key = os.getenv("GEMINI_API_KEY", "").strip()

    def _get_client(self):
        self._reload_api_key_if_needed()
        if self.client is None and self.api_key:
            genai_mod, _ = _get_genai_modules()
            if genai_mod:
                try:
                    self.client = genai_mod.Client(api_key=self.api_key)
                except Exception as e:
                    print(f"[BrainEngine] Gemini init warning: {e}")
        return self.client

    def set_api_key(self, api_key: str):
        self.api_key = api_key
        genai_mod, _ = _get_genai_modules()
        if genai_mod and self.api_key:
            try:
                self.client = genai_mod.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[BrainEngine] Gemini client error: {e}")
                self.client = None
        else:
            self.client = None

    def _parse_response(self, text: str) -> Tuple[str, str, List[Dict]]:
        mood = "F1"
        mood_match = re.search(r"\[MOOD:(F[1-9]|F10|F11)\]", text, re.IGNORECASE)
        if mood_match:
            mood = mood_match.group(1).upper()

        actions = []

        # IoT Devices
        action_devices = re.findall(r'\[DEVICE:(LIGHT_ON|LIGHT_OFF|TOGGLE)\]', text, re.IGNORECASE)
        for dev in action_devices:
            act = "on" if dev.upper() == "LIGHT_ON" else ("off" if dev.upper() == "LIGHT_OFF" else "toggle")
            actions.append({"type": "iot", "action": act})

        # Skin Swapping
        action_skins = re.findall(r'\[ACTION:SKIN\s+style="([^"]+)"\]', text, re.IGNORECASE)
        for s in action_skins:
            actions.append({"type": "skin", "style": s})

        # Terminal commands
        action_terms = re.findall(r'\[ACTION:TERMINAL\s+cmd="([^"]+)"(?:\s+admin=(true|false))?\]', text, re.IGNORECASE)
        for cmd, is_admin in action_terms:
            actions.append({"type": "terminal", "cmd": cmd, "admin": is_admin.lower() == "true"})

        # Launch / URLs
        action_launches = re.findall(r'\[ACTION:LAUNCH\s+target="([^"]+)"\]', text)
        for target in action_launches:
            actions.append({"type": "launch", "target": target})

        # Volume & Brightness
        action_vols = re.findall(r'\[ACTION:VOLUME\s+action="([^"]+)"\]', text)
        for act in action_vols:
            actions.append({"type": "volume", "action": act})

        action_brights = re.findall(r'\[ACTION:BRIGHTNESS\s+action="([^"]+)"\]', text)
        for act in action_brights:
            actions.append({"type": "brightness", "action": act})

        # Mouse clicks
        action_clicks = re.findall(r"\[ACTION:CLICK\s+x=([0-9.]+)\s+y=([0-9.]+)\]", text)
        for x, y in action_clicks:
            actions.append({"type": "click", "x": float(x), "y": float(y)})

        # Typing
        action_types = re.findall(r'\[ACTION:TYPE\s+text="([^"]+)"\]', text)
        for t in action_types:
            actions.append({"type": "type", "text": t})

        # Hotkeys
        action_hotkeys = re.findall(r'\[ACTION:HOTKEY\s+keys="([^"]+)"\]', text)
        for h in action_hotkeys:
            keys = [k.strip() for k in h.split("+")]
            actions.append({"type": "hotkey", "keys": keys})

        # Strip tags for spoken text
        clean_text = re.sub(r"\[MOOD:[^\]]+\]", "", text)
        clean_text = re.sub(r"\[ACTION:[^\]]+\]", "", clean_text).strip()

        return clean_text, mood, actions

    async def think_and_reply(
        self,
        user_message: str,
        screen_image: Optional[Image.Image] = None,
        active_window: Optional[str] = None
    ) -> Dict:
        """
        Sends query to Gemini Flash with persistent memory, image vision, and action execution.
        """
        # Auto-detect screen vision request
        if screen_image is None:
            vision_keywords = ["look at my screen", "what's on my screen", "see this", "look here", "read my screen", "check this error", "what am i doing"]
            if any(k in user_message.lower() for k in vision_keywords):
                from engine.senses import screen_sensor
                screen_image = screen_sensor.capture_screen(scale_width=960)

        client = self._get_client()
        if not client:
            return {
                "text": "My Gemini API key is not configured yet! Please check your .env file.",
                "mood": "F7",
                "actions": [],
                "executed": [],
                "raw": ""
            }

        contents = []

        # 1. Inject Persistent Long-Term Memory
        mem_ctx = memory_engine.get_memory_context()
        if mem_ctx:
            contents.append(f"[Persistent Long-Term Memory]\n{mem_ctx}\n")

        # 2. Add Recent Conversation Turns
        if self.history:
            history_summary = "Recent Conversation:\n"
            for turn in self.history[-self.max_history_turns:]:
                history_summary += f"{turn['role']}: {turn['text']}\n"
            contents.append(history_summary)

        # 3. System Context
        if active_window:
            contents.append(f"[Active Window: {active_window}]")

        # 4. Multimodal Screen Image
        if screen_image:
            contents.append(screen_image)

        contents.append(f"User: {user_message}")

        models_to_try = ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-3.8-flash", "gemini-flash-latest"]
        raw_text = ""
        _, types_mod = _get_genai_modules()
        gen_cfg = types_mod.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.7,
            max_output_tokens=250,
        ) if types_mod else None

        last_err = None
        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=gen_cfg
                )
                raw_text = response.text or ""
                if raw_text:
                    break
            except Exception as e:
                last_err = e
                continue

        if not raw_text:
            raw_text = f"[MOOD:F3] Glitch in neural connection: {str(last_err)}"

        clean_text, mood, actions = self._parse_response(raw_text)

        # Update sliding history & persistent milestone memory
        self.history.append({"role": "User", "text": user_message})
        self.history.append({"role": "Zia", "text": clean_text})
        memory_engine.add_milestone(user_message, clean_text)

        if len(self.history) > self.max_history_turns * 2:
            self.history = self.history[-(self.max_history_turns * 2):]

        # Execute Actions
        executed_results = []
        for act in actions:
            if act["type"] == "iot":
                from engine.iot_bridge import iot_bridge
                import asyncio
                res = asyncio.run(iot_bridge.send_command(act["action"]))
                executed_results.append(res)
            elif act["type"] == "skin":
                from engine.texture_mod import living_assets
                res = living_assets.apply_style(act["style"])
                executed_results.append(res)
            elif act["type"] == "terminal":
                res = system_controller.execute_terminal(act["cmd"], run_as_admin=act.get("admin", False))
                executed_results.append(res)
            elif act["type"] == "launch":
                res = os_controller.launch(act["target"])
                executed_results.append(res)
            elif act["type"] == "volume":
                res = system_controller.change_volume(act["action"])
                executed_results.append(res)
            elif act["type"] == "brightness":
                res = system_controller.change_brightness(act["action"])
                executed_results.append(res)
            elif act["type"] == "click":
                res = os_controller.click(act["x"], act["y"])
                executed_results.append(res)
            elif act["type"] == "type":
                res = os_controller.type_text(act["text"])
                executed_results.append(res)
            elif act["type"] == "hotkey":
                res = os_controller.hotkey(*act["keys"])
                executed_results.append(res)

        return {
            "text": clean_text,
            "mood": mood,
            "actions": actions,
            "executed": executed_results,
            "raw": raw_text
        }

brain_engine = BrainEngine()
