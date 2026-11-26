"""Composites the 1→2 hand-off: projected-photo layer (RGBA, exact photo pixels) over the 3D beauty pass.

    tools/py.sh tools/composite_handoff.py [--frames 270 285 300] [--dir renders/_entrance]

final = beauty · (1 − α) + photo · α   (straight alpha from ENTRANCE_PROJ). Same operation Remotion will do in the
assembly (two image sequences, the projection layer on top). Writes handoff_final_<frame>.png and
handoff_strip_960.png (start | middle | end, labelled) plus handoff_alpha_strip.png (where the photo is still used).
"""

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("--frames", type=int, nargs="+", default=[270, 285, 300])
ap.add_argument("--dir", default="renders/_entrance")
a = ap.parse_args()
d = ROOT / a.dir
finals, alphas = [], []
for f in a.frames:
    beauty = Image.open(d / f"handoff_beauty_{f:04d}.png").convert("RGB")
    proj = Image.open(d / f"handoff_proj_{f:04d}.png").convert("RGBA").resize(beauty.size, Image.LANCZOS)
    b = np.asarray(beauty).astype(np.float32) / 255
    p = np.asarray(proj).astype(np.float32) / 255
    al = p[..., 3:4]
    out = b * (1 - al) + p[..., :3] * al
    img = Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8))
    img.save(d / f"handoff_final_{f:04d}.png")
    finals.append(img)
    alphas.append(Image.fromarray((al[..., 0] * 255).astype(np.uint8)).convert("RGB"))
    print(f"frame {f}: photo coverage {float(al.mean()) * 100:.1f} %")


def strip(images, labels, name, w=640):
    h = round(w * images[0].height / images[0].width)
    s = Image.new("RGB", (w * len(images), h + 22), (18, 18, 18))
    dr = ImageDraw.Draw(s)
    for i, (im, lab) in enumerate(zip(images, labels)):
        s.paste(im.resize((w, h), Image.LANCZOS), (i * w, 22))
        dr.text((i * w + 8, 5), lab, fill=(235, 235, 235))
    s.save(d / name)


labels = [f"{tag} — frame {f}" for tag, f in zip(("START (photo)", "MIDDLE", "END (3D)"), a.frames)]
strip(finals, labels, "handoff_strip_960.png")
strip(alphas, [f"photo alpha {f}" for f in a.frames], "handoff_alpha_strip.png")
print("HANDOFF_OK", d / "handoff_strip_960.png")
