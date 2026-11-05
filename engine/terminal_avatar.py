import sys
import time
import math
import threading

# ANSI 256 Color Palette
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_HAIR = "\033[38;5;141m"       # Lilac / Lavender
C_HAIR_SHADOW = "\033[38;5;99m" # Deep Violet
C_SKIN = "\033[38;5;224m"       # Ivory Peach
C_EYE_CYAN = "\033[38;5;51m"    # Cyber Ice Blue
C_EYE_STAR = "\033[38;5;220m"    # Golden Yellow
C_EYE_LOVE = "\033[38;5;205m"    # Hot Pink
C_BLUSH = "\033[38;5;204m"       # Soft Rose
C_MOUTH = "\033[38;5;197m"       # Ruby Red
C_BUST = "\033[38;5;236m"        # Dark Obsidian
C_BUST_ACCENT = "\033[38;5;68m"  # Slate Blue
C_TEAR = "\033[38;5;39m"         # Cyan Water

class TerminalAvatarRenderer:
    """
    High-performance 24 FPS ANSI/ASCII Terminal Avatar Engine.
    Animates Zia's facial expressions, breathing cycles, and audio lip-sync
    directly inside standard terminal windows (SSH/tmux/CLI) with 0% VRAM and <0.5% CPU.
    """
    def __init__(self):
        self.active_expression = "F1"
        self.mouth_open = 0.0 # 0.0 to 1.0
        self.is_running = False

    def get_eye_rendering(self, expr: str, eye_blink: bool):
        expr = expr.upper()
        if eye_blink and expr != "F11":
            return f"{C_HAIR}──{C_RESET}", f"{C_HAIR}──{C_RESET}"

        if expr == "F4": # Star Eyes
            return f"{C_EYE_STAR}★ {C_RESET}", f"{C_EYE_STAR}★ {C_RESET}"
        elif expr == "F5": # Love Eyes
            return f"{C_EYE_LOVE}♥ {C_RESET}", f"{C_EYE_LOVE}♥ {C_RESET}"
        elif expr == "F3": # Angry
            return f"{C_EYE_CYAN}◣ {C_RESET}", f"{C_EYE_CYAN}◢ {C_RESET}"
        elif expr == "F6": # Sad / Cry
            return f"{C_EYE_CYAN}╥ {C_RESET}", f"{C_EYE_CYAN}╥ {C_RESET}"
        elif expr == "F7": # Surprised
            return f"{C_EYE_CYAN}⊙ {C_RESET}", f"{C_EYE_CYAN}⊙ {C_RESET}"
        elif expr == "F8": # Thinking
            return f"{C_EYE_CYAN}・{C_RESET}", f"{C_EYE_CYAN}・{C_RESET}"
        elif expr == "F9": # Smug / Wink
            return f"{C_EYE_CYAN}^ {C_RESET}", f"{C_HAIR}──{C_RESET}"
        elif expr == "F10": # Shocked
            return f"{C_EYE_CYAN}⬚ {C_RESET}", f"{C_EYE_CYAN}⬚ {C_RESET}"
        elif expr == "F11": # Sleepy
            return f"{C_HAIR}─ {C_RESET}", f"{C_HAIR}─ {C_RESET}"
        else: # F1 Neutral / F2 Blush
            return f"{C_EYE_CYAN}● {C_RESET}", f"{C_EYE_CYAN}● {C_RESET}"

    def get_mouth_rendering(self, expr: str, mouth_open: float):
        expr = expr.upper()
        if mouth_open > 0.6:
            return f"{C_MOUTH}█{C_RESET}"
        elif mouth_open > 0.2:
            return f"{C_MOUTH}▄{C_RESET}"

        if expr == "F2": # Blush
            return f"{C_MOUTH}ω{C_RESET}"
        elif expr == "F3": # Angry
            return f"{C_MOUTH}▲{C_RESET}"
        elif expr == "F4": # Star eyes
            return f"{C_MOUTH}▽{C_RESET}"
        elif expr == "F5": # Love eyes
            return f"{C_MOUTH}3{C_RESET}"
        elif expr == "F6": # Sad
            return f"{C_MOUTH}⌒{C_RESET}"
        elif expr == "F7": # Surprised
            return f"{C_MOUTH}O{C_RESET}"
        elif expr == "F8": # Thinking
            return f"{C_MOUTH}~{C_RESET}"
        elif expr == "F9": # Smug tongue
            return f"{C_MOUTH}P{C_RESET}"
        elif expr == "F10": # Shocked
            return f"{C_MOUTH}口{C_RESET}"
        elif expr == "F11": # Sleepy
            return f"{C_HAIR}-{C_RESET}"
        else:
            return f"{C_HAIR}─{C_RESET}"

    def render_frame(self, expr: str = "F1", mouth_val: float = 0.0, tick: float = 0.0) -> str:
        """
        Renders a single high-density ANSI ASCII portrait frame.
        """
        expr = expr.upper()

        # Natural procedural blinking (every ~3.5s)
        cycle = tick % 3.5
        is_blinking = (cycle < 0.15) and (expr != "F11")

        # Procedural breathing offset
        b_offset = " " if math.sin(tick * 1.5) > 0 else ""

        l_eye, r_eye = self.get_eye_rendering(expr, is_blinking)
        mouth = self.get_mouth_rendering(expr, mouth_val)

        # Cheeks / Blush
        if expr in ["F2", "F5"]:
            l_cheek = f"{C_BLUSH}///{C_RESET}"
            r_cheek = f"{C_BLUSH}///{C_RESET}"
        elif expr == "F6": # Tears
            l_cheek = f"{C_TEAR} ' {C_RESET}"
            r_cheek = f"{C_TEAR} ' {C_RESET}"
        else:
            l_cheek = f"{C_SKIN}   {C_RESET}"
            r_cheek = f"{C_SKIN}   {C_RESET}"

        # Eyebrows
        if expr == "F3":
            l_brow = f"{C_HAIR}\\  {C_RESET}"
            r_brow = f"{C_HAIR}  /{C_RESET}"
        elif expr == "F6":
            l_brow = f"{C_HAIR}/  {C_RESET}"
            r_brow = f"{C_HAIR}  \\{C_RESET}"
        elif expr == "F8":
            l_brow = f"{C_HAIR}─  {C_RESET}"
            r_brow = f"{C_HAIR}  ?{C_RESET}"
        else:
            l_brow = f"{C_HAIR}── {C_RESET}"
            r_brow = f"{C_HAIR} ──{C_RESET}"

        crown = f"{C_EYE_STAR}   ▲   ▲   ▲   {C_RESET}" if expr == "F4" else f"{C_HAIR_SHADOW}               {C_RESET}"
        sleep_bubble = f"{C_HAIR_SHADOW}  z Z Z{C_RESET}" if expr == "F11" else "       "

        frame = f"""
{C_HAIR_SHADOW}         ╭───────────╮{C_RESET}
{C_HAIR_SHADOW}       ╭─┤{crown}├─╮{C_RESET}
{C_HAIR}      ╭╯ ╰───────────╯ ╰╮{C_RESET}
{C_HAIR}     ╭╯  {C_SKIN}╭───────────╮{C_HAIR}  ╰╮{C_RESET}
{C_HAIR}    ╭╯   {C_SKIN}│{l_brow}   {r_brow}{C_SKIN}│{C_HAIR}   ╰╮{C_RESET}
{C_HAIR}    │ {C_HAIR_SHADOW}╭──{C_SKIN}│  {l_eye}   {r_eye} {C_SKIN}│{C_HAIR_SHADOW}──╮{C_HAIR} │{sleep_bubble}{C_RESET}
{C_HAIR}    │ │  {C_SKIN}│ {l_cheek}   {r_cheek} {C_SKIN}│{C_HAIR}  │ │{C_RESET}
{C_HAIR}    │ │  {C_SKIN}│     {mouth}     {C_SKIN}│{C_HAIR}  │ │{C_RESET}
{C_HAIR}    ╰╮╰╮ {C_SKIN}╰───╮   ╭───╯{C_HAIR} ╭╯╭╯{C_RESET}
{C_HAIR}     ╰╮╰╮    {C_SKIN}│   │{C_HAIR}    ╭╯╭╯{C_RESET}
{C_BUST}  ╭───┴──┴───{C_SKIN}│   │{C_BUST}───┴──┴───╮{C_RESET}
{C_BUST} ╭╯ {C_BUST_ACCENT}Z I A{C_BUST}   ╰───╯          ╰╮{b_offset}{C_RESET}
{C_BUST} │                              │{b_offset}{C_RESET}
{C_BUST} ╰──────────────────────────────╯{C_RESET}
"""
        return frame

    def run_live(self, duration_sec: float = None, expr: str = "F1"):
        """
        Runs an interactive 24 FPS animation loop right inside the terminal.
        """
        self.is_running = True
        self.active_expression = expr

        # Hide cursor
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()

        start_time = time.time()
        tick = 0.0

        try:
            while self.is_running:
                now = time.time()
                if duration_sec and (now - start_time >= duration_sec):
                    break

                tick += 0.042 # ~24 FPS
                # Simulated speech wave bobbing
                mouth = abs(math.sin(tick * 3.0)) if self.mouth_open > 0.0 else 0.0

                frame = self.render_frame(self.active_expression, mouth, tick)

                # Reset cursor to top-left of viewport without flickering
                sys.stdout.write("\033[H")
                sys.stdout.write(frame)
                sys.stdout.flush()

                time.sleep(1.0 / 24.0)

        finally:
            self.is_running = False
            # Show cursor and reset colors
            sys.stdout.write("\033[?25h" + C_RESET)
            sys.stdout.flush()

terminal_avatar = TerminalAvatarRenderer()

