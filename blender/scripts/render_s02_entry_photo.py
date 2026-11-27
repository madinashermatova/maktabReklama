"""Renders the scene-2 entry photo layer (D hand-off 1 → 2) from the APPROVED replica, without changing it:
ENTRANCE_PROJ in blender/kit/entrance.blend → renders/s02_turnstile_proj/####.png (RGBA, straight alpha), frames
270 … S02_BEATS.dissolveEnd. Remotion lays it over the scene-2 render (<S02EntryPhoto>); `npm run sync` publishes it.

    "C:\\Program Files\\Blender Foundation\\Blender 5.3\\blender.exe" -b blender/kit/entrance.blend \
        --python blender/scripts/render_s02_entry_photo.py -- [--preview]

The saved entrance.blend lost the projector-depth image of the PROJ_photo material (the build script assigned it
after its own renders; the image did not persist), so the depth test fails and the layer renders empty. The depth map
itself was rendered by the approved build (renders/_entrance/proj_depth.exr); it is re-attached here for this render
only — the .blend is never saved.
"""

from __future__ import annotations

import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as C  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
PREVIEW = "--preview" in argv
tl = C.load_timeline()
F0 = C.get_scene_def("s02_turnstile")["from"]
F_END = tl["s02"]["beats"]["dissolveEnd"]
DEPTH = C.RENDERS_DIR / "_entrance" / "proj_depth.exr"
OUT = C.RENDERS_DIR / "s02_turnstile_proj"

if not DEPTH.exists():
    raise SystemExit(f"Missing {DEPTH} (rendered by build_entrance.py)")
sc = bpy.data.scenes["ENTRANCE_PROJ"]
mat = bpy.data.materials["PROJ_photo"]
empty = [n for n in mat.node_tree.nodes if n.type == "TEX_IMAGE" and n.image is None]
if len(empty) != 1:
    raise SystemExit(f"Expected exactly one empty image node (projector depth) in PROJ_photo, found {len(empty)}")
img = bpy.data.images.load(str(DEPTH), check_existing=True)
img.colorspace_settings.name = "Non-Color"
empty[0].image = img

bpy.context.window.scene = sc
sc.render.resolution_percentage = tl["previewPercentage"] if PREVIEW else 100
sc.eevee.taa_render_samples = tl["previewSamples"] if PREVIEW else 16
sc.render.film_transparent = True
sc.render.image_settings.color_mode = "RGBA"
OUT.mkdir(parents=True, exist_ok=True)
for f in range(F0, F_END + 1):
    sc.frame_set(f)
    sc.render.filepath = str(OUT / f"{f:04d}")
    bpy.ops.render.render(write_still=True, scene=sc.name)
print(f"ENTRY_PHOTO {F0}–{F_END} → {OUT}")
