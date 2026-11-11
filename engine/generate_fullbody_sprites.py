"""
Project Zia - Master Full-Body Cel-Shaded Anime Sprite Generator (Precision Aligned)
Generates all 21 high-resolution full-body sprite frames with clean alpha transparency.
Fixes:
- Erases mouth from row 256..264 completely so zero duplicate/split mouth marks exist.
- Eye bounding boxes strictly bounded inside eye sockets (left: 325..363, right: 405..443).
- Eyelids do not overlap hair or exterior face boundaries.
- Emotion features (tears, blush, smug :3) placed at exact facial landmark coordinates.
"""

import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUTPUT_DIR = "assets/sprites/zia_anime"
os.makedirs(OUTPUT_DIR, exist_ok=True)

RAW_SOURCE = r"C:\Users\Student\.gemini\antigravity\brain\47af9d27-79cc-4ab2-9667-c00f440d124f\zia_fullbody_base_1793851706764.jpg"

def build_clean_base_with_alpha():
    """Extracts transparent full-body character from solid white background."""
    raw = Image.open(RAW_SOURCE).convert("RGB")
    arr = np.array(raw)
    h, w, _ = arr.shape

    is_white = (arr[:, :, 0] > 242) & (arr[:, :, 1] > 242) & (arr[:, :, 2] > 242)

    from collections import deque
    visited = np.zeros((h, w), dtype=bool)
    queue = deque()

    for x in range(w):
        if is_white[0, x]:
            queue.append((0, x))
            visited[0, x] = True
        if is_white[h - 1, x]:
            queue.append((h - 1, x))
            visited[h - 1, x] = True
    for y in range(h):
        if is_white[y, 0]:
            queue.append((y, 0))
            visited[y, 0] = True
        if is_white[y, w - 1]:
            queue.append((y, w - 1))
            visited[y, w - 1] = True

    while queue:
        cy, cx = queue.popleft()
        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ny, nx = cy + dy, cx + dx
            if 0 <= ny < h and 0 <= nx < w:
                if not visited[ny, nx] and is_white[ny, nx]:
                    visited[ny, nx] = True
                    queue.append((ny, nx))

    alpha = np.full((h, w), 255, dtype=np.uint8)
    alpha[visited] = 0

    mask_img = Image.fromarray(alpha)
    mask_blur = mask_img.filter(ImageFilter.GaussianBlur(0.6))
    alpha_soft = np.array(mask_blur)
    alpha_final = np.where(visited, 0, np.clip(alpha_soft, 0, 255)).astype(np.uint8)

    rgba = np.dstack([arr, alpha_final])
    base_img = Image.fromarray(rgba, "RGBA")
    return base_img

base = build_clean_base_with_alpha()
W, H = base.size

# Palette sampled directly from Zia character
SKIN_BASE = (252, 222, 203, 255)
SKIN_SHADOW = (235, 185, 170, 255)
LASH_DARK = (44, 25, 20, 255)
CREASE_TONE = (220, 168, 154, 255)
MOUTH_OUTLINE = (54, 24, 20, 255)
MOUTH_CAVITY = (168, 48, 56, 255)
MOUTH_TONGUE = (235, 110, 120, 255)
TEETH_WHITE = (255, 255, 255, 255)

def mask_bangs(orig_img, modified_img):
    """Preserves dark foreground hair bangs in front of upper forehead/brows."""
    arr_orig = np.array(orig_img)
    arr_mod = np.array(modified_img)
    hair_region = (arr_orig[180:202, 310:470, 0] < 80) & \
                  (arr_orig[180:202, 310:470, 1] < 65) & \
                  (arr_orig[180:202, 310:470, 2] < 60) & \
                  (arr_orig[180:202, 310:470, 3] > 180)
    arr_mod[180:202, 310:470][hair_region] = arr_orig[180:202, 310:470][hair_region]
    return Image.fromarray(arr_mod)

def erase_original_mouth(img):
    """Cleanly replaces original mouth line with surrounding skin tone."""
    arr = np.array(img)
    skin_fill = arr[253:255, 366:404].mean(axis=0, keepdims=True).astype(np.uint8)
    for y in range(256, 265):
        arr[y, 366:404] = skin_fill
    return Image.fromarray(arr)

