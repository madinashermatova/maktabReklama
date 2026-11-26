"""Renders the school building exterior (kit pieces PIECE_school_building + PIECE_school_grounds) — the still that
becomes the website hero image in scene 1. Run INSIDE the kit file; nothing is saved back to it unless --save:

    blender -b blender/kit/school_kit.blend --python blender/scripts/kit_exterior_hero.py -- \
        [--res 50] [--samples 64] [--out renders/_kit/exterior/school_exterior.png] [--save path.blend] [--no-render]

Lens 24 mm (standard set), eye at 1.7 m — a parent's view walking up the entrance path, 3/4 to the facade.
Lighting: preset outdoor_day with the sun moved to the front-left (34° elevation, light raking across the facade); the sky is
re-synced to the sun so both agree.
"""

from __future__ import annotations

import math
import sys
import time
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as C  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default


res = int(arg("--res", "50"))
samples = int(arg("--samples", "64"))
out = C.ROOT / arg("--out", "renders/_kit/exterior/school_exterior.png")
cam_loc = tuple(float(v) for v in arg("--cam", "14,-34,1.7").split(","))
cam_aim = tuple(float(v) for v in arg("--aim", "-3,0,5.6").split(","))
lens = float(arg("--lens", "24"))
sun_el, sun_az = (float(v) for v in arg("--sun", "34,-125").split(","))

sc = bpy.context.scene
coll = bpy.data.collections.new("HERO_EXTERIOR")
sc.collection.children.link(coll)
for piece in ("school_building", "school_grounds"):
    ob = bpy.data.objects.new(f"{piece}.inst", None)
    ob.instance_type = "COLLECTION"
    ob.instance_collection = bpy.data.collections[f"PIECE_{piece}"]
    coll.objects.link(ob)

C.apply_render_settings(sc, samples=samples)
sc.render.resolution_percentage = res
C.apply_lighting_preset("outdoor_day")
sun = bpy.data.objects["SUN_outdoor_day"]
C.set_sun_direction(sun, sun_el, sun_az)
C.sync_sky_to_sun(bpy.data.worlds["W_outdoor_day"], sun)
# Outdoor daylight: slightly punchier tone curve than the neutral interior default
for look in ("AgX - Medium High Contrast", "Medium High Contrast"):
    try:
        sc.view_settings.look = look
        break
    except TypeError:
        pass
print(f"LOOK {sc.view_settings.look}")
for prop, val in (("fast_gi_distance", 6.0), ("clamp_surface_indirect", 10.0)):
    try:
        setattr(sc.eevee, prop, val)
    except (AttributeError, TypeError):
        pass

rig, cam, focus = C.make_camera_rig("HERO_RIG", lens=lens, location=cam_loc, focus_location=cam_aim, fstop=8.0)
C.look_at(rig, cam_aim)
cam.data.clip_end = 800.0
C.set_lens(cam, lens, allow_special=True)
sc.camera = cam

if arg("--save"):
    bpy.ops.wm.save_as_mainfile(filepath=str(C.ROOT / arg("--save")), copy=True)
    print(f"SAVED {arg('--save')}")

if "--no-render" not in argv:
    out.parent.mkdir(parents=True, exist_ok=True)
    sc.render.filepath = str(out)
    t0 = time.perf_counter()
    bpy.ops.render.render(write_still=True)
    print(f"HERO_RENDERED {time.perf_counter() - t0:.1f} s → {out}")
