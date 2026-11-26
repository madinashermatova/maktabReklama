"""50 % overlay of the 3D replica render on the reference photo (camera-match check).

    tools/py.sh tools/overlay_match.py [--render renders/_entrance/entrance_match_960.png]
                                       [--photo assets/reference/entrance_front.jpg] [--out renders/_entrance/overlay_50_960.png]
Also writes overlay_edges_960.png: photo in grey with the render's edges in magenta (easier to judge alignment).
"""

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("--render", default="renders/_entrance/entrance_match_960.png")
ap.add_argument("--photo", default="assets/reference/entrance_front.jpg")
ap.add_argument("--out", default="renders/_entrance/overlay_50_960.png")
a = ap.parse_args()

r = Image.open(ROOT / a.render).convert("RGB")
p = Image.open(ROOT / a.photo).convert("RGB").resize(r.size, Image.LANCZOS)
Image.blend(p, r, 0.5).save(ROOT / a.out)
edges = np.asarray(r.convert("L").filter(ImageFilter.FIND_EDGES)).astype(float)
e = np.clip((edges - 18) / 40, 0, 1)[..., None]
grey = np.asarray(p.convert("L").convert("RGB")).astype(float) * 0.8
mix = grey * (1 - e) + np.array([255, 0, 255]) * e
Image.fromarray(mix.astype(np.uint8)).save(ROOT / a.out.replace("overlay_50", "overlay_edges"))
print("OVERLAY_OK", a.out)
