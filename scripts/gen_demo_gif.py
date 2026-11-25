#!/usr/bin/env python3
"""
Generate assets/demo.gif — an animated terminal recording using Pillow.
Run from the repo root: python3 scripts/gen_demo_gif.py
"""

import os
from PIL import Image, ImageDraw, ImageFont

ASSETS = os.path.join(os.path.dirname(__file__), "..", "assets")
os.makedirs(ASSETS, exist_ok=True)

FONT_PATH = "/System/Library/Fonts/SFNSMono.ttf"
FONT_SIZE = 14

# colour palette
BG      = (13,  17,  23)
CHROME  = (22,  27,  34)
BORDER  = (48,  54,  61)
CMD     = (121, 192, 255)
MUTED   = (110, 118, 129)
NORMAL  = (201, 209, 217)
SAME    = ( 63, 185,  80)
VALID   = (227, 179,  65)
REG     = (248,  81,  73)
DIFF    = (210, 168, 255)
HEADER  = ( 88, 166, 255)
DIVIDER = (139, 148, 158)
SUB     = (139, 148, 158)
DOT_RED = (255,  95,  86)
DOT_YEL = (255, 189,  46)
DOT_GRN = ( 39, 201,  63)

LINES = [
    # (color, text)
    (CMD,     "$ make run"),
    (MUTED,   ""),
    (HEADER,  "=== baseline  (openai/gpt-oss-20b) ==="),
    (MUTED,   "  baseline/scenario_01/run1 → scenario_01_run1.json"),
    (MUTED,   "  baseline/scenario_02/run1 → scenario_02_run1.json"),
    (MUTED,   "  ... 20 scenarios x 5 runs each ..."),
    (MUTED,   ""),
    (HEADER,  "=== replay  (openai/gpt-oss-safeguard-20b) ==="),
    (MUTED,   "  replay/scenario_01/run1 → replay_scenario_01_run1.json"),
    (MUTED,   "  ... 20 scenarios x 5 runs each ..."),
    (MUTED,   ""),
    (SAME,    "scenario_01: SAME (SAME 5/5)"),
    (SUB,     "  run1:SAME  run2:SAME  run3:SAME  run4:SAME  run5:SAME"),
    (SAME,    "scenario_02: SAME (SAME 5/5)"),
    (SUB,     "  run1:SAME  run2:SAME  run3:SAME  run4:SAME  run5:SAME"),
    (VALID,   "scenario_03: VALID CHANGE (VALID CHANGE 5/5)"),
    (SUB,     "  run1:VALID CHANGE  run2:VALID CHANGE  run3:VALID CHANGE ..."),
    (SAME,    "scenario_04: SAME (SAME 5/5)"),
    (SUB,     "  run1:SAME  run2:SAME  run3:SAME  run4:SAME  run5:SAME"),
    (REG,     "scenario_11: REGRESSION (REGRESSION 4/5, SAME 1/5)  not stable"),
    (SUB,     "  run1:REGRESSION  run2:SAME  run3:REGRESSION  run4:REGRESSION ..."),
    (MUTED,   ""),
    (DIVIDER, "── Summary ──────────────────────────────────"),
    (SAME,    "  SAME          14 / 20"),
    (VALID,   "  VALID CHANGE   3 / 20"),
    (REG,     "  REGRESSION     2 / 20"),
    (DIFF,    "  DIFFERENT      1 / 20"),
    (MUTED,   ""),
    (REG,     "── Suspicious reply warnings ─────────────────"),
    (REG,     "  scenario_11/run3: reply mentions 'refunded' after failed call"),
]

W          = 760
PAD_X      = 20
PAD_Y      = 48      # first line baseline
LINE_H     = 20
CHROME_H   = 34
HOLD_MS    = 150     # ms per new line
PAUSE_MS   = 3000    # ms to hold the finished frame
FADE_MS    = 600     # ms for the fade-out (spread over N_FADE frames)
N_FADE     = 8


def make_base_image(font):
    n = len(LINES)
    height = PAD_Y + n * LINE_H + 20
    img = Image.new("RGB", (W, height), BG)
    draw = ImageDraw.Draw(img)
    # chrome bar
    draw.rectangle([0, 0, W, CHROME_H], fill=CHROME)
    # dots
    draw.ellipse([12, 12, 24, 24], fill=DOT_RED)
    draw.ellipse([32, 12, 44, 24], fill=DOT_YEL)
    draw.ellipse([52, 12, 64, 24], fill=DOT_GRN)
    # title
    title = "mini-agent-regression-tester — make run"
    bbox = font.getbbox(title)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, 10), title, font=font, fill=MUTED)
    return img, height


def render_lines(draw, font, up_to: int):
    for i, (color, text) in enumerate(LINES[:up_to]):
        y = PAD_Y + i * LINE_H
        if text:
            draw.text((PAD_X, y), text, font=font, fill=color)


def blend(img, ratio):
    """Blend image toward BG by ratio (0=original, 1=all BG)."""
    bg = Image.new("RGB", img.size, BG)
    return Image.blend(img, bg, ratio)


def main():
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    base_img, height = make_base_image(font)

    frames = []
    durations = []

    # --- build up line by line ---
    for n in range(1, len(LINES) + 1):
        img = base_img.copy()
        draw = ImageDraw.Draw(img)
        render_lines(draw, font, n)
        frames.append(img)
        durations.append(HOLD_MS)

    # --- hold the finished frame ---
    frames[-1] = frames[-1].copy()
    durations[-1] = PAUSE_MS

    # --- fade out to blank ---
    full_frame = frames[-1].copy()
    for k in range(1, N_FADE + 1):
        ratio = k / N_FADE
        faded = blend(full_frame, ratio)
        frames.append(faded)
        durations.append(FADE_MS // N_FADE)

    out = os.path.join(ASSETS, "demo.gif")
    frames[0].save(
        out,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=False,
    )
    print(f"✓  assets/demo.gif  ({len(frames)} frames, {sum(durations)/1000:.1f}s loop)")


if __name__ == "__main__":
    main()
