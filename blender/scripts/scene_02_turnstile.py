"""Scene 2 — "Turnstile with Face ID" (film frames 270–509) → blender/scenes/s02_turnstile.blend

    "C:\\Program Files\\Blender Foundation\\Blender 5.3\\blender.exe" -b --python blender/scripts/scene_02_turnstile.py -- [--no-bake]

Prerequisite: `npm run faceid:render` (renders/_faceid/####.png, the terminal display). Entry photo layer: render_s02_entry_photo.py. Beats: S02_BEATS in
src/timeline.ts (via blender/timeline.json) — no frame numbers are hard-coded here.

Real layout (user, 2026-11-27): the school has ONE Face ID turnstile, at the entrance, in the passage between the
laser-cut gate and the guard booth (qorovul xonasi); the building straight ahead after the turnstile is the school
CAFETERIA with a glass facade. Built on the APPROVED photo-matched entrance replica (blender/kit/entrance.blend,
appended; the gate stays closed) with two deliberate replacements (user, 2026-11-27): the courtyard building's
door / barred windows / wall AC units → the cafeteria glass wall + furnished interior (blender/scripts/kit_cafeteria.py,
shared with scene 8), and the low-poly potted palms → modelled potted palms (blender/scripts/kit_plants.py); plus the
kit slab.
  * 270–300  D hand-off: the camera path, lens (18 mm + the photo's lens shift) and geometry equal entrance.blend's
             CAM_S02_START, so the ENTRANCE_PROJ photo layer (rendered from entrance.blend) lies exactly on this render
  * 300–358  the camera glides toward the guard booth, 18 → 85 mm, exact stop on the Face ID terminal
  * 362–391  scan on the terminal display (Remotion texture: abstract dot lattice only), red → green; LEDs red → green
  * 395–420  the glass wing swings open; the camera passes through the lane beside the booth
  * 420–470  slow, calm glide into the courtyard toward the glass cafeteria, past the potted palms (level, 24 mm)
  * 460–509  it tilts down to the paving and sinks into it (smooth accelerating dive) into the slab under it: EXIT S
             matched to scene 3's existing ENTRY (same kit slab, same anchor — scene 3 is not re-rendered)
Verticals stay vertical: the camera pitch is locked level until the final tilt into the paving (tiltStart);
vertical framing uses lens shift only.

INVENTED (no photo shows it; neutral — listed in docs/status.md): the turnstile's design (one stainless cabinet +
one glass wing + a Face ID terminal on a post; the real one is confirmed beside the booth, its model is not
photographed) and its automatic opening; the cafeteria's glass-wall details and interior (no photo of it).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as C  # noqa: E402
import build_kit as K  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
NO_BAKE = "--no-bake" in argv

SCENE_ID = "s02_turnstile"
SD = C.get_scene_def(SCENE_ID)
F0, F1 = SD["from"], SD["end"]  # 270, 509
B = C.load_timeline()["s02"]["beats"]
ENTRANCE = C.KIT_DIR / "entrance.blend"
KIT = C.KIT_DIR / "school_kit.blend"
FACEID_DIR = C.RENDERS_DIR / "_faceid"

# --------------------------------------------------------------------------- scene, replica, kit
C.reset_scene()
sc = C.setup_scene(SCENE_ID, samples=64)

with bpy.data.libraries.load(str(ENTRANCE), link=False) as (src, dst):
    dst.collections = ["ENTRANCE_REPLICA"]
    dst.worlds = ["W_entrance_morning"]
sc.collection.children.link(bpy.data.collections["ENTRANCE_REPLICA"])
sc.world = bpy.data.worlds["W_entrance_morning"]
for other in [s for s in bpy.data.scenes if s != sc]:  # never carry the replica's own scenes along
    bpy.data.scenes.remove(other)

# Sign glow: the approved replica's compositor (build_entrance.py ENT_COMPOSITE: Bloom, threshold 1.6, strength 0.55,
# size 0.55), rebuilt here so its Render Layers node points at this scene.
ng = bpy.data.node_groups.new("S02_COMPOSITE", "CompositorNodeTree")
ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
rl = ng.nodes.new("CompositorNodeRLayers")
rl.scene = sc
gl = ng.nodes.new("CompositorNodeGlare")
for t_ in ("Bloom", "Fog Glow"):
    try:
        gl.inputs["Type"].default_value = t_
        break
    except TypeError:
        pass
for k_, v_ in (("Threshold", 1.6), ("Strength", 0.55), ("Size", 0.55), ("Saturation", 1.0)):
    if k_ in gl.inputs:
        gl.inputs[k_].default_value = v_
go = ng.nodes.new("NodeGroupOutput")
ng.links.new(rl.outputs["Image"], gl.inputs["Image"])
ng.links.new(gl.outputs[0], go.inputs[0])
sc.compositing_node_group = ng
sc.render.use_compositing = True

# The replica's scene-2 start camera defines the hand-off framing (18 mm + lens shift); read it, then drop its cameras.
cam_ref = bpy.data.objects["CAM_S02_START"]
sc.frame_set(F0)  # evaluate its baked hand-off path at the first frame (matrix_world is stale right after append)
bpy.context.view_layer.update()
REF_LENS, REF_SHIFT = cam_ref.data.lens, (cam_ref.data.shift_x, cam_ref.data.shift_y)
REF_LOC = cam_ref.matrix_world.translation.copy()
_ref_rot = cam_ref.matrix_world.to_euler()
assert abs(REF_LOC.z - 1.4) < 1e-3 and abs(_ref_rot.x - math.radians(90)) < 1e-4 and abs(_ref_rot.z) < 1e-4, (REF_LOC, _ref_rot)
for n in ("CAM_S02_START", "CAM_PHOTO_MATCH"):
    bpy.data.objects.remove(bpy.data.objects[n])
for n in ("gate_frame", "booth_body", "booth_roof", "passage_soffit", "courtyard_facade", "courtyard_coping_plinth"):
    assert n in bpy.data.objects, n

with bpy.data.libraries.load(str(KIT), link=False) as (src, dst):
    dst.collections = ["PIECE_slab"]
kit_root = bpy.data.collections.new("KIT_pieces")
sc.collection.children.link(kit_root)
kit_root.children.link(bpy.data.collections["PIECE_slab"])
bpy.context.view_layer.layer_collection.children["KIT_pieces"].exclude = True

ts = bpy.data.collections.new("TURNSTILE")
sc.collection.children.link(ts)
OB = bpy.data.objects


def bounds(ob):
    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return Vector([min(v[i] for v in bb) for i in range(3)]), Vector([max(v[i] for v in bb) for i in range(3)])


def box(bm, x0, x1, y0, y1, z0, z1, mi=0):
    K.add_box(bm, min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1), min(z0, z1), max(z0, z1), mi)


def obj(name, bm, mats, bevel=0.0, smooth=False, coll=None):
    return K.finish_object(name, bm, mats, coll or ts, bevel=bevel, smooth=smooth)


def key_rot_z(ob, frames, angle_fn):
    for f in frames:
        ob.rotation_euler.z = angle_fn(f)
        ob.keyframe_insert("rotation_euler", index=2, frame=f)
    for fc in C.fcurves_of(ob):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"  # every frame keyed


def swing(t, overshoot):
    """Motorised swing: eased start, a small physical overshoot, settles with zero speed (t in 0..1)."""
    return C.ease_out_back(C.ease_in_out_sine(t), overshoot)


# --------------------------------------------------------------------------- measured replica geometry
g_lo, g_hi = bounds(OB["gate_frame"])
b_lo, b_hi = bounds(OB["booth_body"])
GATE_X1, GATE_Y1 = g_hi.x, g_hi.y  # right end of the (closed) gate leaves (−0.64), gate plane back face (8.56)
BOOTH_Y1 = b_hi.y  # back wall of the booth (10.88)
BOOTH_X0 = b_lo.x  # left side wall of the guard booth (0.22): the passage is GATE_X1 … BOOTH_X0 (0.86 m)

# --------------------------------------------------------------------------- courtyard building → the glass cafeteria (user, 2026-11-27)
import random  # noqa: E402

import kit_cafeteria as KC  # noqa: E402
import kit_plants as KP  # noqa: E402

f_lo, f_hi = bounds(OB["courtyard_facade"])  # x −12 … 4, y 16.5 … 16.8, h 3.6
M_render = OB["courtyard_facade"].data.materials[0]  # the replica's courtyard render (end walls, fascia)
for n in ("courtyard_facade", "courtyard_door_leaves", "courtyard_door_arch", "courtyard_window_glass",
          "courtyard_window_grilles", "courtyard_ac_units", "courtyard_ac_fans", "courtyard_ac_pipes", "courtyard_interior",
          "palm_leaflets", "palm_stems"):
    bpy.data.objects.remove(OB[n])
cp = OB["courtyard_coping_plinth"]  # keep the roof slab + coping, drop the plinth band under the old wall
bm = bmesh.new()
bm.from_mesh(cp.data)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if (cp.matrix_world @ v.co).z < 1.0], context="VERTS")
bm.to_mesh(cp.data)
bm.free()
CAF_Y = f_lo.y + 0.02  # outer glass line ≈ the old wall face
CAF_H = f_hi.z  # 3.6 (roof slab underside)
GLAZE_TOP = CAF_H - 0.3  # plaster fascia band above the glazing
caf = bpy.data.collections.new("CAFETERIA")
sc.collection.children.link(caf)
MC = KC.materials()
bm = bmesh.new()  # fascia band + the two end walls in the replica's render
box(bm, f_lo.x - 0.05, f_hi.x + 0.05, CAF_Y - 0.04, CAF_Y + 0.3, GLAZE_TOP, CAF_H)
for x0_, x1_ in ((f_lo.x - 0.05, f_lo.x + 0.25), (f_hi.x - 0.25, f_hi.x + 0.05)):
    box(bm, x0_, x1_, CAF_Y - 0.04, CAF_Y + 5.05, 0.0, CAF_H)
obj("cafeteria_fascia_endwalls", bm, [M_render], coll=caf, bevel=0.003)
CAF_DOOR_X = KC.glass_wall(caf, MC, f_lo.x + 0.25, f_hi.x - 0.25, CAF_Y, 0.0, GLAZE_TOP, door_x=-4.5)  # old doorway axis
KC.interior(caf, MC, f_lo.x + 0.25, f_hi.x - 0.25, CAF_Y + 0.2, CAF_Y + 5.0, CAF_H - 0.32, random.Random(8),
            counter_x=(-9.5, -5.5))
cpd = bpy.data.lightprobes.new("CAF_irradiance", "VOLUME")
cprobe = bpy.data.objects.new("CAF_irradiance", cpd)
cprobe.location = ((f_lo.x + f_hi.x) / 2, CAF_Y + 2.6, CAF_H / 2)
cprobe.scale = ((f_hi.x - f_lo.x) / 2 - 0.4, 2.3, CAF_H / 2 - 0.2)
caf.objects.link(cprobe)

# --------------------------------------------------------------------------- potted palms (modelled, replace the low-poly ones)
PM = KP.palm_materials()
plants = bpy.data.collections.new("PLANTS")
sc.collection.children.link(plants)
for i in range(4):
    pl_lo, pl_hi = bounds(OB[f"planter_{i}"])
    ctr = Vector(((pl_lo.x + pl_hi.x) / 2, (pl_lo.y + pl_hi.y) / 2, pl_hi.z + 0.004))
    KP.potted_palm(f"palm_{i}", ctr, plants, PM, random.Random(40 + i), height=1.8, spread=1.08,
                   soil_radius=(pl_hi.x - pl_lo.x) / 2 - 0.02, avoid_dir=(1.0, -0.3) if i == 2 else None)

# --------------------------------------------------------------------------- materials
M_steel = K.mat_metal("S02_steel_brushed", "#C8CBCE", 0.24, brushed=True)
M_glass = K.mat_glass("S02_glass_wing")
M_black_glass = K.mat_simple("S02_black_glass", "#06070A", rough=0.06, coat=1.0)
M_black = K.mat_simple("S02_terminal_body", "#0E1013", rough=0.32)
M_sensor = K.mat_simple("S02_sensor_window", "#020203", rough=0.04, coat=1.0)


def emit_mat(name, rgba, strength):
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    nt.nodes.clear()
    em = nt.nodes.new("ShaderNodeEmission")
    em.name = "emit"
    em.inputs["Color"].default_value = rgba
    em.inputs["Strength"].default_value = strength
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m, em


LOCKED = C.hex_rgba("#FF3B3B")
GO = C.hex_rgba("#36E07A")
M_led, EM_led = emit_mat("S02_led_status", LOCKED, 5.0)
for f, c in ((B["granted"], LOCKED), (B["granted"] + 6, GO)):
    EM_led.inputs["Color"].default_value = c
    EM_led.inputs["Color"].keyframe_insert("default_value", frame=f)

# --------------------------------------------------------------------------- the turnstile (one lane, beside the booth)
CAB_W, CAB_L, CAB_H = 0.18, 1.2, 1.0
CAB_X0 = GATE_X1 + 0.04  # cabinet stands against the gate's end post, lane on the booth side
CAB_X1 = CAB_X0 + CAB_W
CAB_Y0 = GATE_Y1 + 0.22
CAB_Y1 = CAB_Y0 + CAB_L
CAB_CX = (CAB_X0 + CAB_X1) / 2
LX = (CAB_X1 + BOOTH_X0) / 2  # lane centre line (≈ −0.10), 0.64 m clear
WING_Y = (CAB_Y0 + CAB_Y1) / 2
bm = bmesh.new()
box(bm, CAB_X0, CAB_X1, CAB_Y0, CAB_Y1, 0.0, CAB_H)
obj("turnstile_cabinet", bm, [M_steel], bevel=0.012)
bm = bmesh.new()
box(bm, CAB_X0 + 0.006, CAB_X1 - 0.006, CAB_Y0 + 0.006, CAB_Y1 - 0.006, CAB_H, CAB_H + 0.008)
obj("turnstile_top_glass", bm, [M_black_glass], bevel=0.002)
bm = bmesh.new()  # status LEDs: a line along the lane-side top edge + a bar on the entry face (red → green)
ex = CAB_X1 - 0.022
box(bm, ex - 0.004, ex + 0.004, CAB_Y0 + 0.06, CAB_Y1 - 0.06, CAB_H + 0.008, CAB_H + 0.011)
box(bm, CAB_CX - 0.05, CAB_CX + 0.05, CAB_Y0 - 0.002, CAB_Y0, 0.84, 0.852)
obj("turnstile_led", bm, [M_led])

WING_W, WING_Z0, WING_Z1 = BOOTH_X0 - CAB_X1 - 0.08, 0.36, 1.22
piv = bpy.data.objects.new("wing_pivot", None)
piv.empty_display_size = 0.1
piv.location = (CAB_X1, WING_Y, 0.0)
ts.objects.link(piv)
bm = bmesh.new()
K.add_rounded_slab(bm, 0.018 + WING_W / 2, 0.0, (WING_Z0 + WING_Z1) / 2, WING_W, WING_Z1 - WING_Z0, 0.012, 0.05,
                   segments=6, plane="XZ")
wing = obj("wing_glass", bm, [M_glass])
wing.parent = piv
bm = bmesh.new()  # polished hinge post + two clamps
K.add_cylinder(bm, 0.012, 0.0, WING_Z0 - 0.02, WING_Z1 + 0.02, 0.016, segments=24)
for zc in (WING_Z0 + 0.12, WING_Z1 - 0.12):
    box(bm, 0.012, 0.075, -0.014, 0.014, zc - 0.045, zc + 0.045)
wpost = obj("wing_post", bm, [M_steel], bevel=0.003)
wpost.parent = piv
WING_OPEN = math.radians(90)  # swings inward (+Y), flat against the cabinet


def wing_angle(f):
    return WING_OPEN * swing((f - B["wingsOpenStart"]) / (B["wingsOpenEnd"] - B["wingsOpenStart"]), 0.6)


ALL = range(F0, F1 + 1)
key_rot_z(piv, ALL, wing_angle)

# --------------------------------------------------------------------------- Face ID terminal (entry end of the cabinet)
TERM_BASE = Vector((CAB_CX, CAB_Y0 + 0.13, CAB_H + 0.008))
TERM_POS = TERM_BASE + Vector((0.0, -0.03, 0.44))  # head centre (≈ 1.45 m)
SCR_LOCAL = Vector((0.0, -0.0135, -0.012))  # display centre in terminal space
STOP_DIST = 1.35  # 85 mm framing of the 0.25 m head
_dx = TERM_POS.x - LX
CAM_STOP = Vector((LX, TERM_POS.y - math.sqrt(STOP_DIST ** 2 - _dx ** 2), TERM_POS.z + SCR_LOCAL.z))  # level with the display
d = CAM_STOP - TERM_POS
term = bpy.data.objects.new("TERMINAL", None)
term.location = TERM_POS
term.rotation_euler = (0.0, 0.0, math.atan2(d.x, -d.y))  # front (−Y) faces the camera stop; upright (level camera)
ts.objects.link(term)
K.tube("terminal_post", [[tuple(TERM_BASE), tuple(TERM_BASE + Vector((0, -0.015, 0.2))), tuple(TERM_POS - Vector((0, -0.02, 0.11)))]],
       0.016, M_steel, ts, fillet=0.08)
bm = bmesh.new()
K.add_rounded_slab(bm, 0.0, 0.0, 0.0, 0.142, 0.252, 0.026, 0.014, segments=6, plane="XZ")
box(bm, -0.03, 0.03, 0.013, 0.03, -0.16, -0.11)  # mount block onto the post
body = obj("terminal_body", bm, [M_black], bevel=0.002)
body.parent = term
SCR_W, SCR_H = 0.118, 0.21
bm = bmesh.new()
uvl = bm.loops.layers.uv.verify()
vs = [bm.verts.new(v) for v in ((-SCR_W / 2, -0.0135, -SCR_H / 2 - 0.012), (SCR_W / 2, -0.0135, -SCR_H / 2 - 0.012),
                                (SCR_W / 2, -0.0135, SCR_H / 2 - 0.012), (-SCR_W / 2, -0.0135, SCR_H / 2 - 0.012))]
fc = bm.faces.new(vs)
for loop, uv in zip(fc.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
    loop[uvl].uv = uv
me = bpy.data.meshes.new("terminal_screen")
bm.to_mesh(me)
bm.free()
screen = bpy.data.objects.new("terminal_screen", me)
ts.objects.link(screen)
screen.parent = term
bm = bmesh.new()  # two small sensor windows above the display (part of the terminal, not a CCTV camera)
for sx in (-0.018, 0.018):
    K.add_rounded_slab(bm, sx, -0.0136, 0.108, 0.014, 0.008, 0.001, 0.004, segments=3, plane="XZ")
sens = obj("terminal_sensors", bm, [M_sensor])
sens.parent = term


def screen_material():
    m = bpy.data.materials.new("S02_faceid_screen")
    nt = m.node_tree
    nt.nodes.clear()
    tex = nt.nodes.new("ShaderNodeTexImage")
    img = bpy.data.images.load(str(FACEID_DIR / f"{F0:04d}.png"), check_existing=True)
    img.source = "SEQUENCE"
    tex.image = img
    tex.extension = "EXTEND"
    iu = tex.image_user
    iu.frame_duration = F1 - F0 + 1
    iu.frame_start = F0
    iu.frame_offset = F0 - 1
    iu.use_auto_refresh = True
    uvn = nt.nodes.new("ShaderNodeUVMap")
    nt.links.new(uvn.outputs[0], tex.inputs["Vector"])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 2.2
    nt.links.new(tex.outputs["Color"], em.inputs["Color"])
    gls = nt.nodes.new("ShaderNodeBsdfGlossy")
    gls.inputs["Roughness"].default_value = 0.06
    gls.inputs["Color"].default_value = (0.04, 0.04, 0.045, 1)
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(em.outputs[0], add.inputs[0])
    nt.links.new(gls.outputs[0], add.inputs[1])
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(add.outputs[0], o.inputs["Surface"])
    return m


if not (FACEID_DIR / f"{F0:04d}.png").exists():
    raise SystemExit(f"Missing {FACEID_DIR} — run `npm run faceid:render` first")
me.materials.append(screen_material())

spill_d = bpy.data.lights.new("TERMINAL_spill", "AREA")  # the display's light on the bezel / post (red → green)
spill_d.shape, spill_d.size, spill_d.size_y = "RECTANGLE", SCR_W, SCR_H
spill_d.use_shadow = False
spill = bpy.data.objects.new("TERMINAL_spill", spill_d)
ts.objects.link(spill)
spill.parent = term
spill.location = (0.0, -0.016, -0.012)
spill.rotation_euler = (math.radians(-90), 0, 0)  # area lights emit along local −Z → terminal front (−Y)
for f, c, e in ((F0, LOCKED, 0.2), (B["scanStart"] - 6, LOCKED, 0.2), (B["scanStart"], C.hex_rgba("#FF8A84"), 0.45),
                (B["granted"], C.hex_rgba("#FF8A84"), 0.45), (B["granted"] + 6, GO, 0.6)):
    spill_d.color = c[:3]
    spill_d.energy = e
    spill_d.keyframe_insert("color", frame=f)
    spill_d.keyframe_insert("energy", frame=f)

# How much of the new turnstile the photo camera sees through the open passage (it fades in with the 3D during the D dissolve)
bpy.context.view_layer.update()
_dg = bpy.context.evaluated_depsgraph_get()
_seen = _tested = 0
for o in ts.all_objects:
    if o.type != "MESH":
        continue
    vv = o.data.vertices
    for v in list(vv)[:: max(1, len(vv) // 200)]:
        q = o.matrix_world @ v.co
        dvec = q - REF_LOC
        hit, loc, _n, _i, hob, _m = sc.ray_cast(_dg, REF_LOC, dvec.normalized(), distance=dvec.length + 0.05)
        _tested += 1
        _seen += bool(hit and hob.name == o.name)
print(f"TURNSTILE visible from the photo camera: {_seen} of {_tested} sampled vertices")

# --------------------------------------------------------------------------- the camera's route and the slab (EXIT S)
DIVE = Vector((1.2, 12.55, 0.0))  # end of the courtyard glide: right of the palms (planter 2 at x ≈ −0.36), 4 m from the glass
LAND = Vector((1.26, 13.05, 0.0))  # where the camera sinks into the paving (slab anchor x/y)
FINAL_YAW = math.radians(12)  # looking at the cafeteria glass, a little to the left (palms in the left foreground)
slab_shell = next(o for o in bpy.data.collections["PIECE_slab"].all_objects if o.name.startswith("slab_shell"))
slab_top_local = max(v[2] for v in slab_shell.bound_box)  # −0.02
slab = bpy.data.objects.new("SLAB.inst", None)  # under the courtyard paving, turned like the camera (anchor yaw = rig yaw)
slab.instance_type = "COLLECTION"
slab.instance_collection = bpy.data.collections["PIECE_slab"]
slab.location = (LAND.x, LAND.y, -slab_top_local - 0.006)  # slab top 6 mm under the paving (no z-fight)
slab.rotation_euler = (0.0, 0.0, FINAL_YAW)
ts.objects.link(slab)
bpy.context.view_layer.update()
C.add_slab_probe(slab)
slab_anchor_m = C.slab_handoff_matrix(slab)
SLAB_ANCHOR = slab_anchor_m.translation.copy()

# --------------------------------------------------------------------------- film camera
rig, cam, focus = C.make_camera_rig("RIG_S02", lens=REF_LENS, location=REF_LOC, rotation=(math.radians(90), 0, 0), fstop=4.0)
cam.data.clip_start = 0.01
S_SPEED = C.HANDOFF_TYPES["S"]["speed"]
E_HOLD = 6
EXIT_START = F1 - E_HOLD  # 503
assert EXIT_START == B["exitHold"], "S02_BEATS.exitHold must equal scene end − 6"

# D hand-off segment: identical to build_entrance.py cam_path (CAM_S02_START), so the photo layer lines up.
BLEND_FRAMES = B["dissolveEnd"] - F0
V0, V1 = 0.03, 0.07


def dissolve_y(f):
    t = f - F0
    acc = (V1 - V0) / BLEND_FRAMES
    if t <= BLEND_FRAMES:
        return V0 * t + 0.5 * acc * t * t
    return V0 * BLEND_FRAMES + 0.5 * acc * BLEND_FRAMES ** 2 + V1 * (t - BLEND_FRAMES)


def hermite(p0, m0, p1, m1, t):
    h00, h10 = 2 * t ** 3 - 3 * t ** 2 + 1, t ** 3 - 2 * t ** 2 + t
    h01, h11 = -2 * t ** 3 + 3 * t ** 2, t ** 3 - t ** 2
    return p0 * h00 + m0 * h10 + p1 * h01 + m1 * h11


P_D = Vector((REF_LOC.x, REF_LOC.y + dissolve_y(B["dissolveEnd"]), REF_LOC.z))
WAY = [  # (frame, position, velocity m/frame)
    (B["dissolveEnd"], P_D, Vector((0.0, V1, 0.0))),
    (B["boothStop"], CAM_STOP, Vector((0, 0, 0))),
    (B["moveOn"], CAM_STOP, Vector((0, 0, 0))),
    (B["lanePass"], Vector((LX, WING_Y, CAM_STOP.z)), Vector((0.002, 0.07, 0.0))),
    (B["lanePass"] + 20, Vector((LX + 0.06, BOOTH_Y1 + 0.1, CAM_STOP.z)), Vector((0.03, 0.06, 0.0))),
    (B["revealEnd"], Vector((DIVE.x, DIVE.y, CAM_STOP.z - 0.05)), Vector((0.004, 0.04, -0.006))),
    (EXIT_START, SLAB_ANCHOR + Vector((0, 0, S_SPEED * E_HOLD)), Vector((0, 0, -S_SPEED))),
]


def cam_position(f):
    if f <= B["dissolveEnd"]:
        return Vector((REF_LOC.x, REF_LOC.y + dissolve_y(f), REF_LOC.z))
    if f >= EXIT_START:
        return SLAB_ANCHOR + Vector((0, 0, S_SPEED * (F1 - f)))
    for (fa, pa, va), (fb, pb, vb) in zip(WAY, WAY[1:]):
        if fa <= f <= fb:
            n = fb - fa
            return hermite(pa, va * n, pb, vb * n, (f - fa) / n)
    raise ValueError(f)


bpy.context.view_layer.update()
SCREEN_C = term.matrix_world @ SCR_LOCAL
_a = SCREEN_C - CAM_STOP
AIM_Y = math.atan2(-_a.x, _a.y)
LEVEL = math.radians(90)


def ss(f, a, b):
    return C.smootherstep((f - a) / (b - a))


def cam_rotation(f):
    """Pitch locked level (verticals stay vertical) until the final tilt; yaw: ahead → terminal → lane → cafeteria."""
    yaw = AIM_Y * ss(f, B["dissolveEnd"] + 20, B["boothStop"] - 4)
    yaw *= 1 - ss(f, B["moveOn"], B["moveOn"] + 18)
    yaw += FINAL_YAW * ss(f, B["lanePass"] + 10, B["revealEnd"])  # gentle turn toward the cafeteria glass
    pitch = LEVEL * (1 - ss(f, B["tiltStart"], EXIT_START))
    return (pitch, 0.0, yaw)


C.bake_path(rig, range(F0, EXIT_START), lambda f: dict(location=tuple(cam_position(f)), rotation=cam_rotation(f)))
exit_anchor = bpy.data.objects.new("EXIT_ANCHOR_S", None)
exit_anchor.matrix_world = slab_anchor_m
ts.objects.link(exit_anchor)
bpy.context.view_layer.update()
assert abs(exit_anchor.matrix_world.to_euler().z - FINAL_YAW) < 1e-4, (exit_anchor.matrix_world.to_euler(), FINAL_YAW)
C.key_handoff(rig, cam, SCENE_ID, "EXIT", exit_anchor)

# Lens: 18 mm hand-off (+ the photo's lens shift, easing out) → 85 on the terminal → 24 in the lane, the courtyard and the S pass
for f, lens in ((F0, REF_LENS), (B["dissolveEnd"], REF_LENS), (B["zoomStart"], 35.0), (B["boothStop"], 85.0),
                (B["moveOn"], 85.0), (B["lanePass"] - 4, 24.0), (EXIT_START - 3, 24.0)):
    C.set_lens(cam, lens, frame=f, allow_special=True)
for (f, sx, sy) in ((F0, *REF_SHIFT), (B["dissolveEnd"], *REF_SHIFT), (B["zoomStart"], 0.0, 0.0)):
    cam.data.shift_x, cam.data.shift_y = sx, sy
    cam.data.keyframe_insert("shift_x", frame=f)
    cam.data.keyframe_insert("shift_y", frame=f)
for fcv in C.fcurves_of(cam.data):
    if fcv.data_path in ("lens", "shift_x", "shift_y"):
        for kp in fcv.keyframe_points:
            if kp.co.x < EXIT_START:
                kp.interpolation, kp.easing = "SINE", "EASE_IN_OUT"
# DOF: off for the photo match and the moves; on the terminal only
for f, v in ((F0, False), (B["zoomStart"] + 4, True), (B["moveOn"] + 8, False)):
    cam.data.dof.use_dof = v
    cam.data.dof.keyframe_insert("use_dof", frame=f)
for f, p in ((F0, SCREEN_C), (B["moveOn"], SCREEN_C)):
    C.key_transform(focus, f, location=tuple(p))
C.set_easing(focus)

# --------------------------------------------------------------------------- colour: approved exterior look
vs_ = sc.view_settings
for look in ("AgX - Medium High Contrast", "Medium High Contrast"):
    try:
        vs_.look = look
        break
    except TypeError:
        pass
EXT_LOOK = vs_.look
vs_.use_white_balance = False
# Inside the slab (camera within the solid top deck, 505 …) switch to scene 3's colour settings — never seen.
SLAB_IN = EXIT_START + 2
for f, look in ((F0, EXT_LOOK), (SLAB_IN - 1, EXT_LOOK), (SLAB_IN, "None")):
    vs_.look = look
    vs_.keyframe_insert("look", frame=f)
vs_.look = EXT_LOOK
for fcv in C.fcurves_of(sc):
    for kp in fcv.keyframe_points:
        if fcv.data_path.endswith("look"):
            kp.interpolation = "CONSTANT"
C.key_slab_isolation(SLAB_IN, F1)

# --------------------------------------------------------------------------- clearance check (no clipping, ever)
sc.frame_set(F0)
dg = bpy.context.evaluated_depsgraph_get()
ANIM = {wing.name, wpost.name}
SKIP = ("courtyard_tree_leaves", "proj_sky_card")


def bvh_of(objs):
    verts, polys = [], []
    for o in objs:
        ev = o.evaluated_get(dg)
        try:
            m = ev.to_mesh()
        except RuntimeError:
            continue
        if m is None:
            continue
        base = len(verts)
        mw = o.matrix_world
        verts += [mw @ v.co for v in m.vertices]
        polys += [[base + i for i in p.vertices] for p in m.polygons]
        ev.to_mesh_clear()
    return BVHTree.FromPolygons(verts, polys) if polys else None


static = bvh_of([o for o in sc.objects if o.visible_get() and o.type in ("MESH", "CURVE")
                 and not o.name.startswith(SKIP) and o.name not in ANIM])
worst = []
for f in range(F0, F1 + 1):
    sc.frame_set(f)
    p = rig.matrix_world.translation.copy()
    dyn = bvh_of([OB[n] for n in ANIM])
    ds = [t[3] for t in ((static.find_nearest(p) if static else None), (dyn.find_nearest(p) if dyn else None)) if t and t[0]]
    if f < EXIT_START - 2:  # the S pass itself goes through the paving by design
        worst.append((min(ds) if ds else 99.0, f))
worst.sort()
print("CLEARANCE min (m, frame):", [(round(d_, 3), f_) for d_, f_ in worst[:6]])
if worst[0][0] < 0.12:
    print(f"WARNING: camera within {worst[0][0]:.3f} m of geometry at frame {worst[0][1]}")

sc.camera = cam
if not NO_BAKE:
    sc.frame_set(F1)
    try:
        bpy.ops.object.lightprobe_cache_bake(subset="ALL")
        print("PROBES_BAKED")
    except RuntimeError as e:
        print(f"PROBE_BAKE_FAILED {e}")

sc.frame_set(F0)
sc["s02_notes"] = (f"D entry {F0}–{B['dissolveEnd']} (photo layer from entrance.blend ENTRANCE_PROJ), turnstile lane x={LX:.3f} "
                   f"beside the booth, stop {B['boothStop']}, courtyard glide to {B['revealEnd']}, glass cafeteria ahead, "
                   f"EXIT S {EXIT_START}–{F1} (SLAB.inst, look switch at {SLAB_IN}).")
print("saved", C.save_scene(SCENE_ID))