def draw_anime_blush(draw_obj, intensity=1.0):
    """Draws cute translucent anime blush ovals on cheeks."""
    rx = int(12 * intensity)
    ry = int(6 * intensity)
    blush_col = (255, 135, 145, int(90 * intensity))
    # Cheeks directly below eyes: left=(344, 236), right=(424, 236)
    draw_obj.ellipse([344 - rx, 236 - ry, 344 + rx, 236 + ry], fill=blush_col)
    draw_obj.ellipse([424 - rx, 236 - ry, 424 + rx, 236 + ry], fill=blush_col)
    
    line_col = (230, 100, 115, int(150 * intensity))
    for dx in [-5, 0, 5]:
        draw_obj.line([(344 + dx - 2, 236 + 3), (344 + dx + 2, 236 - 3)], fill=line_col, width=1)
        draw_obj.line([(424 + dx - 2, 236 + 3), (424 + dx + 2, 236 - 3)], fill=line_col, width=1)

def generate_idle_frames():
    # 1. idle_open (Base resting expression)
    base.save(os.path.join(OUTPUT_DIR, "idle_open.png"))

    # 2. idle_blink (Cute happy ^ ^ curved eyes)
    img = base.copy()
    draw = ImageDraw.Draw(img)
    # Left eye closed [325..363]
    draw.polygon([(325, 216), (330, 200), (356, 200), (363, 216), (356, 232), (330, 232)], fill=SKIN_BASE)
    draw.arc([325, 212, 363, 226], start=190, end=350, fill=LASH_DARK, width=3)
    draw.arc([330, 202, 358, 210], start=190, end=350, fill=CREASE_TONE, width=1)

    # Right eye closed [405..443]
    draw.polygon([(405, 216), (412, 200), (438, 200), (443, 216), (436, 232), (412, 232)], fill=SKIN_BASE)
    draw.arc([405, 212, 443, 226], start=190, end=350, fill=LASH_DARK, width=3)
    draw.arc([410, 202, 438, 210], start=190, end=350, fill=CREASE_TONE, width=1)

    img = mask_bangs(base, img)
    img.save(os.path.join(OUTPUT_DIR, "idle_blink.png"))

    # 3. idle_half (Half-closed eyelid for smooth 24fps blink transition)
    img_half = base.copy()
    draw_half = ImageDraw.Draw(img_half)
    # Left eye half [325..363]
    draw_half.polygon([(325, 216), (330, 200), (356, 200), (363, 216), (358, 219), (328, 219)], fill=SKIN_BASE)
    draw_half.arc([325, 213, 363, 225], start=185, end=355, fill=LASH_DARK, width=3)
    draw_half.arc([330, 204, 358, 212], start=190, end=350, fill=CREASE_TONE, width=1)

    # Right eye half [405..443]
    draw_half.polygon([(405, 216), (412, 200), (438, 200), (443, 216), (438, 219), (410, 219)], fill=SKIN_BASE)
    draw_half.arc([405, 213, 443, 225], start=185, end=355, fill=LASH_DARK, width=3)
    draw_half.arc([410, 204, 438, 212], start=190, end=350, fill=CREASE_TONE, width=1)

    img_half = mask_bangs(base, img_half)
    img_half.save(os.path.join(OUTPUT_DIR, "idle_half.png"))

    # 4. idle_wink (Left eye winks happily, right eye open with twinkle)
    img_wink = base.copy()
    draw_wink = ImageDraw.Draw(img_wink)
    draw_wink.polygon([(325, 216), (330, 200), (356, 200), (363, 216), (356, 232), (330, 232)], fill=SKIN_BASE)
    draw_wink.arc([325, 212, 363, 226], start=190, end=350, fill=LASH_DARK, width=3)
    draw_wink.arc([330, 202, 358, 210], start=190, end=350, fill=CREASE_TONE, width=1)
    
    # Tiny cute twinkle star
    cx, cy = 322, 212
    draw_wink.polygon([(cx, cy-4), (cx+1, cy-1), (cx+4, cy), (cx+1, cy+1), (cx, cy+4), (cx-1, cy+1), (cx-4, cy), (cx-1, cy-1)], fill=(255, 235, 110, 255))
    img_wink = mask_bangs(base, img_wink)
    img_wink.save(os.path.join(OUTPUT_DIR, "idle_wink.png"))
    print("[FullBodyGen] Idle frames generated.")

