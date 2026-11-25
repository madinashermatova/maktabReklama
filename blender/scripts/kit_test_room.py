"""Assembles a 9 × 6 m sample classroom from kit pieces (collection instances) and renders it per lighting preset.
Run INSIDE the kit file (nothing is saved back to it unless --save is given):

    blender -b blender/kit/school_kit.blend --python blender/scripts/kit_test_room.py -- \
        [--presets all | day_interior,warm_interior,...] [--res 50] [--samples 128] \
        [--out-dir renders/_kit/v2] [--suffix ""] [--no-probe] [--save renders/_kit/kit_test_room.blend] [--no-render]
"""

from __future__ import annotations

import math
import sys
import time
from pathlib import Path

import bmesh
import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as C  # noqa: E402
import build_kit as K  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default


presets_arg = arg("--presets", "all")
presets = list(C.LIGHTING_PRESETS) if presets_arg == "all" else presets_arg.split(",")
res = int(arg("--res", "100"))
samples = int(arg("--samples", "128"))
out_dir = C.ROOT / arg("--out-dir", "renders/_kit/v2")
suffix = arg("--suffix", "")
save_path = arg("--save")
use_probe = "--no-probe" not in argv

sc = bpy.context.scene
room = bpy.data.collections.new("TEST_ROOM")
sc.collection.children.link(room)
H, W, T = K.ROOM_HEIGHT, K.MODULE, K.WALL_T


def inst(piece, loc, rot_z_deg=0.0, name=None):
    ob = bpy.data.objects.new(name or f"{piece}.inst", None)
    ob.instance_type = "COLLECTION"
    ob.instance_collection = bpy.data.collections[f"PIECE_{piece}"]
    ob.location = loc
    ob.rotation_euler = (0, 0, math.radians(rot_z_deg))
    room.objects.link(ob)
    return ob


# Shell: 3 × 2 modules (x 0..9, y 0..6), windows on the x = 9 wall
for i in range(3):
    for j in range(2):
        inst("floor_area", (W * i, W * j, 0))
        inst("ceiling_panel", (W * i, W * j, H))
for i, piece in enumerate(("wall_segment", "door_frame", "wall_segment")):
    inst(piece, (W * i, 6.0, 0))
    if piece != "door_frame":
        inst("skirting", (W * i, 6.0, 0))
for i in range(3):
    inst("wall_segment", (W * (i + 1), 0.0, 0), 180)
    inst("skirting", (W * (i + 1), 0.0, 0), 180)
for j in range(2):
    inst("wall_segment", (0.0, W * j, 0), 90)
    inst("skirting", (0.0, W * j, 0), 90)
    inst("wall_window", (9.0, W * (j + 1), 0), -90)
    inst("skirting", (9.0, W * (j + 1), 0), -90)
for x, y in ((-T, -T), (9.0, -T), (-T, 6.0), (9.0, 6.0)):
    inst("corner_post", (x, y, 0))
inst("exterior_backdrop", (9.0 + T, 6.0, 0), -90)  # exterior (local +Y) → world +X

# Furniture: two rows of desks facing the whiteboard (left wall, x = 0) → students face −X
for k, (x, y) in enumerate(((3.4, 1.9), (3.4, 4.0), (5.6, 1.9), (5.6, 4.0))):
    inst("desk_double", (x, y, 0), -90, name=f"desk_{k}")
    for dy in (-0.32, 0.32):
        inst("chair", (x + 0.48, y + dy, 0), -90 + (3 if dy > 0 else -4), name=f"chair_{k}_{dy}")
inst("monitor", (3.30, 4.15, 0.76), 90 - 8, name="monitor_0")  # screen faces the students (+X)
# LED accent channel along the back wall top (wall-washer), and one under the whiteboard
inst("led_accent", (0.0, 5.93, 3.17), 0, name="accent_back")
inst("led_accent", (0.04, 1.5, 2.25), 90, name="accent_board")

mat = {m.name.removeprefix("KIT_"): m for m in bpy.data.materials if m.name.startswith("KIT_")}


def mesh_obj(name, bm, mats, smooth=False, bevel=0.004):
    return K.finish_object(name, bm, mats, room, bevel=bevel, smooth=smooth)


