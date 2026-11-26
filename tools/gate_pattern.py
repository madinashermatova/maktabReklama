"""Tileable laser-cut panel masks for the entrance replica (white = metal, black = cut-out hole).

    tools/py.sh tools/gate_pattern.py

Pattern: classic 8-fold star-and-cross lattice (8-point stars on a square grid, cross-shaped openings between
them, small square piercings), the family of geometric ornament seen on the real gate and booth doors in
assets/reference/entrance_front.jpg. Decorative geometry only — not a symbol or emblem.
Outputs assets/textures/gate_pattern.png (1024², 4 × 4 repeats) and booth_glass_pattern.png (finer, etched glass).
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "textures"
OUT.mkdir(parents=True, exist_ok=True)


def star(cx, cy, r_out, r_in, n=8, rot=math.pi / 8):
    pts = []
    for k in range(2 * n):
        r = r_out if k % 2 == 0 else r_in
        a = rot + k * math.pi / n
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def panel(size=1024, reps=4, ss=3):
    S = size * ss
    T = S / reps
    im = Image.new("L", (S, S), 255)  # metal
    d = ImageDraw.Draw(im)
    for i in range(-1, reps + 2):
        for j in range(-1, reps + 2):
            cx, cy = i * T, j * T
            d.polygon(star(cx, cy, 0.40 * T, 0.24 * T), fill=0)  # star opening
            d.polygon(star(cx, cy, 0.17 * T, 0.10 * T), fill=255)  # metal rosette inside the star
            d.ellipse([cx - 0.045 * T, cy - 0.045 * T, cx + 0.045 * T, cy + 0.045 * T], fill=0)
            # cross opening at the cell centre
            mx, my = cx + T / 2, cy + T / 2
            a, b = 0.21 * T, 0.065 * T
            d.rectangle([mx - a, my - b, mx + a, my + b], fill=0)
            d.rectangle([mx - b, my - a, mx + b, my + a], fill=0)
            d.rectangle([mx - 0.03 * T, my - 0.03 * T, mx + 0.03 * T, my + 0.03 * T], fill=255)
            # small square piercings on the cell edges between stars
            for ex, ey in ((cx + T / 2, cy), (cx, cy + T / 2)):
                q = 0.05 * T
                d.polygon([(ex, ey - q), (ex + q, ey), (ex, ey + q), (ex - q, ey)], fill=0)
    return im.filter(ImageFilter.GaussianBlur(ss * 0.6)).resize((size, size), Image.LANCZOS)


panel(1024, 4).save(OUT / "gate_pattern.png")
panel(1024, 6).save(OUT / "booth_glass_pattern.png")
print("PATTERNS_OK", OUT)
