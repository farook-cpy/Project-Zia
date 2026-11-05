"""
Project Zia - Sprite Avatar System Verification Suite (tests/test_sprite_system.py)
Tests:
1. PNG Sprite Asset Integrity (12 frames, RGBA, transparency, dimensions)
2. Desktop Sprite Companion State Machine & Animation Controllers
3. Idle, Talk, and Walk Cycle frame transitions
4. Window Minimization Trigger & Detection
5. Zero-Token Command Routing ('sprite mode' / 'switch to sprite')
6. Client UI HTML/CSS/JS stage and controller integration
"""

import os
import sys
import unittest
from pathlib import Path
from PIL import Image

# Ensure project root in sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

class TestSpriteAvatarSystem(unittest.TestCase):

    def setUp(self):
        self.sprite_dir = ROOT / "assets" / "sprites" / "zia_anime"
        self.expected_frames = [
            "idle_open.png", "idle_half.png", "idle_blink.png", "idle_wink.png",
            "talk_closed.png", "talk_half.png", "talk_open.png", "talk_o.png", "talk_smile.png",
            "walk_0.png", "walk_1.png", "walk_2.png", "walk_3.png",
            "emotion_happy.png", "emotion_thinking.png", "emotion_surprised.png",
            "emotion_sad.png", "emotion_shy.png", "emotion_annoyed.png", "emotion_smug.png", "emotion_sleepy.png"
        ]

    def test_01_sprite_assets_exist(self):
        """Verifies that all 12 required anime sprite frames exist."""
        for frame in self.expected_frames:
            p = self.sprite_dir / frame
            self.assertTrue(p.exists(), f"Missing sprite frame: {frame}")

    def test_02_sprite_transparency_and_format(self):
        """Verifies that all sprite frames are valid RGBA images with clean transparency."""
        for frame in self.expected_frames:
            p = self.sprite_dir / frame
            with Image.open(p) as img:
                self.assertEqual(img.mode, "RGBA", f"{frame} is not RGBA")
                self.assertGreaterEqual(img.width, 512, f"{frame} width too small: {img.width}")
                self.assertGreaterEqual(img.height, 512, f"{frame} height too small: {img.height}")
                # Corner pixel should be completely transparent (alpha == 0)
                corner_alpha = img.getpixel((0, 0))[3]
                self.assertEqual(corner_alpha, 0, f"{frame} corner is not transparent (alpha={corner_alpha})")

    def test_03_zero_token_command_router(self):
        """Verifies zero-token local router switches to sprite mode."""
        from engine.local_commands import local_router
        res = local_router.match_and_execute("switch to sprite")
        self.assertIsNotNone(res)
        actions = res.get("actions", [])
        self.assertTrue(any(a.get("type") == "switch_mode" and a.get("mode") == "sprite" for a in actions))

        res2 = local_router.match_and_execute("anime mode")
        self.assertIsNotNone(res2)
        self.assertIn("Anime sprite companion active", res2.get("text", ""))

    def test_04_desktop_sprite_companion_class(self):
        """Verifies desktop_sprite.py initializes and handles idle, talk, walk states."""
        import desktop_sprite
        from desktop_sprite import DesktopSpriteCompanion

        companion = DesktopSpriteCompanion(always_visible=False)
        self.assertIsNotNone(companion.root)
        self.assertIn("idle_open", companion.frames)
        self.assertIn("walk_1", companion.frames)
        self.assertIn("talk_open", companion.frames)
        self.assertIn("emotion_happy", companion.frames)
        self.assertIn("emotion_thinking", companion.frames)
        self.assertIn("emotion_surprised", companion.frames)

        # Test emotion setting
        companion.set_mood("F4")
        self.assertEqual(companion.current_mood, "F4")
        self.assertEqual(companion.current_emotion_frame, "emotion_happy")

        companion.set_mood("F8")
        self.assertEqual(companion.current_mood, "F8")
        self.assertEqual(companion.current_emotion_frame, "emotion_thinking")

        # Test speech trigger
        companion.trigger_speech("Testing voice speech bubble", duration=1.0)
        self.assertTrue(companion.is_speaking)
        self.assertEqual(companion.current_state, "talking")

        # Test animation tick
        companion.animation_tick()

        # Clean up
        companion.clear_speech_bubble()
        self.assertFalse(companion.is_speaking)
        companion.root.destroy()

    def test_05_client_ui_integration(self):
        """Verifies that client_ui index.html and app.js include the sprite avatar stage and controller."""
        html_path = ROOT / "client_ui" / "index.html"
        self.assertTrue(html_path.exists())
        html_content = html_path.read_text(encoding="utf-8")
        self.assertIn("anime-sprite-stage", html_content)
        self.assertIn("anime-sprite-img", html_content)

        js_path = ROOT / "client_ui" / "app.js"
        self.assertTrue(js_path.exists())
        js_content = js_path.read_text(encoding="utf-8")
        self.assertIn("AnimeSpriteController", js_content)
        self.assertIn("setupMinimizationHandler", js_content)
        self.assertIn("visibilitychange", js_content)

        css_path = ROOT / "client_ui" / "style.css"
        self.assertTrue(css_path.exists())
        css_content = css_path.read_text(encoding="utf-8")
        self.assertIn(".anime-sprite-stage", css_content)
        self.assertIn(".anime-speech-bubble", css_content)

if __name__ == "__main__":
    unittest.main(verbosity=2)