def generate_mouth_frames():
    # 5. talk_closed (Resting mouth)
    base.save(os.path.join(OUTPUT_DIR, "talk_closed.png"))

    # 6. talk_half (Parted lips)
    img_half = erase_original_mouth(base.copy())
    d = ImageDraw.Draw(img_half)
    d.line([(377, 259), (385, 260), (393, 259)], fill=MOUTH_OUTLINE, width=2)
    d.polygon([(378, 259), (385, 260), (392, 259), (390, 265), (385, 266), (380, 265)], fill=MOUTH_CAVITY, outline=MOUTH_OUTLINE, width=1)
    d.chord([381, 262, 389, 266], start=0, end=180, fill=MOUTH_TONGUE)
    img_half.save(os.path.join(OUTPUT_DIR, "talk_half.png"))

    # 7. talk_open (Open cavity for vowels 'ah', 'aa')
    img_open = erase_original_mouth(base.copy())
    d = ImageDraw.Draw(img_open)
    pts_cavity = [(375, 258), (385, 259), (395, 258), (393, 268), (385, 271), (377, 268)]
    d.polygon(pts_cavity, fill=MOUTH_CAVITY, outline=MOUTH_OUTLINE, width=2)
    d.polygon([(378, 259), (385, 260), (392, 259), (390, 263), (385, 263), (380, 263)], fill=TEETH_WHITE)
    d.chord([377, 264, 393, 271], start=0, end=180, fill=MOUTH_TONGUE)
    img_open.save(os.path.join(OUTPUT_DIR, "talk_open.png"))

    # 8. talk_o (Rounded phoneme 'oh', 'oo')
    img_o = erase_original_mouth(base.copy())
    d = ImageDraw.Draw(img_o)
    d.ellipse([379, 256, 391, 268], fill=MOUTH_CAVITY, outline=MOUTH_OUTLINE, width=2)
    d.ellipse([382, 262, 388, 267], fill=MOUTH_TONGUE)
    img_o.save(os.path.join(OUTPUT_DIR, "talk_o.png"))

    # 9. talk_smile (Talking smile)
    img_smile = erase_original_mouth(base.copy())
    d = ImageDraw.Draw(img_smile)
    pts_smile = [(373, 257), (385, 258), (397, 257), (395, 269), (385, 272), (375, 269)]
    d.polygon(pts_smile, fill=MOUTH_CAVITY, outline=MOUTH_OUTLINE, width=2)
    d.polygon([(376, 258), (385, 259), (394, 258), (392, 262), (385, 262), (378, 262)], fill=TEETH_WHITE)
    d.chord([376, 265, 394, 272], start=0, end=180, fill=MOUTH_TONGUE)
    img_smile.save(os.path.join(OUTPUT_DIR, "talk_smile.png"))
    print("[FullBodyGen] Mouth frames generated.")

