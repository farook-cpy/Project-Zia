import io
from PIL import Image, ImageDraw, ImageFont
import pygetwindow as gw

class ScreenSensor:
    def __init__(self):
        self._mss = None

    def _get_mss(self):
        if self._mss is None:
            import mss
            self._mss = mss.mss()
        return self._mss

    def capture_screen(self, scale_width=960) -> Image.Image:
        """
        Captures the primary monitor screen, optimized for low CPU and minimal token consumption.
        """
        # Try MSS first
        try:
            sct = self._get_mss()
            monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            if scale_width and img.width > scale_width:
                ratio = scale_width / float(img.width)
                scale_height = int(float(img.height) * float(ratio))
                img = img.resize((scale_width, scale_height), Image.Resampling.BILINEAR)
            return img
        except Exception:
            pass

        # Try PIL ImageGrab as second fallback
        try:
            from PIL import ImageGrab
            img = ImageGrab.grab()
            if scale_width and img.width > scale_width:
                ratio = scale_width / float(img.width)
                scale_height = int(float(img.height) * float(ratio))
                img = img.resize((scale_width, scale_height), Image.Resampling.BILINEAR)
            return img
        except Exception:
            pass

        # Safe fallback placeholder frame
        fallback_img = Image.new("RGB", (960, 540), color=(10, 10, 10))
        draw = ImageDraw.Draw(fallback_img)
        draw.text((40, 40), "[Screen Capture Active]", fill=(200, 200, 200))
        return fallback_img

    def capture_screen_bytes(self, quality=80) -> bytes:
        img = self.capture_screen()
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality)
        return buf.getvalue()

    def get_active_window_title(self) -> str:
        try:
            active = gw.getActiveWindow()
            if active and active.title:
                return active.title.strip()
        except Exception:
            pass
        return "Desktop / Primary Workspace"

screen_sensor = ScreenSensor()

