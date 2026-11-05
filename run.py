import sys
import os
import time
import shutil
import subprocess
import threading
import asyncio
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

# Auto-create .env from .env.example if missing
env_path = ROOT_DIR / ".env"
env_example = ROOT_DIR / ".env.example"
if not env_path.exists() and env_example.exists():
    env_path.write_text(env_example.read_text(encoding="utf-8"), encoding="utf-8")
    print("[*] Created .env configuration file from template.")

from engine.config import HOST, HTTP_PORT
from engine.server import start_server

def run_server_thread():
    """Runs the aiohttp engine server in a background daemon thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(start_server())
    except Exception as e:
        print(f"[Engine Server Error] {e}")

def run_desktop_sprite_thread():
    """Runs the floating desktop anime sprite companion that activates when minimized."""
    try:
        from desktop_sprite import DesktopSpriteCompanion
        companion = DesktopSpriteCompanion(always_visible=False)
        companion.run()
    except Exception as e:
        print(f"[*] Desktop sprite notice: {e}")

def launch_desktop_window(target_url: str, is_overlay: bool = False):
    """
    Launches a dedicated native desktop window (no browser tabs, no URL bar).
    If is_overlay is True:
      - Runs as a frameless, transparent, always-on-top floating desktop companion
      - Draggable to any corner or position on screen with zero background
    Cross-platform: Linux Mint (WebKitGTK), macOS (WKWebView), Windows (WebView2).
    """
    if is_overlay:
        sep = "&" if "?" in target_url else "?"
        target_url = f"{target_url}{sep}overlay=1"

    # 1. Try native pywebview window
    try:
        import webview
        mode_str = "Transparent Desktop Overlay" if is_overlay else "Standard Window"
        print(f"[*] Launching native desktop companion ({mode_str})...")
        window = webview.create_window(
            title="FAITH // Zia",
            url=target_url,
            width=360 if is_overlay else 460,
            height=520 if is_overlay else 680,
            resizable=True,
            frameless=is_overlay,
            on_top=is_overlay,
            transparent=is_overlay,
            easy_drag=True,
            background_color="#00000000" if is_overlay else "#000000"
        )
        webview.start()
        return True
    except Exception as e_wv:
        print(f"[*] Native webview notice: {e_wv}")

    # 2. Fallback: launch standalone app window (Chromium / Chrome / Edge --app)
    print("[*] Launching standalone application window mode...")
    app_candidates = [
        "msedge", "google-chrome", "chromium-browser", "chromium", "brave-browser"
    ]
    for exe in app_candidates:
        if shutil.which(exe):
            subprocess.Popen([exe, f"--app={target_url}"])
            return True

    # 3. Final fallback: default system browser
    import webbrowser
    webbrowser.open(target_url)
    return True

def main():
    is_overlay = ("--overlay" in sys.argv or "--widget" in sys.argv or "-o" in sys.argv)
    mode_title = "Transparent Desktop Overlay Mode" if is_overlay else "Standard Visual Mode"

    print("=" * 60)
    print(f"[*] Project FAITH // Zia Engine [{mode_title}]")
    print(f"[*] Target Host: http://{HOST}:{HTTP_PORT}/")
    print("=" * 60)

    # Start backend server daemon
    server_thread = threading.Thread(target=run_server_thread, daemon=True)
    server_thread.start()

    # Start desktop anime sprite companion (activates automatically when window is minimized)
    if "--no-sprite" not in sys.argv:
        sprite_thread = threading.Thread(target=run_desktop_sprite_thread, daemon=True)
        sprite_thread.start()

    # Wait for server port to be ready
    time.sleep(1.2)

    # Launch dedicated standalone desktop window
    url = f"http://{HOST}:{HTTP_PORT}/"
    launch_desktop_window(url, is_overlay=is_overlay)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[*] Project Zia stopped cleanly.")
