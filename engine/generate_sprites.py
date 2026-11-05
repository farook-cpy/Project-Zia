"""
Project Zia - Master Anime PNG Sprite Asset Generator
Produces high-resolution, perfectly aligned cel-shaded sprite frames for Zia:
- Idle animations (open, half-blink, happy closed blink, wink)
- Talking lip-sync frames (closed, half, open, rounded 'o', smile)
- 4-phase shoulder/head walk cycle with hair physics
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

LEFT_EYE_POLY = [
    (350, 408), (368, 376), (392, 356), (416, 354), (438, 368), (460, 396), (468, 414),
    (456, 434), (430, 444), (408, 446), (386, 444), (362, 434)
]
RIGHT_EYE_POLY = [
    (540, 408), (558, 376), (582, 356), (606, 354), (628, 368), (650, 396), (658, 414),
    (646, 434), (620, 444), (598, 446), (576, 444), (552, 434)
]

def restore_bangs(target_img):
    """Restores foreground hair bangs above y=376."""
    arr_orig = np.array(base_orig)
    arr_target = np.array(target_img)
    patch_orig = arr_orig[320:376, 320:680]
    is_hair = (patch_orig[:, :, 0] < 140) & (patch_orig[:, :, 1] < 100) & (patch_orig[:, :, 2] < 90) & (patch_orig[:, :, 3] > 200)
    arr_target[320:376, 320:680][is_hair] = patch_orig[is_hair]
    return Image.fromarray(arr_target)

def generate_eye_sprites():
    # 1. idle_open
    base_orig.save(os.path.join(OUTPUT_DIR, "idle_open.png"))

    # 2. idle_blink (Happy ^ ^)
    img_blink = base_orig.copy()
    draw = ImageDraw.Draw(img_blink)
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
    draw.arc([370, 368, 446, 398], start=195, end=345, fill=CREASE, width=2)
    draw.arc([562, 368, 638, 398], start=195, end=345, fill=CREASE, width=2)
    img_blink = restore_bangs(img_blink)
    img_blink.save(os.path.join(OUTPUT_DIR, "idle_blink.png"))

    # 3. idle_half (Half-closed eyelid for smooth transition)
    img_half = base_orig.copy()
    draw = ImageDraw.Draw(img_half)
    half_left_poly = [(352, 406), (370, 376), (392, 356), (416, 354), (438, 368), (460, 396), (466, 410), (440, 410), (408, 412), (375, 410)]
    half_right_poly = [(542, 406), (560, 376), (582, 356), (606, 354), (628, 368), (650, 396), (656, 410), (630, 410), (598, 412), (565, 410)]
    draw.polygon(half_left_poly, fill=SKIN_UPPER)
    draw.polygon(half_right_poly, fill=SKIN_UPPER)
    for w in range(4):
        draw.line([(352, 406 + w), (408, 412 + w), (466, 410 + w)], fill=DARK_LASH, width=2)
        draw.line([(542, 406 + w), (598, 412 + w), (656, 410 + w)], fill=DARK_LASH, width=2)
    img_half = restore_bangs(img_half)
    img_half.save(os.path.join(OUTPUT_DIR, "idle_half.png"))

    # 4. idle_wink (Left wink, right sparkling open)
    img_wink = base_orig.copy()
    draw = ImageDraw.Draw(img_wink)
    draw.polygon(LEFT_EYE_POLY, fill=SKIN_UPPER)
    draw.chord([362, 400, 456, 446], start=0, end=180, fill=SKIN_LOWER)
    for w in range(5):
        draw.arc([354, 388 + w, 464, 432 + w], start=190, end=350, fill=DARK_LASH, width=2)
    draw.line([(354, 410), (344, 402)], fill=DARK_LASH, width=3)
    draw.line([(464, 410), (474, 404)], fill=DARK_LASH, width=3)
    draw.arc([370, 368, 446, 398], start=195, end=345, fill=CREASE, width=2)
    # Cute twinkle star
    cx, cy = 345, 386
    draw.polygon([(cx, cy-8), (cx+3, cy-3), (cx+8, cy), (cx+3, cy+3), (cx, cy+8), (cx-3, cy+3), (cx-8, cy), (cx-3, cy-3)], fill=(255, 235, 110, 255))
    img_wink = restore_bangs(img_wink)
    img_wink.save(os.path.join(OUTPUT_DIR, "idle_wink.png"))
    print("[SpriteGen] Eye sprites generated.")

def generate_mouth_sprites():
    LIP_DARK = (52, 22, 20, 255)
    MOUTH_CAVITY = (156, 42, 50, 255)
    MOUTH_DEEP = (98, 20, 28, 255)
    TEETH = (255, 255, 255, 255)
    TONGUE = (238, 122, 130, 255)

    # 1. talk_closed
    base_orig.save(os.path.join(OUTPUT_DIR, "talk_closed.png"))

    # 2. talk_half (Mouth slightly open)
    img_half = base_orig.copy()
    draw = ImageDraw.Draw(img_half)
    poly_half = [
        (478, 524), (490, 526), (505, 527), (520, 526), (534, 524),
        (530, 535), (518, 541), (505, 543), (492, 541), (482, 535)
    ]
    draw.polygon(poly_half, fill=MOUTH_CAVITY, outline=LIP_DARK)
    draw.polygon([(482, 525), (505, 527), (528, 525), (522, 530), (505, 531), (488, 530)], fill=TEETH)
    draw.chord([492, 534, 518, 546], start=0, end=180, fill=TONGUE)
    draw.line([(470, 522), (490, 525), (505, 527), (520, 525), (542, 522)], fill=LIP_DARK, width=3)
    img_half.save(os.path.join(OUTPUT_DIR, "talk_half.png"))

    # 3. talk_open (Mouth wide open for vowels)
    img_open = base_orig.copy()
    draw = ImageDraw.Draw(img_open)
    poly_open = [
        (472, 523), (485, 526), (505, 527), (525, 526), (538, 523),
        (532, 540), (520, 548), (505, 551), (490, 548), (478, 540)
    ]
    draw.polygon(poly_open, fill=MOUTH_CAVITY, outline=LIP_DARK)
    draw.polygon([(476, 524), (505, 528), (534, 524), (524, 534), (486, 534)], fill=MOUTH_DEEP)
    draw.polygon([(480, 524), (505, 528), (530, 524), (522, 532), (505, 534), (488, 532)], fill=TEETH)
    draw.chord([486, 537, 524, 554], start=0, end=180, fill=TONGUE)
    draw.line([(470, 522), (485, 525), (505, 527), (525, 525), (542, 522)], fill=LIP_DARK, width=3)
    img_open.save(os.path.join(OUTPUT_DIR, "talk_open.png"))

    # 4. talk_o (Cute rounded small mouth)
    img_o = base_orig.copy()
    draw = ImageDraw.Draw(img_o)
    draw.ellipse([490, 520, 520, 544], fill=MOUTH_CAVITY, outline=LIP_DARK, width=3)
    draw.ellipse([494, 522, 516, 535], fill=MOUTH_DEEP)
    draw.ellipse([497, 522, 513, 527], fill=TEETH)
    img_o.save(os.path.join(OUTPUT_DIR, "talk_o.png"))

    # 5. talk_smile (Cheerful wide beaming smile)
    img_smile = base_orig.copy()
    draw = ImageDraw.Draw(img_smile)
    poly_smile = [
        (468, 521), (485, 525), (505, 526), (525, 525), (544, 521),
        (538, 539), (524, 548), (505, 552), (486, 548), (474, 539)
    ]
    draw.polygon(poly_smile, fill=MOUTH_CAVITY, outline=LIP_DARK)
    draw.polygon([(474, 523), (505, 527), (536, 523), (528, 533), (505, 535), (482, 533)], fill=TEETH)
    draw.chord([484, 537, 526, 554], start=0, end=180, fill=TONGUE)
    draw.line([(466, 521), (485, 525), (505, 526), (525, 525), (546, 521)], fill=LIP_DARK, width=3)
    img_smile.save(os.path.join(OUTPUT_DIR, "talk_smile.png"))
    print("[SpriteGen] Mouth sprites generated.")

def generate_walk_sprites():
    arr_base = np.array(base_orig)
    h, w = arr_base.shape[:2]

    def make_walk(angle_deg, shift_x, shift_y, hair_sway):
        pivot = (512, 650)
        M = cv2.getRotationMatrix2D(pivot, angle_deg, 1.0)
        M[0, 2] += shift_x
        M[1, 2] += shift_y
        warped = cv2.warpAffine(arr_base, M, (w, h), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))

        if abs(hair_sway) > 0.5:
            shift_M = np.float32([[1, 0, hair_sway], [0, 1, 0]])
            # Left tail
            left_mask = np.zeros((h, w), dtype=np.uint8)
            cv2.ellipse(left_mask, (220, 720), (100, 180), 15, 0, 360, 255, -1)
            left_tail = cv2.bitwise_and(warped, warped, mask=left_mask)
            shifted_left = cv2.warpAffine(left_tail, shift_M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0,0))

            # Right tail
            right_mask = np.zeros((h, w), dtype=np.uint8)
            cv2.ellipse(right_mask, (800, 720), (100, 180), -15, 0, 360, 255, -1)
            right_tail = cv2.bitwise_and(warped, warped, mask=right_mask)
            shifted_right = cv2.warpAffine(right_tail, shift_M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0,0))

            mask_both = cv2.bitwise_or(left_mask, right_mask)
            inv_mask = cv2.bitwise_not(mask_both)
            body = cv2.bitwise_and(warped, warped, mask=inv_mask)
            warped = cv2.add(body, cv2.add(shifted_left, shifted_right))

        return Image.fromarray(warped)

    make_walk(0.0, 0, 0, 0).save(os.path.join(OUTPUT_DIR, "walk_0.png"))
    make_walk(-2.2, -4, 8, 4.5).save(os.path.join(OUTPUT_DIR, "walk_1.png"))
    make_walk(0.0, 0, -6, -2.0).save(os.path.join(OUTPUT_DIR, "walk_2.png"))
    make_walk(2.2, 4, 8, -4.5).save(os.path.join(OUTPUT_DIR, "walk_3.png"))
    print("[SpriteGen] Walk sprites generated.")

if __name__ == "__main__":
    generate_eye_sprites()
    generate_mouth_sprites()
    generate_walk_sprites()
    print("[SpriteGen] All master anime PNG sprites generated successfully!")