bm = bmesh.new()  # whiteboard on the left wall
K.add_box(bm, 0.0, 0.02, 1.5, 4.5, 0.95, 2.15)
mesh_obj("whiteboard", bm, [mat["board"]])
bm = bmesh.new()
for y0, y1, z0, z1 in ((1.48, 4.52, 0.93, 0.95), (1.48, 4.52, 2.15, 2.17), (1.48, 1.50, 0.95, 2.15), (4.50, 4.52, 0.95, 2.15)):
    K.add_box(bm, 0.0, 0.03, y0, y1, z0, z1)
K.add_box(bm, 0.0, 0.08, 1.6, 4.4, 0.91, 0.93)
mesh_obj("whiteboard_frame", bm, [mat["steel_brushed"]], bevel=0.002)
bm = bmesh.new()  # teal accent panel on the back wall
K.add_box(bm, 0.4, 2.6, 5.985, 6.0, 0.08, 3.2)
mesh_obj("accent_panel", bm, [mat["wall_accent"]], bevel=0.0)
bm = bmesh.new()  # teacher's desk
K.add_rounded_slab(bm, 1.2, 4.9, 0.7475, 1.4, 0.7, 0.025, 0.02)
mesh_obj("teacher_desk_top", bm, [mat["wood_dark"]], bevel=0.003)
bm = bmesh.new()
K.add_box(bm, 0.55, 0.6, 4.6, 5.2, 0.0, 0.735)
K.add_box(bm, 1.8, 1.85, 4.6, 5.2, 0.0, 0.735)
K.add_box(bm, 0.6, 1.8, 5.17, 5.2, 0.25, 0.735)
mesh_obj("teacher_desk_body", bm, [mat["wood_dark"]], bevel=0.003)

# Camera rig: back corner looking across the desks toward the windows and the door
rig, cam, focus = C.make_camera_rig("TEST_RIG", lens=24, location=(0.9, 0.7, 1.55),
                                    focus_location=(4.0, 3.2, 0.8), fstop=1.8)
C.look_at(rig, (6.2, 4.9, 1.2))
for ob in [o for o in bpy.data.objects if o.name.startswith("RIG")]:
    bpy.data.objects.remove(ob)
sc.camera = cam

C.apply_render_settings(sc, samples=samples)
sc.render.resolution_percentage = res

probe = None
if use_probe:
    # Irradiance volume: occlusion-aware bounce light (no light leaking, contact darkening)
    pd = bpy.data.lightprobes.new("ROOM_irradiance", "VOLUME")
    probe = bpy.data.objects.new("ROOM_irradiance", pd)
    probe.location = (4.5, 3.0, H / 2)
    probe.scale = (4.4, 2.9, H / 2 - 0.02)  # volume probes are 2 × 2 × 2 at scale 1
    for prop, val in (("resolution_x", 16), ("resolution_y", 11), ("resolution_z", 6), ("capture_world", True),
                      ("dilation_radius", 2.0), ("surface_bias", 0.1), ("escape_bias", 0.2)):
        if hasattr(pd, prop):
            setattr(pd, prop, val)
    room.objects.link(probe)

out_dir.mkdir(parents=True, exist_ok=True)


def bake_probe(preset=""):
    if probe is None or preset == "outdoor_day":  # exterior preset: the interior probe would leak darkness
        return 0.0
    t0 = time.perf_counter()
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = probe
    probe.select_set(True)
    try:
        bpy.ops.object.lightprobe_cache_bake(subset="ALL")
    except RuntimeError as e:
        print(f"PROBE_BAKE_FAILED {e}")
    return time.perf_counter() - t0


if save_path:
    C.apply_lighting_preset(presets[0])
    bake_probe()
    bpy.ops.wm.save_as_mainfile(filepath=str(C.ROOT / save_path), copy=True)
    print(f"SAVED {save_path}")

if "--no-render" not in argv:
    for p in presets:
        C.apply_lighting_preset(p)
        if probe is not None:
            probe.hide_render = p == "outdoor_day"
        tb = bake_probe(p)
        sc.render.filepath = str(out_dir / f"{p}{suffix}.png")
        t0 = time.perf_counter()
        bpy.ops.render.render(write_still=True)
        print(f"RENDERED {p}{suffix} bake {tb:.1f} s + render {time.perf_counter() - t0:.1f} s → {sc.render.filepath}")