def generate_walk_frames():
    """
    Seamless 4-phase walk cycle:
    Whole-body bob and continuous shear blending from the waist down (zero cuts or seams).
    """
    arr_base = np.array(base)
    h, w, c = arr_base.shape

    def create_walk_step(stride_px=0, bob_y=0, tilt_deg=0.0):
        shifted = np.zeros_like(arr_base)
        if bob_y > 0:
            shifted[bob_y:, :] = arr_base[:-bob_y, :]
        elif bob_y < 0:
            shifted[:bob_y, :] = arr_base[-bob_y:, :]
        else:
            shifted = arr_base.copy()

        waist_y = 580
        feet_y = 1340
        sheared = shifted.copy()

        if stride_px != 0:
            for y in range(waist_y, feet_y):
                progress = (y - waist_y) / (feet_y - waist_y)
                weight = 0.5 * (1.0 - math.cos(progress * math.pi))
                dx = int(round(stride_px * weight))
                if dx > 0:
                    sheared[y, dx:] = shifted[y, :-dx]
                    sheared[y, :dx] = 0
                elif dx < 0:
                    sheared[y, :dx] = shifted[y, -dx:]
                    sheared[y, dx:] = 0

        img = Image.fromarray(sheared, "RGBA")
        if tilt_deg != 0.0:
            img = img.rotate(tilt_deg, resample=Image.Resampling.BICUBIC, center=(w // 2, feet_y))
        return img

    w0 = create_walk_step(stride_px=-6, bob_y=4, tilt_deg=0.6)
    w0.save(os.path.join(OUTPUT_DIR, "walk_0.png"))

    w1 = create_walk_step(stride_px=0, bob_y=-3, tilt_deg=-0.3)
    w1.save(os.path.join(OUTPUT_DIR, "walk_1.png"))

    w2 = create_walk_step(stride_px=6, bob_y=4, tilt_deg=-0.6)
    w2.save(os.path.join(OUTPUT_DIR, "walk_2.png"))

    w3 = create_walk_step(stride_px=0, bob_y=-3, tilt_deg=0.3)
    w3.save(os.path.join(OUTPUT_DIR, "walk_3.png"))
    print("[FullBodyGen] Walk cycle frames generated.")

def generate_emotion_frames():
    # 1. emotion_happy (F4): Radiant smiling eyes, cheerful open smile, soft blush
    img_happy = Image.open(os.path.join(OUTPUT_DIR, "idle_blink.png"))
    img_happy = erase_original_mouth(img_happy)
    d = ImageDraw.Draw(img_happy)
    pts_smile = [(373, 257), (385, 258), (397, 257), (395, 269), (385, 272), (375, 269)]
    d.polygon(pts_smile, fill=MOUTH_CAVITY, outline=MOUTH_OUTLINE, width=2)
    d.polygon([(376, 258), (385, 259), (394, 258), (392, 262), (385, 262), (378, 262)], fill=TEETH_WHITE)
    d.chord([376, 265, 394, 272], start=0, end=180, fill=MOUTH_TONGUE)
    draw_anime_blush(d, intensity=1.1)
    img_happy.save(os.path.join(OUTPUT_DIR, "emotion_happy.png"))

    # 2. emotion_thinking (F8): Base eyes, wondering mouth
    img_think = erase_original_mouth(base.copy())
    d = ImageDraw.Draw(img_think)
    d.arc([380, 258, 390, 265], start=0, end=180, fill=MOUTH_OUTLINE, width=2)
    # Tiny curious highlight in right eye
    d.ellipse([428, 210, 432, 214], fill=(255, 255, 255, 240))
    img_think.save(os.path.join(OUTPUT_DIR, "emotion_thinking.png"))

    # 3. emotion_surprised (F7, F10): Round wide eyes, small 'o' mouth
    img_surp = erase_original_mouth(base.copy())
    d = ImageDraw.Draw(img_surp)
    d.ellipse([380, 256, 390, 267], fill=MOUTH_CAVITY, outline=MOUTH_OUTLINE, width=2)
    img_surp.save(os.path.join(OUTPUT_DIR, "emotion_surprised.png"))

    # 4. emotion_sad (F6): Gentle downturned mouth, tears on cheeks below eyes
    img_sad = erase_original_mouth(base.copy())
    d = ImageDraw.Draw(img_sad)
    d.arc([378, 259, 392, 269], start=20, end=160, fill=MOUTH_OUTLINE, width=2)
    # Tear drops placed naturally on the cheek planes
    tear_col = (140, 200, 255, 230)
    d.ellipse([342, 240, 346, 246], fill=tear_col)
    d.ellipse([422, 240, 426, 246], fill=tear_col)
    img_sad.save(os.path.join(OUTPUT_DIR, "emotion_sad.png"))

    # 5. emotion_shy (F2, F5): Deep rosy blush, bashful smile
    img_shy = erase_original_mouth(base.copy())
    d = ImageDraw.Draw(img_shy)
    draw_anime_blush(d, intensity=1.5)
    d.arc([379, 258, 391, 265], start=190, end=350, fill=MOUTH_OUTLINE, width=2)
    img_shy.save(os.path.join(OUTPUT_DIR, "emotion_shy.png"))

    # 6. emotion_annoyed (F3): Deadpan half-lidded eyes, straight horizontal pout line
    img_ann = Image.open(os.path.join(OUTPUT_DIR, "idle_half.png"))
    img_ann = erase_original_mouth(img_ann)
    d = ImageDraw.Draw(img_ann)
    d.line([(378, 260), (392, 260)], fill=MOUTH_OUTLINE, width=2)
    img_ann.save(os.path.join(OUTPUT_DIR, "emotion_annoyed.png"))

    # 7. emotion_smug (F9): Left eye wink, right eye open, cute :3 cat mouth
    img_smug = Image.open(os.path.join(OUTPUT_DIR, "idle_wink.png"))
    img_smug = erase_original_mouth(img_smug)
    d = ImageDraw.Draw(img_smug)
    d.arc([377, 257, 385, 264], start=190, end=350, fill=MOUTH_OUTLINE, width=2)
    d.arc([385, 257, 393, 264], start=190, end=350, fill=MOUTH_OUTLINE, width=2)
    draw_anime_blush(d, intensity=0.7)
    img_smug.save(os.path.join(OUTPUT_DIR, "emotion_smug.png"))

    # 8. emotion_sleepy (F11): Relaxed drowsy half-closed eyes, soft small mouth
    img_sleep = Image.open(os.path.join(OUTPUT_DIR, "idle_half.png"))
    img_sleep = erase_original_mouth(img_sleep)
    d = ImageDraw.Draw(img_sleep)
    d.ellipse([382, 259, 388, 264], fill=MOUTH_CAVITY, outline=MOUTH_OUTLINE, width=1)
    img_sleep.save(os.path.join(OUTPUT_DIR, "emotion_sleepy.png"))
    print("[FullBodyGen] Emotion frames generated.")

if __name__ == "__main__":
    generate_idle_frames()
    generate_mouth_frames()
    generate_walk_frames()
    generate_emotion_frames()
    print("[FullBodyGen] All 21 full-body anime sprite frames generated successfully!")
