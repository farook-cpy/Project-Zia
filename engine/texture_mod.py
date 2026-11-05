import time
from pathlib import Path
from PIL import Image, ImageEnhance

ROOT_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = ROOT_DIR / "assets" / "models" / "Kaguya"
TEXTURE_DIR = MODEL_DIR / "textures"
if not TEXTURE_DIR.exists():
    TEXTURE_DIR = ROOT_DIR / "assets" / "models" / "TianYeLulu" / "IceGirl.8192"

BASE_TEXTURE = TEXTURE_DIR / "texture_00.png"
TEMP_SKIN = TEXTURE_DIR / "temp_skin.png"

class LivingAssetEngine:
    def __init__(self):
        self.active_style = "default"

    def apply_style(self, style_name: str = "night") -> dict:
        """
        Dynamically generates an ambient style variant of texture_00.png
        and saves it to temp_skin.png for zero-lag hot texture swapping.
        """
        if not BASE_TEXTURE.exists():
            return {"success": False, "error": "Base texture not found"}

        style_name = style_name.lower().strip()
        rel_base = BASE_TEXTURE.relative_to(ROOT_DIR).as_posix()

        if style_name in ["default", "day", "reset", "normal"]:
            self.active_style = "default"
            return {
                "success": True,
                "style": "default",
                "texture_url": f"/{rel_base}?t={int(time.time())}"
            }

        try:
            img = Image.open(BASE_TEXTURE).convert("RGBA")
            r, g, b, a = img.split()

            if "night" in style_name or "dark" in style_name:
                # Night Ambient: cool moonlight blue/purple tint with soft contrast
                r = r.point(lambda i: int(i * 0.82))
                g = g.point(lambda i: int(i * 0.88))
                b = b.point(lambda i: min(255, int(i * 1.12)))
                styled_img = Image.merge("RGBA", (r, g, b, a))

                enhancer = ImageEnhance.Contrast(styled_img)
                styled_img = enhancer.enhance(1.08)

            elif "cyber" in style_name or "neon" in style_name:
                # Cyberpunk Neon: punchy magenta/cyan enhancement
                r = r.point(lambda i: min(255, int(i * 1.15)))
                g = g.point(lambda i: int(i * 0.90))
                b = b.point(lambda i: min(255, int(i * 1.25)))
                styled_img = Image.merge("RGBA", (r, g, b, a))

                enhancer = ImageEnhance.Contrast(styled_img)
                styled_img = enhancer.enhance(1.15)

            elif "warm" in style_name or "sunset" in style_name:
                # Sunset Golden Hour: warm amber glow
                r = r.point(lambda i: min(255, int(i * 1.18)))
                g = g.point(lambda i: int(i * 0.98))
                b = b.point(lambda i: int(i * 0.78))
                styled_img = Image.merge("RGBA", (r, g, b, a))

                enhancer = ImageEnhance.Contrast(styled_img)
                styled_img = enhancer.enhance(1.05)

            else:
                styled_img = img

            # Save optimized texture sheet
            styled_img.save(TEMP_SKIN, "PNG", optimize=True)
            self.active_style = style_name

            rel_temp = TEMP_SKIN.relative_to(ROOT_DIR).as_posix()
            timestamp = int(time.time() * 1000)
            url = f"/{rel_temp}?t={timestamp}"

            return {
                "success": True,
                "style": style_name,
                "texture_url": url
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

living_assets = LivingAssetEngine()

