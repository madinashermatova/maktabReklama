"""Checks PIECE_slab: renders the S-pass cut frame (camera at slab_HANDOFF, looking straight down, 24 mm) under two
very different lighting presets and reports the pixel difference — the cut must look identical in every scene.
Also renders an inspection view of the cavity. Run inside the kit file:

    blender -b blender/kit/school_kit.blend --python blender/scripts/kit_slab_test.py -- [--res 50] [--samples 16]
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as C  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
res = int(argv[argv.index("--res") + 1]) if "--res" in argv else 50
samples = int(argv[argv.index("--samples") + 1]) if "--samples" in argv else 16
out_dir = C.RENDERS_DIR / "_kit" / "slab"
out_dir.mkdir(parents=True, exist_ok=True)

sc = bpy.context.scene
slab = bpy.data.objects.new("slab.inst", None)
slab.instance_type = "COLLECTION"
slab.instance_collection = bpy.data.collections["PIECE_slab"]
sc.collection.objects.link(slab)
probe = C.add_slab_probe(slab)

C.apply_render_settings(sc, samples=samples)
sc.render.resolution_percentage = res
rig, cam, focus = C.make_camera_rig("SLAB_RIG", lens=24)
cam.data.dof.use_dof = False  # storyboard: DOF off during the pass
anchor = C.slab_handoff_matrix(slab)
rig.location = anchor.translation
rig.rotation_euler = (0, 0, 0)  # looking straight down (−Z), image up = +Y
sc.camera = cam


def bake():
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = probe
    probe.select_set(True)
    bpy.ops.object.lightprobe_cache_bake(subset="ALL")


import numpy as np  # noqa: E402


results = {}
for preset in ("day_interior", "tech_dark"):
    C.apply_lighting_preset(preset)
    C.key_slab_isolation(5, 20)  # as a scene would around its S cut
    sc.frame_set(10)
    bake()
    path = out_dir / f"slab_cut_{preset}.png"
    sc.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(str(path))
    results[preset] = np.array(img.pixels[:]).reshape(-1, 4)[:, :3]
    print(f"SLAB_CUT {preset} mean {results[preset].mean():.4f}")
diff = np.abs(results["day_interior"] - results["tech_dark"])
print(f"SLAB_DIFF mean {diff.mean() * 255:.2f}/255  max {diff.max() * 255:.1f}/255")

# Inspection view: a few frames before the cut (just under the top deck), wider so the cavity reads
rig.location = anchor.translation + C.Vector((0.0, -0.9, 0.3))
C.look_at(rig, anchor.translation + C.Vector((0.3, 0.6, -0.45)))
sc.render.filepath = str(out_dir / "slab_cavity_inspect.png")
bpy.ops.render.render(write_still=True)
print("SLAB_INSPECT done")
