import sys
import os
import shutil
import subprocess
import webbrowser

_pyautogui = None

def get_pyautogui():
    global _pyautogui
    if _pyautogui is None:
        try:
            import pyautogui
            pyautogui.FAILSAFE = True
            pyautogui.PAUSE = 0.05
            _pyautogui = pyautogui
        except Exception:
            _pyautogui = None
    return _pyautogui

class OSController:
    def __init__(self):
        self._screen_width = None
        self._screen_height = None
        self.os_type = sys.platform  # 'win32', 'linux', 'darwin'

    @property
    def screen_size(self):
        if self._screen_width is None:
            ag = get_pyautogui()
            if ag:
                try:
                    self._screen_width, self._screen_height = ag.size()
                except Exception:
                    self._screen_width, self._screen_height = (1920, 1080)
            else:
                self._screen_width, self._screen_height = (1920, 1080)
        return (self._screen_width, self._screen_height)

    @property
    def screen_width(self):
        return self.screen_size[0]

    @property
    def screen_height(self):
        return self.screen_size[1]

    def click(self, x_ratio: float, y_ratio: float, button: str = "left", clicks: int = 1) -> dict:
        """
        Translates normalized coordinates (0.0 to 1.0) to screen pixels and clicks.
        """
        ag = get_pyautogui()
        if not ag:
            return {"success": False, "error": "pyautogui unavailable"}
        try:
            clamped_x = max(0.0, min(1.0, float(x_ratio)))
            clamped_y = max(0.0, min(1.0, float(y_ratio)))
            target_x = int(clamped_x * self.screen_width)
            target_y = int(clamped_y * self.screen_height)
            ag.moveTo(target_x, target_y, duration=0.2, tween=ag.easeOutQuad)
            ag.click(x=target_x, y=target_y, clicks=clicks, button=button)
            return {"success": True, "action": "click", "coords": [target_x, target_y]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def type_text(self, text: str, interval: float = 0.02) -> dict:
        ag = get_pyautogui()
        if not ag:
            return {"success": False, "error": "pyautogui unavailable"}
        try:
            ag.write(text, interval=interval)
            return {"success": True, "action": "type_text", "length": len(text)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def hotkey(self, *keys) -> dict:
        ag = get_pyautogui()
        if not ag:
            return {"success": False, "error": "pyautogui unavailable"}
        try:
            ag.hotkey(*keys)
            return {"success": True, "action": "hotkey", "keys": list(keys)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def open_url(self, url: str) -> dict:
        """
        Opens a URL cross-platform (Linux Mint, macOS, Windows).
        """
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        try:
            webbrowser.open(url)
            return {"success": True, "action": "open_url", "url": url}
        except Exception as e:
            return {"success": False, "error": str(e), "url": url}

    def launch(self, target: str) -> dict:
        """
        Launches an application or URL cross-platform (Linux Mint, macOS, Windows).
        """
        target = target.strip()

        # Check common shorthand targets
        shortcuts = {
            "yt": "https://www.youtube.com",
            "youtube": "https://www.youtube.com",
            "ig": "https://www.instagram.com",
            "instagram": "https://www.instagram.com",
            "spotify": "https://open.spotify.com",
            "github": "https://github.com",
            "reddit": "https://reddit.com",
            "twitter": "https://x.com",
            "x": "https://x.com"
        }

        lower_target = target.lower()
        if lower_target in shortcuts:
            return self.open_url(shortcuts[lower_target])

        # If it looks like a URL
        if lower_target.startswith("http://") or lower_target.startswith("https://") or lower_target.endswith(".com") or lower_target.endswith(".org"):
            return self.open_url(target)

        # Desktop Application Launch (Cross-OS)
        try:
            if self.os_type == "linux":
                # Linux Mint / Ubuntu
                cmd = target if shutil.which(target) else f"xdg-open {target}"
                subprocess.Popen(cmd, shell=True)
            elif self.os_type == "darwin":
                # macOS
                subprocess.Popen(f"open -a '{target}'", shell=True)
            else:
                # Windows
                subprocess.Popen(f"start {target}", shell=True)
            return {"success": True, "action": "launch", "target": target}
        except Exception as e:
            return {"success": False, "error": str(e), "target": target}

os_controller = OSController()
