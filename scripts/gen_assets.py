#!/usr/bin/env python3
"""
Generate assets/demo.svg (animated terminal) and assets/arch.svg (pipeline diagram).
Run from the repo root: python3 scripts/gen_assets.py
"""

import os, textwrap

ASSETS = os.path.join(os.path.dirname(__file__), "..", "assets")
os.makedirs(ASSETS, exist_ok=True)

# ── colour palette (GitHub dark-mode friendly) ───────────────────────────────
BG      = "#0d1117"
CHROME  = "#161b22"
BORDER  = "#30363d"
CMD     = "#79c0ff"
MUTED   = "#6e7681"
NORMAL  = "#c9d1d9"
SAME    = "#3fb950"
VALID   = "#e3b341"
REG     = "#f85149"
DIFF    = "#d2a8ff"
HEADER  = "#58a6ff"
DIVIDER = "#8b949e"
SUB     = "#8b949e"


# ─────────────────────────────────────────────────────────────────────────────
# demo.svg  —  animated terminal recording
# ─────────────────────────────────────────────────────────────────────────────

TERMINAL_LINES = [
    # (delay_s, color, text)
    (0.3,  CMD,     "$ make run"),
    (0.9,  MUTED,   ""),
    (1.1,  HEADER,  "=== baseline  (openai/gpt-oss-20b) ==="),
    (1.4,  MUTED,   "  baseline/scenario_01/run1 → scenario_01_run1.json"),
    (1.55, MUTED,   "  baseline/scenario_02/run1 → scenario_02_run1.json"),
    (1.70, MUTED,   "  … 20 scenarios × 5 runs each …"),
    (1.90, MUTED,   ""),
    (2.0,  HEADER,  "=== replay  (openai/gpt-oss-safeguard-20b) ==="),
    (2.2,  MUTED,   "  replay/scenario_01/run1 → replay_scenario_01_run1.json"),
    (2.35, MUTED,   "  … 20 scenarios × 5 runs each …"),
    (2.55, MUTED,   ""),
    (2.70, SAME,    "scenario_01: SAME (SAME 5/5)"),
    (2.85, SUB,     "  run1:SAME  run2:SAME  run3:SAME  run4:SAME  run5:SAME"),
    (3.00, SAME,    "scenario_02: SAME (SAME 5/5)"),
    (3.15, SUB,     "  run1:SAME  run2:SAME  run3:SAME  run4:SAME  run5:SAME"),
    (3.30, VALID,   "scenario_03: VALID CHANGE (VALID CHANGE 5/5)"),
    (3.45, SUB,     "  run1:VALID CHANGE  run2:VALID CHANGE  run3:VALID CHANGE …"),
    (3.60, SAME,    "scenario_04: SAME (SAME 5/5)"),
    (3.75, SUB,     "  run1:SAME  run2:SAME  run3:SAME  run4:SAME  run5:SAME"),
    (3.90, VALID,   "scenario_07: VALID CHANGE (VALID CHANGE 5/5)"),
    (4.05, SUB,     "  run1:VALID CHANGE  run2:VALID CHANGE  run3:VALID CHANGE …"),
    (4.20, REG,     "scenario_11: REGRESSION (REGRESSION 4/5, SAME 1/5) ⚠ not stable"),
    (4.35, SUB,     "  run1:REGRESSION  run2:SAME  run3:REGRESSION  run4:REGRESSION …"),
    (4.55, MUTED,   ""),
    (4.65, DIVIDER, "── Summary ──────────────────────────────────"),
    (4.80, SAME,    "  SAME          14 / 20"),
    (4.95, VALID,   "  VALID CHANGE   3 / 20"),
    (5.10, REG,     "  REGRESSION     2 / 20"),
    (5.25, DIFF,    "  DIFFERENT      1 / 20"),
    (5.40, MUTED,   ""),
    (5.55, REG,     "── Suspicious reply warnings ────────────────"),
    (5.70, REG,     "  scenario_11/run3/baseline: reply mentions 'refunded' after failed call"),
    (6.00, MUTED,   ""),
]

