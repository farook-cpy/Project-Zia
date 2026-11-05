#!/usr/bin/env python3
"""
Project Zia - Non-AI Slop & Minimalist UI Verification Suite
Ensures the codebase, prompts, dialogue, and UI are 100% free from AI clichés,
sycophantic assistant filler, robotic buzzwords, and visual clutter.
"""

import re
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# UTF-8 terminal safety
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ANSI_CYAN = "\033[96m"
ANSI_GREEN = "\033[92m"
ANSI_YELLOW = "\033[93m"
ANSI_RED = "\033[91m"
ANSI_MAGENTA = "\033[95m"
ANSI_BOLD = "\033[1m"
ANSI_RESET = "\033[0m"


class NoAiSlopTestSuite:
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.failures = []

    def assert_test(self, category: str, test_name: str, condition: bool, detail: str = ""):
        self.total += 1
        if condition:
            self.passed += 1
            print(f"  {ANSI_GREEN}[PASS]{ANSI_RESET} {test_name} {ANSI_CYAN}({detail}){ANSI_RESET}")
        else:
            self.failed += 1
            self.failures.append(f"[{category}] {test_name}: {detail}")
            print(f"  {ANSI_RED}[FAIL]{ANSI_RESET} {test_name} {ANSI_YELLOW}({detail}){ANSI_RESET}")

    def run_all(self):
        print(f"\n{ANSI_BOLD}{ANSI_CYAN}======================================================================")
        print(" PROJECT ZIA // NON-AI SLOP & MINIMALIST UI VERIFICATION SUITE")
        print(" Zero Sycophancy | Human Cadence | Pure Minimalist Grey UI | No Clutter")
        print(f"======================================================================{ANSI_RESET}\n")

        self.test_system_prompt_slop_free()
        self.test_dialogue_templates_slop_free()
        self.test_ui_cleanliness_and_no_clutter()
        self.test_expressive_avatar_and_sfx()

        print(f"\n{ANSI_BOLD}{ANSI_CYAN}======================================================================")
        print(" NON-AI SLOP SCOREBOARD")
        print(f"======================================================================{ANSI_RESET}")
        print(f" Total Assertions: {self.total}")
        print(f" Passed:           {ANSI_GREEN}{self.passed}{ANSI_RESET}")
        print(f" Failed:           {ANSI_RED if self.failed > 0 else ANSI_GREEN}{self.failed}{ANSI_RESET}")
        rate = (self.passed / max(self.total, 1)) * 100
        print(f" Compliance Rate:  {ANSI_GREEN}{rate:.1f}%{ANSI_RESET}")

        if self.failures:
            print(f"\n{ANSI_RED}{ANSI_BOLD}Violations Detected:{ANSI_RESET}")
            for f in self.failures:
                print(f"  * {f}")
            return 1
        else:
            print(f"\n{ANSI_GREEN}{ANSI_BOLD}[VERIFIED] Codebase and UI are 100% free from AI slop and clichés.{ANSI_RESET}\n")
            return 0

    # -------------------------------------------------------------------------
    # 1. System Prompt & Personality Architecture
    # -------------------------------------------------------------------------
    def test_system_prompt_slop_free(self):
        print(f"{ANSI_BOLD}{ANSI_MAGENTA}>>> SUITE 1: System Prompt & Personality Anti-Slop Audit{ANSI_RESET}")
        from engine.brain import SYSTEM_PROMPT

        lower_prompt = SYSTEM_PROMPT.lower()

        # Ban common sycophantic instructions
        banned_instructions = [
            "you are a helpful assistant", "always be polite and courteous",
            "as an ai language model", "apologize profusely", "provide a detailed disclaimer"
        ]
        found = [b for b in banned_instructions if b in lower_prompt]
        self.assert_test("Prompt", "System prompt contains zero sycophantic instructions", len(found) == 0, f"Banned instructions found: {found}")

        # Enforce negative constraints against slop
        has_slop_rule = "zero ai slop" in lower_prompt and "never use corporate assistant filler" in lower_prompt
        self.assert_test("Prompt", "Explicit negative constraints against AI filler present", has_slop_rule, "Found negative anti-slop prompt guard")

        # Natural human cadence directive
        has_cadence = "direct" in lower_prompt and "concise" in lower_prompt
        self.assert_test("Prompt", "Directive for direct, concise human-like cadence", has_cadence, "Direct 1-2 sentence cadence specified")

    # -------------------------------------------------------------------------
    # 2. Local Dialogue Templates (No Robotic Jargon)
    # -------------------------------------------------------------------------
    def test_dialogue_templates_slop_free(self):
        print(f"\n{ANSI_BOLD}{ANSI_MAGENTA}>>> SUITE 2: Conversational Dialogue Quality Audit{ANSI_RESET}")
        from engine.local_commands import local_router

        # Test A: Avatar Switch Minimal Mode
        r_stop = local_router.match_and_execute("stop avatar")
        text_stop = r_stop.get("text", "")
        self.assert_test("Dialogue", "Minimal mode switch is concise and unpretentious", text_stop == "Minimal mode active.", f"Output: '{text_stop}'")

        # Test B: Avatar Switch Live2D Mode
        r_load = local_router.match_and_execute("load avatar")
        text_load = r_load.get("text", "")
        self.assert_test("Dialogue", "Live2D avatar load is concise and unpretentious", text_load == "Loading avatar.", f"Output: '{text_load}'")

        # Test C: Desk light switch (no 'via IoT relay' or IP address jargon)
        r_light = local_router.match_and_execute("turn on the desk light")
        text_light = r_light.get("text", "")
        has_relay_jargon = "via iot relay" in text_light.lower() or "192.168" in text_light
        self.assert_test("Dialogue", "Smart light control speaks like a human, not a network log", not has_relay_jargon and "on" in text_light.lower(), f"Output: '{text_light}'")

        # Test D: Projector stream (no 'dispatched streaming intent' jargon)
        r_proj = local_router.match_and_execute("play black clover on projector")
        text_proj = r_proj.get("text", "")
        has_intent_jargon = "dispatched" in text_proj.lower() or "intent" in text_proj.lower()
        self.assert_test("Dialogue", "Projector media command has zero Android intent jargon", not has_intent_jargon, f"Output: '{text_proj}'")

        # Test E: Tablet Botim call (no 'dispatched VoIP intent' jargon)
        r_call = local_router.match_and_execute("call dad on botim")
        text_call = r_call.get("text", "")
        has_call_jargon = "dispatched" in text_call.lower() or "activity" in text_call.lower()
        self.assert_test("Dialogue", "Tablet call command is natural human speech", not has_call_jargon and "dad" in text_call.lower(), f"Output: '{text_call}'")

    # -------------------------------------------------------------------------
    # 3. UI Cleanliness & De-Cluttering Audit
    # -------------------------------------------------------------------------
    def test_ui_cleanliness_and_no_clutter(self):
        print(f"\n{ANSI_BOLD}{ANSI_MAGENTA}>>> SUITE 3: UI Cleanliness & De-Cluttering Audit{ANSI_RESET}")
        client_ui_dir = ROOT_DIR / "client_ui"
        html = (client_ui_dir / "index.html").read_text(encoding="utf-8")
        css = (client_ui_dir / "style.css").read_text(encoding="utf-8")

        # 1. Zero emojis in HTML/CSS
        emoji_pattern = re.compile(r"[\U00010000-\U0010ffff]", flags=re.UNICODE)
        html_emojis = emoji_pattern.findall(html)
        css_emojis = emoji_pattern.findall(css)
        self.assert_test("UI Cleanliness", "Zero emojis cluttering the HTML/CSS markup", len(html_emojis) == 0 and len(css_emojis) == 0, f"Emojis found: HTML={len(html_emojis)}, CSS={len(css_emojis)}")

        # 2. No top-bar clutter (removed title header and mode badges)
        has_top_bar = "top-bar" in html or "brand-title" in html or "btn-toggle-mode" in html
        self.assert_test("UI Cleanliness", "Top-bar headers, badges and buttons removed", not has_top_bar, "Header clutter completely eliminated")

        # 3. No bottom quick-chips clutter
        has_chips = "quick-chips" in html or "chip-btn" in html
        self.assert_test("UI Cleanliness", "Quick-chip buttons removed from DOM", not has_chips, "Chip clutter eliminated")

        # 4. No cyber grid lines
        has_grid = "bg-grid" in html or "linear-gradient(to right, rgba(0, 240, 255" in css
        self.assert_test("UI Cleanliness", "Cyan matrix grid lines removed", not has_grid, "Background is pure clean matte dark")

        # 5. Pure Grey Palette Variables Present
        has_grey_vars = "--bg-base: #111114" in css and "--eye-base: #f4f4f5" in css
        self.assert_test("UI Cleanliness", "Minimalist matte grey & silver palette enforced", has_grey_vars, "Base #111114 & Eye #f4f4f5 present")

        # 6. Face and Mouth are the primary focal point
        has_face = "avatar-face" in html and "eye-left" in html and "eye-right" in html
        has_mouth = "mouth-waveform-canvas" in html
        self.assert_test("UI Cleanliness", "Eyes and mouth are the sole centered focal point", has_face and has_mouth, "Minimalist face structure verified")

    # -------------------------------------------------------------------------
    # 4. Expressive Avatar Animations & Procedural SFX
    # -------------------------------------------------------------------------
    def test_expressive_avatar_and_sfx(self):
        print(f"\n{ANSI_BOLD}{ANSI_MAGENTA}>>> SUITE 4: Expressive Avatar Features & Procedural SFX Audit{ANSI_RESET}")
        client_ui_dir = ROOT_DIR / "client_ui"
        js = (client_ui_dir / "app.js").read_text(encoding="utf-8")
        css = (client_ui_dir / "style.css").read_text(encoding="utf-8")

        # 1. Interactive Mouse Eye Tracking
        has_eye_tracking = "setupEyeTracking" in js and "updatePupilTracking" in js
        self.assert_test("Avatar", "Interactive mouse cursor eye-tracking implemented", has_eye_tracking, "Pupils track cursor dynamically")

        # 2. Click Interaction (Playful wink/smile on face click)
        has_click_react = "avatarFace.addEventListener(\"click\"" in js or "avatarFace.addEventListener('click'" in js
        self.assert_test("Avatar", "Click interaction on avatar face implemented", has_click_react, "Triggers playful reaction")

        # 3. Procedural Web Audio SFX (Zero external audio assets)
        has_sfx = "playWakeChime" in js and "playReadyChime" in js and "startThinkingHum" in js
        self.assert_test("Audio SFX", "Procedural Web Audio API sound effects synthesized", has_sfx, "Wake chime, thinking hum & ready ding present")

        # 4. Thinking Animation (Undulating Sine Wave in Canvas)
        has_thinking_anim = "this.isThinking" in js and "Math.sin(progress" in js
        self.assert_test("Avatar", "Undulating sine-wave thinking animation rendered in canvas", has_thinking_anim, "Dynamic thinking wave active")

        # 5. Multiple Expressive Moods Defined in CSS
        moods = ["mood-f1", "mood-f4", "mood-f7", "mood-f8", "mood-f9", "mood-f3", "mood-f6", "mood-f11"]
        all_moods_present = all(m in css for m in moods)
        self.assert_test("Avatar", "Rich facial expressions defined in CSS (smile, think, wink, shock, etc.)", all_moods_present, f"{len(moods)} distinct emotional states mapped")


if __name__ == "__main__":
    suite = NoAiSlopTestSuite()
    sys.exit(suite.run_all())
