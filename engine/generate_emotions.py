"""
Project Zia - Master Anime Emotion Sprite Generator
Generates dedicated high-resolution emotion sprite frames:
- emotion_happy.png     (F4: Beaming smile, happy curved eyes, sparkle blush)
- emotion_thinking.png  (F8: Thoughtful gaze up-right, curious head tilt, pondering mouth)
- emotion_surprised.png (F7/F10: Wide sparkling eyes, cute gasp mouth, surprised blush)
- emotion_sad.png       (F6: Sympathetic eyes, concerned brow, gentle comforted pout)
- emotion_shy.png       (F2/F5: Deep rosy blush, bashful glance down, sweet smile)
- emotion_annoyed.png   (F3: Cute anime pout, furrowed brow, huff cheeks)
- emotion_smug.png      (F9: Playful wink, cat mouth :3, confident glint)
- emotion_sleepy.png    (F11: Heavy relaxed eyelids, peaceful soft smile)
"""

import os
import cv2
import numpy as np
from PIL import Image, ImageDraw

OUTPUT_DIR = "assets/sprites/zia_anime"
os.makedirs(OUTPUT_DIR, exist_ok=True)

BASE_PATH = os.path.join(OUTPUT_DIR, "base_clean.png")
base_orig = Image.open(BASE_PATH).convert("RGBA")
W, H = base_orig.size

SKIN_UPPER = (255, 236, 222, 255)
SKIN_LOWER = (252, 212, 202, 255)
DARK_LASH = (62, 26, 22, 255)
CREASE = (235, 178, 162, 255)
ROSY_BLUSH = (248, 142, 148, 200)
LIP_DARK = (52, 22, 20, 255)
MOUTH_CAVITY = (156, 42, 50, 255)
MOUTH_DEEP = (98, 20, 28, 255)
TEETH = (255, 255, 255, 255)
TONGUE = (238, 122, 130, 255)

LEFT_EYE_POLY = [
    (350, 408), (368, 376), (392, 356), (416, 354), (438, 368), (460, 396), (468, 414),
    (456, 434), (430, 444), (408, 446), (386, 444), (362, 434)
]
RIGHT_EYE_POLY = [
    (540, 408), (558, 376), (582, 356), (606, 354), (628, 368), (650, 396), (658, 414),
    (646, 434), (620, 444), (598, 446), (576, 444), (552, 434)
]

def restore_bangs(target_img):
    """Restores foreground hair bangs strictly above y=376."""
    arr_orig = np.array(base_orig)
    arr_target = np.array(target_img)
    patch_orig = arr_orig[320:376, 320:680]
    is_hair = (patch_orig[:, :, 0] < 140) & (patch_orig[:, :, 1] < 100) & (patch_orig[:, :, 2] < 90) & (patch_orig[:, :, 3] > 200)
    arr_target[320:376, 320:680][is_hair] = patch_orig[is_hair]
    return Image.fromarray(arr_target)

def draw_sparkle(draw, cx, cy, radius=7, color=(255, 240, 150, 255)):
    draw.polygon([
        (cx, cy - radius), (cx + radius*0.35, cy - radius*0.35),
        (cx + radius, cy), (cx + radius*0.35, cy + radius*0.35),
        (cx, cy + radius), (cx - radius*0.35, cy + radius*0.35),
        (cx - radius, cy), (cx - radius*0.35, cy - radius*0.35)
    ], fill=color)