TOTAL   = 8.5   # seconds per full loop (must be > last delay + 1)
FADE_S  = 0.6   # seconds to hold the full frame before wiping
W, H    = 820, 540
PAD_X   = 24
PAD_Y   = 54    # below chrome strip
LINE_H  = 18


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def gen_demo_svg():
    # All elements share the same dur=TOTAL and begin="0s".
    # Per-element keyTimes control when each line pops in and when the whole
    # frame wipes — this keeps the loop perfectly synchronised.
    fade_start = (TOTAL - FADE_S) / TOTAL  # all lines fade out together

    lines_svg = []
    for i, (delay, color, text) in enumerate(TERMINAL_LINES):
        y = PAD_Y + i * LINE_H
        t = esc(text) if text else "​"   # zero-width space keeps height
        a0 = max(0.0, delay / TOTAL)
        a1 = min(a0 + 0.01, fade_start - 0.01)   # snap-in
        a2 = min(a1 + 0.001, fade_start - 0.005)
        lines_svg.append(
            f'  <text x="{PAD_X}" y="{y}" fill="{color}" '
            f'font-family=\'Courier New\',monospace font-size="13" '
            f'opacity="0">'
            f'{t}'
            f'<animate attributeName="opacity" '
            f'values="0;0;1;1;0" '
            f'keyTimes="0;{a0:.4f};{a1:.4f};{fade_start:.4f};1" '
            f'dur="{TOTAL}s" begin="0s" '
            f'repeatCount="indefinite"/>'
            f'</text>'
        )

    n = len(TERMINAL_LINES)
    height = max(H, PAD_Y + n * LINE_H + 30)

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" viewBox="0 0 {W} {height}">
  <defs>
    <style>
      text {{ font-family: "Courier New", Consolas, monospace; font-size: 13px; }}
    </style>
  </defs>

  <!-- window background -->
  <rect width="{W}" height="{height}" rx="10" fill="{BG}"/>

  <!-- title bar chrome -->
  <rect width="{W}" height="34" rx="10" fill="{CHROME}"/>
  <rect y="20" width="{W}" height="14" fill="{CHROME}"/>
  <circle cx="18" cy="17" r="6" fill="#ff5f56"/>
  <circle cx="38" cy="17" r="6" fill="#ffbd2e"/>
  <circle cx="58" cy="17" r="6" fill="#27c93f"/>
  <text x="{W//2}" y="22" text-anchor="middle" fill="{MUTED}" font-size="11">
    mini-agent-regression-tester — make run
  </text>

  <!-- blinking cursor -->
  <rect x="{PAD_X}" y="{PAD_Y - 13}" width="8" height="14" fill="{CMD}" opacity="0.7">
    <animate attributeName="opacity" values="0.7;0;0.7" dur="1s" repeatCount="indefinite"/>
  </rect>

