"""Scene 1 website hero image: the REAL entrance photo with only the sky replaced (CLAUDE.md → HONESTY RULES).

    tools/py.sh tools/hero_sky.py [--src assets/reference/entrance_front.jpg] [--out-dir renders/_hero]

Steps
 1. Lanczos upscale 1280 → 1920 px wide (no AI, no invented detail).
 2. Matte: colour classification into sure-sky / sure-foreground / unknown, in two zones only —
    the upper sky (purple/pink, connected to the top edge, signboard excluded) and the orange sky seen through
    the gate opening. Edge pixels (roof edges, canopy tubes and cables, pipes, antenna, tree branches, the
    street-light pole and wires) get a fractional alpha by colour UNMIXING against local sky / foreground
    colour estimates, so the old purple/orange fringe is removed instead of left as a halo.
 3. New sky: clear morning sky (procedural gradient + a few soft fBm clouds, light from the right like the
    sun on the buildings). Composite:  out = I − α·S_old + α·S_new.
 4. Slight colour match of the foreground to the new sky: magenta/orange spill reflected by the white canopy
    tubes and the area behind the gate is reduced, tiny global cool shift. The signboard (box + glow) is
    excluded from every edit.
Outputs: entrance_hero_1920.png, entrance_matte_1920.png, before_960.png, after_960.png, before_after_960.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("--src", default="assets/reference/entrance_front.jpg")
ap.add_argument("--out-dir", default="renders/_hero")
ap.add_argument("--seed", type=int, default=5)
args = ap.parse_args()

src = Image.open(ROOT / args.src).convert("RGB")
W = 1920
SCALE = W / src.width
H = round(src.height * SCALE)
big = src.resize((W, H), Image.LANCZOS)
I = np.asarray(big).astype(np.float32) / 255.0
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)


def box(x0, y0, x1, y1):
    """Box in ORIGINAL photo pixel coords → boolean mask at output resolution."""
    return (xx >= x0 * SCALE) & (xx < x1 * SCALE) & (yy >= y0 * SCALE) & (yy < y1 * SCALE)


def rgb_to_hsv(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx, mn = a.max(-1), a.min(-1)
    d = mx - mn + 1e-6
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) / 6.0
    s = np.where(mx > 1e-6, (mx - mn) / (mx + 1e-6), 0)
    return h % 1.0, s, mx


h, s, v = rgb_to_hsv(I)

# ---- zones (original-photo coordinates, measured on a gridded copy)
# signboard incl. its lit top edge (thin lavender highlight), measured on 3× zooms: y 219 at x 300 → y 216 at x 900
SIGN = box(268, 200, 930, 292) & (yy >= (219.0 - (xx / SCALE - 300.0) * 0.005) * SCALE)
UPPER = (yy < 300 * SCALE) & ~SIGN
GATE = box(412, 312, 818, 396)  # opening under the canopy beam, above the gate/booth

# ---- classification
purple = ((h > 0.55) | (h < 0.02))
up_sky = UPPER & purple & (s >= 0.30) & (v >= 0.35)
up_fg = UPPER & ((s < 0.16) | (v < 0.30) | ((h > 0.03) & (h < 0.5)))
or_sky = GATE & (h > 0.05) & (h < 0.12) & (s >= 0.55) & (v >= 0.86)
or_fg = GATE & ((s < 0.42) | (v < 0.70) | (h > 0.14) & (h < 0.9))
sure_sky = up_sky | or_sky
sure_fg = ~(UPPER | GATE) | up_fg | or_fg | SIGN
sure_fg &= ~sure_sky

# keep only sky regions connected to the top edge (upper) or lying in the gate opening
lab, n = ndi.label(sure_sky | ((UPPER | GATE) & ~sure_fg))
sizes = ndi.sum(np.ones_like(lab), lab, index=np.arange(n + 1))
# sky = components touching the top edge, lying in the gate opening, or large regions in the upper zone
# (the sky between the canopy rails is cut off from the top edge by the rail tubes)
keep = set(np.unique(lab[0, :])) | set(np.unique(lab[GATE])) | {i for i in range(1, n + 1) if sizes[i] > 1500 * SCALE**2}
keep.discard(0)
connected = np.isin(lab, list(keep))
sure_sky &= connected


def norm_conv(mask, img, sigma):
    m = mask.astype(np.float32)
    w = ndi.gaussian_filter(m, sigma)
    out = np.stack([ndi.gaussian_filter(img[..., c] * m, sigma) for c in range(3)], -1)
    return out / np.maximum(w, 1e-4)[..., None], w


S_old, ws = norm_conv(sure_sky, I, 14 * SCALE)
F_est, wf = norm_conv(sure_fg & (ndi.distance_transform_edt(~sure_sky) < 12 * SCALE), I, 3.0 * SCALE)

# unmixing band: unknown pixels + pixels within 2.5 px (orig) of the other class
near_sky = ndi.distance_transform_edt(~sure_sky) <= 2.5 * SCALE
near_fg = ndi.distance_transform_edt(~sure_fg) <= 2.5 * SCALE
band = connected & ((~sure_sky & ~sure_fg) | (sure_sky & near_fg) | (sure_fg & near_sky & ~SIGN))
d = S_old - F_est
den = (d * d).sum(-1)
a_unmix = np.clip(((I - F_est) * d).sum(-1) / np.maximum(den, 1e-4), 0, 1)
alpha = sure_sky.astype(np.float32)
use = band & (den > 0.01)
alpha[use] = a_unmix[use]
alpha[band & ~use] = 0.5 * sure_sky[band & ~use]
alpha[SIGN] = 0.0
alpha = np.clip(ndi.gaussian_filter(alpha, 0.6), 0, 1) * (alpha > 0.02)

# ---- new sky: clear morning, a few soft clouds; light from the right (sun on the right like the buildings show)
rng = np.random.default_rng(args.seed)
ty = yy / (360 * SCALE)  # 0 at top → 1 near the horizon behind the gate
zen = np.array([0.20, 0.42, 0.78])
hor = np.array([0.80, 0.88, 0.95])
t = np.clip(ty, 0, 1) ** 1.35
sky = zen * (1 - t[..., None]) + hor * t[..., None]
sky *= (0.96 + 0.08 * (xx / W))[..., None]  # brighter toward the sun side


def fbm(octaves, base, aspect=2.6):
    acc = np.zeros((H, W), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        gh = max(2, int(base * 2 ** o))
        gw = max(2, int(base * 2 ** o * W / H / aspect))  # fewer columns → horizontally stretched clouds
        g = rng.standard_normal((gh, gw)).astype(np.float32)
        acc += amp * np.asarray(Image.fromarray(g).resize((W, H), Image.BICUBIC))
        tot += amp
        amp *= 0.5
    return acc / tot


nz = fbm(6, 2.0)
nz = (nz - nz.mean()) / nz.std()
cover = np.clip((nz - 0.55) / 0.9, 0, 1) ** 1.3  # sparse: a few soft clouds
cover *= np.clip(1.25 - ty, 0, 1)  # thinner toward the horizon
detail = fbm(5, 8.0, 1.8)
cover = np.clip(cover * (0.85 + 0.3 * detail), 0, 1)
lit = np.clip(0.5 + 0.5 * (np.roll(cover, -int(6 * SCALE), 1) - np.roll(cover, int(6 * SCALE), 0)), 0, 1)
cloud_col = np.array([0.97, 0.97, 0.98]) * (0.9 + 0.1 * lit[..., None]) - np.array([0.08, 0.06, 0.03]) * (1 - lit[..., None]) * cover[..., None]
S_new = sky * (1 - 0.85 * cover[..., None]) + cloud_col * (0.85 * cover[..., None])
# behind the gate the view is close to the horizon: soft hazy morning white-blue
S_new = np.where(GATE[..., None], hor * 0.98 + 0.02, S_new)
S_new = np.clip(S_new, 0, 1)

out = np.clip(I - alpha[..., None] * S_old + alpha[..., None] * S_new, 0, 1)

# ---- slight colour match of the foreground (signboard excluded, feathered)
SIGN_PAD = box(262, 200, 936, 298) & (yy >= (219.0 - (xx / SCALE - 300.0) * 0.005 - 4.0) * SCALE)
excl = np.maximum(SIGN.astype(np.float32), np.clip(ndi.gaussian_filter(SIGN_PAD.astype(np.float32), 3 * SCALE) * 1.6, 0, 1))
fg_w = (1 - alpha) * (1 - excl)
ho, so, vo = rgb_to_hsv(out)
grey = out.mean(-1, keepdims=True)
spill_mag = UPPER & (ho > 0.72) & (ho < 0.98)  # pink/violet reflected by white tubes, cables, roof edges
spill_or = GATE & (ho > 0.04) & (ho < 0.12)
k = np.zeros((H, W), np.float32)
k[spill_mag] = 0.65
k[spill_or] = 0.35
k = ndi.gaussian_filter(k, 1.0 * SCALE) * fg_w
out = out * (1 - k[..., None]) + (grey * np.array([0.99, 1.0, 1.02])) * k[..., None]
cool = np.array([0.985, 1.0, 1.02])
out = out * (1 + (cool - 1) * fg_w[..., None])
out = np.clip(out, 0, 1)

od = ROOT / args.out_dir
od.mkdir(parents=True, exist_ok=True)
res = Image.fromarray((out * 255 + 0.5).astype(np.uint8))
res.save(od / "entrance_hero_1920.png")
Image.fromarray((alpha * 255 + 0.5).astype(np.uint8)).save(od / "entrance_matte_1920.png")
b960 = src.resize((960, 540), Image.LANCZOS)
a960 = res.resize((960, 540), Image.LANCZOS)
b960.save(od / "before_960.png")
a960.save(od / "after_960.png")
pair = Image.new("RGB", (960, 1100), (20, 20, 20))
pair.paste(b960, (0, 0))
pair.paste(a960, (0, 560))
ImageDraw.Draw(pair).text((8, 542), "BEFORE (original)            AFTER (sky replaced, 1920 px master)", fill=(230, 230, 230))
pair.save(od / "before_after_960.png")
# changed-pixel check: the signboard must be bit-identical to the upscaled original
sign_diff = np.abs(out[SIGN] - I[SIGN]).max()
print(f"HERO_SKY_OK {W}x{H} sky_px={int((alpha > 0.5).sum())} sign_max_diff={sign_diff:.5f} → {od}")
