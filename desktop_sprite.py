"""
Project Zia - Floating Desktop Anime Sprite Companion (desktop_sprite.py)
A lightweight, transparent, click-draggable desktop pet that:
- Floats seamlessly on your Windows desktop with 0% VRAM and < 20MB RAM.
- Automatically ACTIVATES when the main Project Zia window is MINIMISED.
- Automatically HIDES when the main Project Zia window is RESTORED.
- Plays smooth animations:
  * Idle: gentle breathing sway, random natural blinking, occasional playful winks.
  * Talk: synchronized mouth phonemes with speech bubble when Zia speaks.
  * Walking: 4-phase walking cycle strolls along the desktop with step bob & turnarounds.
"""

import os
import sys
import time
import math
import random
import threading
import json
from pathlib import Path
import tkinter as tk
from PIL import Image, ImageTk, ImageOps

# Win32 window detection
IS_WINDOWS = sys.platform == "win32"
if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32

SPRITE_DIR = Path(__file__).resolve().parent / "assets" / "sprites" / "zia_anime"
SPRITE_SIZE = (260, 260)
KEY_COLOR = "#000001"  # Pure transparent key color for Windows

class DesktopSpriteCompanion:
    def __init__(self, always_visible: bool = False):
        self.always_visible = always_visible
        self.root = tk.Tk()
        self.root.title("Zia Sprite Companion")
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        if IS_WINDOWS:
            self.root.wm_attributes("-transparentcolor", KEY_COLOR)

        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()

        # Initial position: bottom right corner above taskbar
        self.win_w = SPRITE_SIZE[0]
        self.win_h = SPRITE_SIZE[1] + 60 # Extra space for speech bubble
        self.pos_x = self.screen_w - self.win_w - 40
        self.pos_y = self.screen_h - self.win_h - 50
        self.root.geometry(f"{self.win_w}x{self.win_h}+{self.pos_x}+{self.pos_y}")

        # Canvas
        self.canvas = tk.Canvas(
            self.root,
            width=self.win_w,
            height=self.win_h,
            bg=KEY_COLOR,
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        # Dragging support
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.canvas.bind("<Button-1>", self.on_drag_start)
        self.canvas.bind("<B1-Motion>", self.on_drag_motion)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)

        # Sprite frames dictionary
        self.frames = {}
        self.frames_flipped = {}
        self.load_sprites()

        # Animation state
        self.current_state = "idle" # "idle", "talking", "walking"
        self.is_walking = False
        self.walk_direction = -1 # -1 = left, 1 = right
        self.walk_step = 0
        self.walk_dest_x = self.pos_x
        self.facing_left = False

        # Blinking state
        self.blink_state = 0 # 0=open, 1=half, 2=blink, 3=half
        self.blink_timer = 0
        self.next_blink_tick = 60 # ~2 seconds

        # Talking state
        self.is_speaking = False
        self.talk_phoneme_idx = 0
        self.speech_text = ""
        self.speech_bubble_item = None
        self.speech_text_item = None
        self.speech_clear_tick = 0

        # Breathing oscillation
        self.tick_counter = 0

        # Emotion state
        self.current_mood = "F1"
        self.current_emotion_frame = None
        self.emotion_reset_tick = 0

        # Canvas Image Item
        self.sprite_canvas_item = self.canvas.create_image(
            self.win_w // 2,
            self.win_h - (SPRITE_SIZE[1] // 2),
            image=self.frames.get("idle_open")
        )

        # Window visibility / main window monitor
        self.is_active = True
        self.main_window_minimized = False

        # Start loops
        self.root.after(33, self.animation_tick) # ~30-40 FPS
        self.start_window_monitor_thread()
        self.start_websocket_listener_thread()

    def load_sprites(self):
        """Pre-renders and scales all anime sprite frames onto the transparent key."""
        frame_names = [
            "idle_open", "idle_half", "idle_blink", "idle_wink",
            "talk_closed", "talk_half", "talk_open", "talk_o", "talk_smile",
            "walk_0", "walk_1", "walk_2", "walk_3",
            "emotion_happy", "emotion_thinking", "emotion_surprised",
            "emotion_sad", "emotion_shy", "emotion_annoyed", "emotion_smug", "emotion_sleepy"
        ]

        bg_key = Image.new("RGBA", SPRITE_SIZE, (0, 0, 1, 255))

        for name in frame_names:
            path = SPRITE_DIR / f"{name}.png"
            if path.exists():
                img = Image.open(path).convert("RGBA")
                resized = img.resize(SPRITE_SIZE, Image.Resampling.LANCZOS)
                comp = Image.alpha_composite(bg_key, resized)
                self.frames[name] = ImageTk.PhotoImage(comp)

                # Generate flipped frame for walking left
                mirrored = ImageOps.mirror(resized)
                comp_mirrored = Image.alpha_composite(bg_key, mirrored)
                self.frames_flipped[name] = ImageTk.PhotoImage(comp_mirrored)
            else:
                print(f"[DesktopSprite] Warning: Missing sprite frame {path}")

    def on_drag_start(self, event):
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def on_drag_motion(self, event):
        deltax = event.x - self.drag_start_x
        deltay = event.y - self.drag_start_y
        self.pos_x += deltax
        self.pos_y += deltay
        self.root.geometry(f"+{self.pos_x}+{self.pos_y}")

    def on_double_click(self, event):
        """Double click to trigger a playful wink and greeting!"""
        self.trigger_speech("Hey! I'm watching over your desktop while Zia is minimized~", duration=4.0)
        self.set_frame("idle_wink")

    def set_frame(self, frame_name: str):
        lookup = self.frames_flipped if self.facing_left else self.frames
        tk_img = lookup.get(frame_name) or self.frames.get("idle_open")
        if tk_img:
            self.canvas.itemconfig(self.sprite_canvas_item, image=tk_img)

    def set_mood(self, mood_code: str, duration: float = 4.2):
        """Sets the anime sprite's emotional expression and auto-resets back to neutral."""
        if not mood_code:
            return
        self.current_mood = mood_code.upper()
        emotion_map = {
            "F4": "emotion_happy",
            "F8": "emotion_thinking",
            "F7": "emotion_surprised",
            "F10": "emotion_surprised",
            "F6": "emotion_sad",
            "F2": "emotion_shy",
            "F5": "emotion_shy",
            "F3": "emotion_annoyed",
            "F9": "emotion_smug",
            "F11": "emotion_sleepy"
        }
        self.current_emotion_frame = emotion_map.get(self.current_mood)
        if self.current_emotion_frame and not self.is_speaking and not self.is_walking:
            self.set_frame(self.current_emotion_frame)

        if self.current_emotion_frame and self.current_mood != "F11":
            self.emotion_reset_tick = self.tick_counter + int(duration * 30)

    def trigger_speech(self, text: str, duration: float = 3.5):
        """Displays dialogue speech bubble and activates lip-syncing."""
        self.speech_text = text
        self.is_speaking = True
        self.current_state = "talking"
        self.speech_clear_tick = self.tick_counter + int(duration * 30)

        # Draw cute speech bubble
        self.render_speech_bubble(text)

    def render_speech_bubble(self, text: str):
        # Clear previous bubble
        if self.speech_bubble_item:
            self.canvas.delete(self.speech_bubble_item)
        if self.speech_text_item:
            self.canvas.delete(self.speech_text_item)

        if not text:
            return

        bubble_w = min(240, max(120, len(text) * 7 + 24))
        bubble_h = 42
        bx1 = (self.win_w - bubble_w) // 2
        by1 = 8
        bx2 = bx1 + bubble_w
        by2 = by1 + bubble_h

        # Rounded bubble
        self.speech_bubble_item = self.canvas.create_polygon(
            bx1 + 10, by1,
            bx2 - 10, by1,
            bx2, by1 + 10,
            bx2, by2 - 10,
            bx2 - 10, by2,
            bx1 + (bubble_w // 2) + 6, by2,
            bx1 + (bubble_w // 2), by2 + 10, # tail pointing down
            bx1 + (bubble_w // 2) - 6, by2,
            bx1 + 10, by2,
            bx1, by2 - 10,
            bx1, by1 + 10,
            fill="#ffffff",
            outline="#27272a",
            width=2,
            smooth=True
        )

        # Bubble text (clean sans-serif)
        disp_text = text if len(text) <= 52 else text[:50] + "..."
        self.speech_text_item = self.canvas.create_text(
            (bx1 + bx2) // 2,
            (by1 + by2) // 2,
            text=disp_text,
            fill="#18181b",
            font=("Segoe UI", 8, "bold"),
            width=bubble_w - 16,
            justify="center"
        )

    def clear_speech_bubble(self):
        if self.speech_bubble_item:
            self.canvas.delete(self.speech_bubble_item)
            self.speech_bubble_item = None
        if self.speech_text_item:
            self.canvas.delete(self.speech_text_item)
            self.speech_text_item = None
        self.is_speaking = False
        if self.current_state == "talking":
            self.current_state = "idle"
            self.set_frame(self.current_emotion_frame or "talk_closed")
            self.root.after(120, lambda: self.set_frame(self.current_emotion_frame or "idle_open"))

    # =========================================================================
    # Animation Tick Loop (~30 FPS)
    # =========================================================================
    def animation_tick(self):
        self.tick_counter += 1

        # Check speech timeout
        if self.is_speaking and self.tick_counter >= self.speech_clear_tick:
            self.clear_speech_bubble()

        # Check emotion timeout
        if self.current_emotion_frame and self.emotion_reset_tick and self.tick_counter >= self.emotion_reset_tick:
            self.current_emotion_frame = None
            self.current_mood = "F1"
            self.emotion_reset_tick = 0
            if not self.is_speaking and not self.is_walking:
                self.set_frame("idle_open")

        # State 1: Talking (Smooth Syllabic Cadence, No Flapping Glitch)
        if self.is_speaking:
            talk_cycle = ["talk_half", "talk_open", "talk_half", "talk_smile"]
            idx = (self.tick_counter // 4) % len(talk_cycle)
            self.set_frame(talk_cycle[idx])

        # State 2: Walking Cycle
        elif self.is_walking:
            walk_cycle = ["walk_0", "walk_1", "walk_2", "walk_3"]
            idx = (self.tick_counter // 4) % 4
            self.set_frame(walk_cycle[idx])

            # Move horizontally along desktop
            step_size = 3 * self.walk_direction
            self.pos_x += step_size
            self.facing_left = (self.walk_direction < 0)

            # Clamp within screen bounds
            min_x = 20
            max_x = self.screen_w - self.win_w - 20
            self.pos_x = max(min_x, min(max_x, self.pos_x))
            self.root.geometry(f"+{int(self.pos_x)}+{int(self.pos_y)}")

            # Check if reached walk destination
            if (self.walk_direction < 0 and self.pos_x <= self.walk_dest_x) or \
               (self.walk_direction > 0 and self.pos_x >= self.walk_dest_x):
                self.is_walking = False
                self.current_state = "idle"
                self.set_frame(self.current_emotion_frame or "idle_open")

        # State 3: Organic Multi-Frequency Idle Breathing, Gaze Sway & Blinking Loop
        else:
            # Random Stroll Decision (every ~10-15 seconds)
            if self.tick_counter % 300 == 0 and random.random() < 0.40:
                self.start_random_walk()
                self.root.after(33, self.animation_tick)
                return

            # Blinking cycle
            if self.tick_counter >= self.next_blink_tick:
                # 3-frame natural blink
                blink_subtick = self.tick_counter - self.next_blink_tick
                if blink_subtick < 2:
                    self.set_frame("idle_half")
                elif blink_subtick < 6:
                    self.set_frame("idle_blink")
                elif blink_subtick < 8:
                    self.set_frame("idle_half")
                else:
                    self.set_frame(self.current_emotion_frame or "idle_open")
                    # Schedule next blink (natural 20% double-blink chance)
                    is_double = random.random() < 0.20
                    delay = 18 if is_double else random.randint(80, 180)
                    self.next_blink_tick = self.tick_counter + delay
            else:
                # Occasional playful wink (~10% chance)
                if self.tick_counter % 420 == 120 and random.random() < 0.30:
                    self.set_frame("idle_wink")
                elif self.tick_counter % 420 == 134:
                    self.set_frame(self.current_emotion_frame or "idle_open")
                else:
                    # Multi-frequency organic breathing and gentle lateral sway
                    breath_y = math.sin(self.tick_counter * 0.04) * 2.8 + math.cos(self.tick_counter * 0.02) * 1.0
                    sway_x = math.cos(self.tick_counter * 0.025) * 1.5
                    self.canvas.coords(
                        self.sprite_canvas_item,
                        (self.win_w // 2) + sway_x,
                        self.win_h - (SPRITE_SIZE[1] // 2) + breath_y
                    )
                    self.set_frame(self.current_emotion_frame or "idle_open")

        self.root.after(33, self.animation_tick)

    def start_random_walk(self):
        """Picks a random destination along the bottom of the screen to stroll towards."""
        min_x = 40
        max_x = self.screen_w - self.win_w - 40
        stroll_dist = random.randint(140, 280)
        target_dir = random.choice([-1, 1])

        # Reverse if near screen border
        if self.pos_x + (stroll_dist * target_dir) < min_x:
            target_dir = 1
        elif self.pos_x + (stroll_dist * target_dir) > max_x:
            target_dir = -1

        self.walk_direction = target_dir
        self.walk_dest_x = max(min_x, min(max_x, self.pos_x + stroll_dist * target_dir))
        self.facing_left = (self.walk_direction < 0)
        self.is_walking = True
        self.current_state = "walking"

    # =========================================================================
    # Window Minimization Sentinel Thread
    # =========================================================================
    def start_window_monitor_thread(self):
        thread = threading.Thread(target=self._window_monitor_loop, daemon=True, name="WindowMonitor")
        thread.start()

    def _window_monitor_loop(self):
        """
        Continuously checks whether the main Project Zia window is minimised.
        Only shows the sprite companion when the project window IS MINIMISED.
        """
        if not IS_WINDOWS:
            return

        last_minimized = None

        while True:
            time.sleep(0.35)
            if self.always_visible:
                continue

            minimized = self.check_is_project_minimized()

            if minimized != last_minimized:
                last_minimized = minimized
                if minimized:
                    # Main window was MINIMISED! Reveal sprite companion!
                    self.root.after(0, self.reveal_companion)
                else:
                    # Main window is RESTORED or NOT RUNNING! Hide companion!
                    self.root.after(0, self.hide_companion)

    def check_is_project_minimized(self) -> bool:
        """Finds Project Zia windows and checks if they are minimized (IsIconic)."""
        found_zia = False
        is_any_minimized = False

        def enum_handler(hwnd, extra):
            nonlocal found_zia, is_any_minimized
            if user32.IsWindowVisible(hwnd) or user32.IsIconic(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buf = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buf, length + 1)
                    title = buf.value.lower()
                    if ("zia" in title or "faith" in title) and "sprite" not in title:
                        found_zia = True
                        if user32.IsIconic(hwnd):
                            is_any_minimized = True
            return True

        EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows(EnumWindowsProc(enum_handler), 0)

        # If Zia is running and minimized -> True
        return found_zia and is_any_minimized

    def reveal_companion(self):
        self.root.deiconify()
        self.root.wm_attributes("-topmost", True)
        self.trigger_speech("I'm here! Zia is minimized.", duration=2.5)

    def hide_companion(self):
        self.root.withdraw()

    # =========================================================================
    # Server WebSocket Listener for Real-Time Speech & Reactions
    # =========================================================================
    def start_websocket_listener_thread(self):
        thread = threading.Thread(target=self._ws_listener_loop, daemon=True, name="WSListener")
        thread.start()

    def _ws_listener_loop(self):
        """Connects to Project Zia server WebSocket to receive speech and alerts."""
        import urllib.request
        while True:
            try:
                import websocket
                ws_url = "ws://127.0.0.1:8080/ws"
                def on_msg(ws, message):
                    try:
                        data = json.loads(message)
                        text = data.get("text") or data.get("message")
                        mood = data.get("mood") or data.get("id")
                        if mood:
                            self.root.after(0, lambda m=mood: self.set_mood(m))
                        if text:
                            self.root.after(0, lambda: self.trigger_speech(text, duration=max(3.0, len(text)*0.08)))
                    except Exception:
                        pass

                ws = websocket.WebSocketApp(ws_url, on_message=on_msg)
                ws.run_forever()
            except Exception:
                time.sleep(4.0)

    def run(self):
        print(f"[*] Project Zia - Anime Sprite Companion Started.")
        print(f"[*] State: Active when main window is minimised (always_visible={self.always_visible}).")
        if not self.always_visible:
            # Default to hidden until main window is minimized
            self.root.withdraw()
        self.root.mainloop()

if __name__ == "__main__":
    always_on = ("--always" in sys.argv or "-a" in sys.argv or "--visible" in sys.argv)
    app = DesktopSpriteCompanion(always_visible=always_on)
    app.run()