def generate_all_emotions():
    # 1. EMOTION: HAPPY (F4)
    # Beaming open eyes ^ ^ + happy wide smile + cheek sparkles
    img_happy = base_orig.copy()
    draw = ImageDraw.Draw(img_happy)
    # Eyes closed in happy arch
    draw.polygon(LEFT_EYE_POLY, fill=SKIN_UPPER)
    draw.polygon(RIGHT_EYE_POLY, fill=SKIN_UPPER)
    draw.chord([362, 400, 456, 446], start=0, end=180, fill=SKIN_LOWER)
    draw.chord([552, 400, 646, 446], start=0, end=180, fill=SKIN_LOWER)
    for w in range(5):
        draw.arc([354, 388 + w, 464, 432 + w], start=190, end=350, fill=DARK_LASH, width=2)
        draw.arc([544, 388 + w, 654, 432 + w], start=190, end=350, fill=DARK_LASH, width=2)
    draw.line([(354, 410), (344, 402)], fill=DARK_LASH, width=3)
    draw.line([(464, 410), (474, 404)], fill=DARK_LASH, width=3)
    draw.line([(544, 410), (534, 404)], fill=DARK_LASH, width=3)
    draw.line([(654, 410), (664, 402)], fill=DARK_LASH, width=3)
    # Wide beaming smile
    poly_smile = [
        (468, 521), (485, 525), (505, 526), (525, 525), (544, 521),
        (538, 540), (524, 549), (505, 553), (486, 549), (474, 540)
    ]
    draw.polygon(poly_smile, fill=MOUTH_CAVITY, outline=LIP_DARK)
    draw.polygon([(474, 523), (505, 527), (536, 523), (528, 533), (505, 535), (482, 533)], fill=TEETH)
    draw.chord([484, 537, 526, 554], start=0, end=180, fill=TONGUE)
    draw.line([(466, 521), (485, 525), (505, 526), (525, 525), (546, 521)], fill=LIP_DARK, width=3)
    # Cute cheek sparkles
    draw_sparkle(draw, 340, 460, 6)
    draw_sparkle(draw, 665, 460, 6)
    img_happy = restore_bangs(img_happy)
    img_happy.save(os.path.join(OUTPUT_DIR, "emotion_happy.png"))

    # 2. EMOTION: THINKING (F8)
    # Gaze tilted upward/rightward + thoughtful head tilt + small wondering mouth
    arr_base = np.array(base_orig)
    h, w = arr_base.shape[:2]
    # Subtle curious tilt (+1.8 deg)
    M_tilt = cv2.getRotationMatrix2D((512, 650), 1.8, 1.0)
    tilted = cv2.warpAffine(arr_base, M_tilt, (w, h), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0,0))
    img_think = Image.fromarray(tilted)
    draw = ImageDraw.Draw(img_think)
    # Shift eye pupils upward and slightly right:
    # Cover lower 40% of eye opening with skin to create focused squint
    draw.chord([360, 395, 458, 442], start=0, end=180, fill=SKIN_LOWER)
    draw.chord([550, 395, 648, 442], start=0, end=180, fill=SKIN_LOWER)
    for w in range(3):
        draw.line([(362, 412+w), (408, 416+w), (454, 412+w)], fill=DARK_LASH, width=2)
        draw.line([(552, 412+w), (598, 416+w), (644, 412+w)], fill=DARK_LASH, width=2)
    # Cute wondering mouth (slight sideways pout)
    draw.ellipse([490, 522, 516, 532], fill=(255, 230, 220, 255))
    draw.line([(486, 526), (502, 524), (520, 527)], fill=LIP_DARK, width=3)
    draw.chord([496, 526, 512, 532], start=0, end=180, fill=(240, 140, 145, 255))
    # Thinking sparkle over head
    draw_sparkle(draw, 580, 260, 9, (255, 255, 180, 255))
    draw_sparkle(draw, 605, 240, 5, (255, 255, 210, 255))
    img_think.save(os.path.join(OUTPUT_DIR, "emotion_thinking.png"))

    # 3. EMOTION: SURPRISED / SHOCKED (F7 / F10)
    # Wide eyes + cute small gasp 'o' mouth + blush
    img_surp = base_orig.copy()
    draw = ImageDraw.Draw(img_surp)
    # Cute open 'o' mouth
    draw.ellipse([490, 518, 520, 545], fill=MOUTH_CAVITY, outline=LIP_DARK, width=3)
    draw.ellipse([494, 521, 516, 536], fill=MOUTH_DEEP)
    draw.ellipse([496, 520, 514, 526], fill=TEETH)
    # Highlight lines near temples
    draw.line([(310, 360), (290, 350)], fill=(120, 140, 220, 240), width=3)
    draw.line([(314, 375), (294, 370)], fill=(120, 140, 220, 240), width=3)
    draw.line([(700, 360), (720, 350)], fill=(120, 140, 220, 240), width=3)
    draw.line([(696, 375), (716, 370)], fill=(120, 140, 220, 240), width=3)
    img_surp.save(os.path.join(OUTPUT_DIR, "emotion_surprised.png"))

    # 4. EMOTION: SAD / SYMPATHETIC (F6)
    # Concerned drooping brows + gentle down-turned lip
    img_sad = base_orig.copy()
    draw = ImageDraw.Draw(img_sad)
    # Cover top outer corners of eyes with gentle eyelid droop
    draw.polygon([(350, 368), (380, 358), (410, 372), (370, 386)], fill=SKIN_UPPER)
    draw.polygon([(658, 368), (628, 358), (598, 372), (638, 386)], fill=SKIN_UPPER)
    draw.line([(350, 368), (385, 382)], fill=DARK_LASH, width=3)
    draw.line([(658, 368), (623, 382)], fill=DARK_LASH, width=3)
    # Concerned mouth curve (downturned)
    draw.ellipse([475, 520, 535, 538], fill=(255, 232, 220, 255))
    draw.arc([476, 524, 534, 544], start=195, end=345, fill=LIP_DARK, width=3)
    img_sad = restore_bangs(img_sad)
    img_sad.save(os.path.join(OUTPUT_DIR, "emotion_sad.png"))

    # 5. EMOTION: SHY / BLUSH (F2 / F5)
    # Rich rosy anime blush across cheeks and nose + bashful gaze
    img_shy = base_orig.copy()
    draw = ImageDraw.Draw(img_shy)
    # Extra warm blush ovals on cheeks
    blush_color = (252, 130, 140, 130)
    # Left cheek blush
    for r in range(25, 0, -3):
        draw.ellipse([345 - r, 450 - int(r*0.6), 345 + r, 450 + int(r*0.6)], fill=(255, 120, 135, 28))
    # Right cheek blush
    for r in range(25, 0, -3):
        draw.ellipse([660 - r, 450 - int(r*0.6), 660 + r, 450 + int(r*0.6)], fill=(255, 120, 135, 28))
    # Nose bridge blush bar
    draw.chord([480, 450, 530, 466], start=0, end=180, fill=(255, 130, 145, 50))
    # Bashful cute smile
    draw.line([(480, 525), (496, 529), (514, 529), (530, 525)], fill=LIP_DARK, width=3)
    draw.chord([496, 528, 514, 536], start=0, end=180, fill=(245, 130, 140, 255))
    img_shy = restore_bangs(img_shy)
    img_shy.save(os.path.join(OUTPUT_DIR, "emotion_shy.png"))

    # 6. EMOTION: ANNOYED / POUT (F3)
    # Cute anime pout: furrowed brows, cute huff pout mouth
    img_annoyed = base_orig.copy()
    draw = ImageDraw.Draw(img_annoyed)
    # Inner brow furrow (/ \)
    draw.line([(370, 342), (410, 355)], fill=DARK_LASH, width=4)
    draw.line([(638, 342), (598, 355)], fill=DARK_LASH, width=4)
    # Pout mouth (puffed upward center)
    draw.ellipse([475, 520, 535, 538], fill=(255, 230, 220, 255))
    draw.line([(482, 527), (496, 523), (514, 523), (528, 527)], fill=LIP_DARK, width=3)
    draw.chord([496, 523, 514, 532], start=180, end=360, fill=(240, 120, 130, 255))
    # Little cute huff puff cloud
    draw.ellipse([540, 505, 560, 520], fill=(245, 245, 255, 220), outline=(180, 180, 200, 220), width=1)
    draw.ellipse([555, 500, 575, 515], fill=(245, 245, 255, 220), outline=(180, 180, 200, 220), width=1)
    img_annoyed = restore_bangs(img_annoyed)
    img_annoyed.save(os.path.join(OUTPUT_DIR, "emotion_annoyed.png"))

    # 7. EMOTION: SMUG / PLAYFUL (F9)
    # Left wink + cat mouth :3 + confident smirk
    img_smug = base_orig.copy()
    draw = ImageDraw.Draw(img_smug)
    # Left wink
    draw.polygon(LEFT_EYE_POLY, fill=SKIN_UPPER)
    draw.chord([362, 400, 456, 446], start=0, end=180, fill=SKIN_LOWER)
    for w in range(5):
        draw.arc([354, 388 + w, 464, 432 + w], start=190, end=350, fill=DARK_LASH, width=2)
    draw.line([(354, 410), (344, 402)], fill=DARK_LASH, width=3)
    draw.line([(464, 410), (474, 404)], fill=DARK_LASH, width=3)
    # Cat mouth :3 (two subtle curved arches)
    draw.ellipse([470, 518, 540, 538], fill=(255, 232, 220, 255))
    draw.arc([478, 520, 506, 536], start=0, end=180, fill=LIP_DARK, width=3)
    draw.arc([504, 520, 532, 536], start=0, end=180, fill=LIP_DARK, width=3)
    # Gold star sparkle near wink
    draw_sparkle(draw, 345, 386, 8, (255, 235, 110, 255))
    img_smug = restore_bangs(img_smug)
    img_smug.save(os.path.join(OUTPUT_DIR, "emotion_smug.png"))

    # 8. EMOTION: SLEEPY / RELAXED (F11)
    # Heavy 60% drooped eyelids, calm soft resting smile
    img_sleepy = base_orig.copy()
    draw = ImageDraw.Draw(img_sleepy)
    draw.polygon([(348, 360), (416, 354), (466, 380), (462, 416), (410, 420), (354, 416)], fill=SKIN_UPPER)
    draw.polygon([(538, 360), (606, 354), (656, 380), (652, 416), (600, 420), (544, 416)], fill=SKIN_UPPER)
    draw.chord([362, 404, 456, 436], start=0, end=180, fill=SKIN_LOWER)
    draw.chord([552, 404, 646, 436], start=0, end=180, fill=SKIN_LOWER)
    for w in range(4):
        draw.line([(354, 414 + w), (408, 419 + w), (462, 415 + w)], fill=DARK_LASH, width=2)
        draw.line([(544, 414 + w), (598, 419 + w), (652, 415 + w)], fill=DARK_LASH, width=2)
    # Gentle calm mouth
    draw.line([(485, 526), (505, 528), (525, 526)], fill=LIP_DARK, width=2)
    # Little 'z' bubbles floating up
    draw.text((640, 280), "z", fill=(180, 195, 235, 220), font_size=18)
    draw.text((660, 255), "Z", fill=(180, 195, 235, 240), font_size=24)
    img_sleepy = restore_bangs(img_sleepy)
    img_sleepy.save(os.path.join(OUTPUT_DIR, "emotion_sleepy.png"))

    print("[EmotionGen] All 8 master emotion sprites generated successfully!")

if __name__ == "__main__":
    generate_all_emotions()