''' + "\n".join(lines_svg) + "\n</svg>\n"
    return svg


with open(os.path.join(ASSETS, "demo.svg"), "w") as f:
    f.write(gen_demo_svg())
print("✓  assets/demo.svg")


# ─────────────────────────────────────────────────────────────────────────────
# arch.svg  —  pipeline diagram
# ─────────────────────────────────────────────────────────────────────────────

def gen_arch_svg():
    W2, H2 = 760, 320

    # Layout (all hand-placed)
    # Row 0  y=50:   [Customer Message]
    # Row 1  y=130:  [Model A baseline]  [Model B changed]
    # Row 2  y=210:  [trace_N.json]  [replay_N.json]
    # Row 3  y=290:  [diff.py]
    # Row 4  y=370:  labels

    BOX_W, BOX_H = 160, 44
    ARROW = "#58a6ff"
    BOX_BG  = "#161b22"
    BOX_TXT = "#c9d1d9"
    ACCENT  = "#58a6ff"

    def box(x, y, label, sublabel="", accent=False):
        stroke = ACCENT if accent else BORDER
        lw = 1.5 if accent else 1
        sub = f'<text x="{x + BOX_W//2}" y="{y + 32}" text-anchor="middle" fill="{MUTED}" font-size="10">{esc(sublabel)}</text>' if sublabel else ""
        return (
            f'<rect x="{x}" y="{y}" width="{BOX_W}" height="{BOX_H}" rx="6" '
            f'fill="{BOX_BG}" stroke="{stroke}" stroke-width="{lw}"/>'
            f'<text x="{x + BOX_W//2}" y="{y + (18 if sublabel else 27)}" '
            f'text-anchor="middle" fill="{BOX_TXT}" font-size="13" font-weight="bold">{esc(label)}</text>'
            + sub
        )

    def arrow(x1, y1, x2, y2):
        return (
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{ARROW}" stroke-width="1.5" marker-end="url(#arr)"/>'
        )

    def label_pill(x, y, text, color):
        return (
            f'<rect x="{x}" y="{y}" width="130" height="28" rx="14" fill="{color}" opacity="0.15"/>'
            f'<text x="{x+65}" y="{y+19}" text-anchor="middle" fill="{color}" font-size="12" font-weight="bold">{esc(text)}</text>'
        )

    CX = W2 // 2
    # positions
    msg_x = CX - BOX_W // 2;  msg_y = 20
    ma_x  = CX - BOX_W - 40;  ma_y  = 110
    mb_x  = CX + 40;           mb_y  = 110
    ta_x  = CX - BOX_W - 40;  ta_y  = 200
    tb_x  = CX + 40;           tb_y  = 200
    diff_x= CX - BOX_W // 2;  diff_y= 285

    pills_y = 365
    pill_positions = [
        (CX - 290, pills_y, "SAME",         SAME),
        (CX - 145, pills_y, "VALID CHANGE", VALID),
        (CX +   5, pills_y, "REGRESSION",   REG),
        (CX + 150, pills_y, "DIFFERENT",    DIFF),
    ]

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W2}" height="420" viewBox="0 0 {W2} 420">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="{ARROW}"/>
    </marker>
    <style>text {{ font-family: -apple-system, "Segoe UI", sans-serif; }}</style>
  </defs>
  <rect width="{W2}" height="420" fill="{BG}" rx="12"/>

  <!-- customer message -->
  {box(msg_x, msg_y, "Customer message", accent=True)}

  <!-- split arrow down-left and down-right -->
  {arrow(CX, msg_y + BOX_H, CX, msg_y + BOX_H + 10)}
  <line x1="{CX}" y1="{msg_y + BOX_H + 10}" x2="{ma_x + BOX_W//2}" y2="{msg_y + BOX_H + 10}" stroke="{ARROW}" stroke-width="1.5"/>
  <line x1="{CX}" y1="{msg_y + BOX_H + 10}" x2="{mb_x + BOX_W//2}" y2="{msg_y + BOX_H + 10}" stroke="{ARROW}" stroke-width="1.5"/>
  {arrow(ma_x + BOX_W//2, msg_y + BOX_H + 10, ma_x + BOX_W//2, ma_y)}
  {arrow(mb_x + BOX_W//2, msg_y + BOX_H + 10, mb_x + BOX_W//2, mb_y)}

  <!-- model boxes -->
  {box(ma_x, ma_y, "Model A", "baseline")}
  {box(mb_x, mb_y, "Model B", "changed version")}

  <!-- trace boxes -->
  {arrow(ma_x + BOX_W//2, ma_y + BOX_H, ta_x + BOX_W//2, ta_y)}
  {arrow(mb_x + BOX_W//2, mb_y + BOX_H, tb_x + BOX_W//2, tb_y)}
  {box(ta_x, ta_y, "scenario_N.json", "baseline trace")}
  {box(tb_x, tb_y, "replay_N.json", "replay trace")}

  <!-- converge to diff.py -->
  <line x1="{ta_x + BOX_W//2}" y1="{ta_y + BOX_H}" x2="{ta_x + BOX_W//2}" y2="{ta_y + BOX_H + 10}" stroke="{ARROW}" stroke-width="1.5"/>
  <line x1="{tb_x + BOX_W//2}" y1="{tb_y + BOX_H}" x2="{tb_x + BOX_W//2}" y2="{tb_y + BOX_H + 10}" stroke="{ARROW}" stroke-width="1.5"/>
  <line x1="{ta_x + BOX_W//2}" y1="{ta_y + BOX_H + 10}" x2="{CX}" y2="{ta_y + BOX_H + 10}" stroke="{ARROW}" stroke-width="1.5"/>
  <line x1="{tb_x + BOX_W//2}" y1="{tb_y + BOX_H + 10}" x2="{CX}" y2="{tb_y + BOX_H + 10}" stroke="{ARROW}" stroke-width="1.5"/>
  {arrow(CX, ta_y + BOX_H + 10, CX, diff_y)}
  {box(diff_x, diff_y, "diff.py", "classify per scenario × run", accent=True)}

  <!-- label pills -->
  {arrow(CX, diff_y + BOX_H, CX, pills_y - 10)}
  {"".join(label_pill(x, y, t, c) for x, y, t, c in pill_positions)}
</svg>
'''
    return svg


with open(os.path.join(ASSETS, "arch.svg"), "w") as f:
    f.write(gen_arch_svg())
print("✓  assets/arch.svg")
