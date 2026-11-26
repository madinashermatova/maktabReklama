"""Scene 3 — "CCTV security" (film frames 450–599) → blender/scenes/s03_cctv.blend

    "C:\\Program Files\\Blender Foundation\\Blender 5.3\\blender.exe" -b --python blender/scripts/scene_03_cctv.py

Builds the corridor from the shared kit, three surveillance cameras (pendant turret dome + 2 bullets in wall housings),
renders the cameras' own feeds (renders/_cctv_feeds/<cam>/####.png, used live on the corridor's security monitor),
bakes the irradiance probes and saves the scene. Decisions (user, 2026-11-26): corridor concept with a security
monitor; indoor CCTV in corridors and classrooms is real; 3 → 4 is a lens pass (C) into the dome camera's lens.

Timeline (absolute frames):
  450–456  ENTRY S: slab pass (looking straight down, 24 mm, 0.12 m/frame) — C.key_handoff
  456–482  camera drops through the ceiling into the corridor, decelerates, tilts up to look down the corridor, 24 → 35 mm
  484–510  cameras slide out on short rails (staggered); then servo pans: LEFT 35°, pause 0.5 s, RIGHT 70°, pause
  552–588  a soft glowing light point travels down the corridor; cameras lock on and track it (Locked/Damped Track
           on per-camera lagged targets: 3 / 5 / 7 frames), blue status LEDs pulse brighter on lock-on
  520–585  the wall security monitor shows the three live feeds (no text, no overlay)
  568–599  push forward-and-down along the dome lens axis; EXIT C (lens pass): camera 12 mm inside the front element
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as C  # noqa: E402

SCENE_ID = "s03_cctv"
SD = C.get_scene_def(SCENE_ID)
F0, F1 = SD["from"], SD["end"]  # 450, 599
KIT = C.KIT_DIR / "school_kit.blend"
FEED_DIR = C.RENDERS_DIR / "_cctv_feeds"
FEED_FROM = 484  # cameras start to slide out; before that the feeds are not used (monitor shows standby)
SKIP_FEEDS = "--skip-feeds" in sys.argv

ROOM_H = 3.2
CORR_W = 3.0
CORR_L = 18.0
X0 = -CORR_W / 2

# --------------------------------------------------------------------------- scene + kit
C.reset_scene()
sc = C.setup_scene(SCENE_ID, samples=64)
sc.render.filepath = str(C.RENDERS_DIR / SCENE_ID / "####")

PIECES = ["wall_segment", "wall_window", "door_frame", "floor_area", "ceiling_panel", "skirting", "slab"]
with bpy.data.libraries.load(str(KIT), link=False) as (src, dst):
    dst.collections = [f"PIECE_{p}" for p in PIECES] + [f"LIGHT_{p}" for p in C.LIGHTING_PRESETS]
    dst.worlds = [w for w in src.worlds]
kit_root = bpy.data.collections.new("KIT_pieces")
sc.collection.children.link(kit_root)
for p in PIECES:
    kit_root.children.link(bpy.data.collections[f"PIECE_{p}"])
for p in C.LIGHTING_PRESETS:
    sc.collection.children.link(bpy.data.collections[f"LIGHT_{p}"])
bpy.context.view_layer.layer_collection.children["KIT_pieces"].exclude = True

world_coll = bpy.data.collections.new("CORRIDOR")
sc.collection.children.link(world_coll)


def inst(piece, loc, rot_z=0.0, name=None):
    ob = bpy.data.objects.new(name or f"{piece}.inst", None)
    ob.instance_type = "COLLECTION"
    ob.instance_collection = bpy.data.collections[f"PIECE_{piece}"]
    ob.location = loc
    ob.rotation_euler = (0, 0, math.radians(rot_z))
    world_coll.objects.link(ob)
    return ob


# Corridor along +Y. Kit wall: runs +X from its origin, interior face = local −Y side.
LEFT = {0: "wall_segment", 3: "door_frame", 6: "wall_segment", 9: "wall_segment", 12: "door_frame", 15: "wall_segment"}
RIGHT = {0: "wall_segment", 3: "wall_segment", 6: "wall_segment", 9: "door_frame", 12: "wall_segment", 15: "door_frame"}
for y, piece in LEFT.items():  # x = −1.5, interior faces +X → rot 90°, runs +Y
    inst(piece, (X0, y, 0), 90)
    if piece == "wall_segment":
        inst("skirting", (X0, y, 0), 90)
for y, piece in RIGHT.items():  # x = +1.5, interior faces −X → rot −90°, runs −Y
    inst(piece, (-X0, y + 3, 0), -90)
    if piece == "wall_segment":
        inst("skirting", (-X0, y + 3, 0), -90)
inst("wall_window", (X0, CORR_L, 0), 0)  # far end: window (soft daylight, DOF-blurred)
inst("wall_segment", (-X0, 0, 0), 180)  # behind the camera
for y in range(0, int(CORR_L), 3):
    inst("floor_area", (X0, y, 0))
    inst("ceiling_panel", (X0, y, ROOM_H))

# Slab above the ceiling at the entry point (walls reach 3.5 m → slab bottom deck rests on them)
ENTRY_XY = (0.0, 1.8)
slab = inst("slab", (ENTRY_XY[0], ENTRY_XY[1], ROOM_H + 0.3 + 1.2), 0, name="SLAB.inst")
bpy.context.view_layer.update()  # matrix_world of new objects is stale until the depsgraph updates
C.add_slab_probe(slab)

C.apply_lighting_preset("day_interior")

# --------------------------------------------------------------------------- room atmosphere (docs/design-language.md)
# Scene 3 corridor: morning, cool neutral (≈ 5800 K), slightly dim, small blue status LEDs; cool light-grey walls,
# pale grey-washed floor. Only this file's copies of the kit materials change; shell pieces stay as they are.
ATM_KELVIN = 5800
for key, watts, emit in (("downlight", 6.0, 12.0), ("ledstrip", 6.5, 7.0)):
    light = bpy.data.lights[f"KIT_{key}"]
    light.energy = watts
    light.use_temperature = True
    light.temperature = ATM_KELVIN
    em = next(n for n in bpy.data.materials[f"KIT_{key}_emit"].node_tree.nodes if n.type == "EMISSION")
    em.inputs["Color"].default_value = C.kelvin_rgba(ATM_KELVIN)
    em.inputs["Strength"].default_value = emit
for n in sc.world.node_tree.nodes:
    if n.type == "BACKGROUND":
        n.inputs["Strength"].default_value *= 0.6
for ob in bpy.data.collections["LIGHT_day_interior"].objects:
    if ob.type == "LIGHT":
        ob.data.energy *= 0.55
        ob.data.color = C.kelvin_rgba(6800)[:3]
sc.view_settings.exposure = -0.2


def tint_base_color(mat_name, hex_color, factor):
    """Mix the material's base colour toward hex_color (keeps its texture/grain, shifts the palette)."""
    nt = bpy.data.materials[mat_name].node_tree
    p = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    inp = p.inputs["Base Color"]
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["Factor"].default_value = factor
    mix.inputs["B"].default_value = C.hex_rgba(hex_color)
    if inp.links:
        src = inp.links[0].from_socket
        nt.links.remove(inp.links[0])
        nt.links.new(src, mix.inputs["A"])
    else:
        mix.inputs["A"].default_value = inp.default_value
    nt.links.new(mix.outputs["Result"], inp)


tint_base_color("KIT_wall_paint", "#D8DCDF", 0.85)  # cool light grey
tint_base_color("KIT_floor", "#C4C3BE", 0.6)  # pale grey-washed planks

# --------------------------------------------------------------------------- materials


def principled(name, color, metallic=0.0, rough=0.5, **extra):
    m = bpy.data.materials.new(name)
    p = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    p.inputs["Base Color"].default_value = color
    p.inputs["Metallic"].default_value = metallic
    p.inputs["Roughness"].default_value = rough
    for k, v in extra.items():
        key = k.replace("_", " ")
        if key in p.inputs:
            p.inputs[key].default_value = v
    return m


M_white = principled("S03_housing_white", C.hex_rgba("#EEEDEA"), rough=0.32, Coat_Weight=0.25)
M_grey = principled("S03_housing_grey", C.hex_rgba("#B9BCBF"), metallic=0.0, rough=0.4)
M_black = principled("S03_bezel_black", C.hex_rgba("#0B0C0E"), rough=0.35)
M_anod = principled("S03_lens_barrel", C.hex_rgba("#121315"), metallic=1.0, rough=0.28)
M_steel = principled("S03_rail_steel", C.hex_rgba("#A8ABAE"), metallic=1.0, rough=0.25, Anisotropic=0.5)
M_inner = principled("S03_recess_dark", C.hex_rgba("#141516"), rough=0.7)
# Multi-coated lens glass: thin-film interference gives the subtle green / purple reflections
M_coat = principled("S03_lens_coated", (0.004, 0.005, 0.006, 1), rough=0.04, IOR=1.62,
                    Thin_Film_Thickness=290.0, Thin_Film_IOR=1.38, Coat_Weight=0.0)
M_coat_in = principled("S03_lens_inner", (0.002, 0.002, 0.003, 1), rough=0.06, IOR=1.7,
                       Thin_Film_Thickness=410.0, Thin_Film_IOR=1.38)
M_ir = principled("S03_ir_led", (0.05, 0.01, 0.01, 1), rough=0.15)


def led_material(name):
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    nt.nodes.clear()
    em = nt.nodes.new("ShaderNodeEmission")
    em.name = "led"
    em.inputs["Strength"].default_value = 6.0
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m, em


# --------------------------------------------------------------------------- geometry helpers


def new_obj(name, bm, mats, parent=None, smooth=False, bevel=0.0):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    if smooth:
        for poly in me.polygons:
            poly.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    world_coll.objects.link(ob)
    if parent is not None:
        ob.parent = parent
    if bevel:
        b = ob.modifiers.new("bevel", "BEVEL")
        b.width, b.segments, b.limit_method = bevel, 3, "ANGLE"
        ob.modifiers.new("wn", "WEIGHTED_NORMAL")
    return ob


def empty(name, loc=(0, 0, 0), parent=None, rot=(0, 0, 0)):
    ob = bpy.data.objects.new(name, None)
    ob.empty_display_size = 0.05
    world_coll.objects.link(ob)
    ob.parent = parent
    ob.location = loc
    ob.rotation_euler = rot
    return ob


def box_bm(sx, sy, sz, c=(0, 0, 0), mat=0, bm=None):
    bm = bm or bmesh.new()
    r = bmesh.ops.create_cube(bm, size=1.0)
    for v in r["verts"]:
        v.co = Vector((c[0] + v.co.x * sx, c[1] + v.co.y * sy, c[2] + v.co.z * sz))
    for f in {f for v in r["verts"] for f in v.link_faces}:
        f.material_index = mat
    return bm


def cyl_bm(r, depth, axis="Y", c=(0, 0, 0), seg=40, mat=0, bm=None, r2=None):
    """Cylinder (or cone with r2) centred at c along axis."""
    bm = bm or bmesh.new()
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=depth)
    rot = {"Z": Matrix.Identity(3), "Y": Matrix.Rotation(math.radians(-90), 3, "X"), "X": Matrix.Rotation(math.radians(90), 3, "Y")}[axis]
    for v in res["verts"]:
        v.co = rot @ v.co + Vector(c)
    for f in {f for v in res["verts"] for f in v.link_faces}:
        f.material_index = mat
    return bm


def sphere_bm(r, c=(0, 0, 0), mat=0, bm=None, seg=32):
    bm = bm or bmesh.new()
    res = bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=r)
    for v in res["verts"]:
        v.co += Vector(c)
    for f in {f for v in res["verts"] for f in v.link_faces}:
        f.material_index = mat
    return bm


def lens_assembly(parent, front_y, r_front, name, ir_ring=0):
    """Lens along local +Y ending at front_y: anodised barrel, coated front element, two inner coated elements,
    black iris; optional ring of IR LEDs around it. Returns the front element's local centre."""
    bm = cyl_bm(r_front + 0.004, 0.05, "Y", (0, front_y - 0.025, 0), mat=0)
    # open the barrel front: inner black tube slightly smaller (reads as depth)
    cyl_bm(r_front + 0.0005, 0.048, "Y", (0, front_y - 0.023, 0), mat=1, bm=bm)
    new_obj(f"{name}_barrel", bm, [M_anod, M_inner], parent, smooth=True)
    bm = bmesh.new()
    sphere_bm(r_front * 2.2, (0, front_y - r_front * 2.2 + 0.003, 0), bm=bm, seg=48)
    # keep only the cap in front of the barrel lip (a gently domed front element)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y < front_y - 0.0015], context="VERTS")
    new_obj(f"{name}_front", bm, [M_coat], parent, smooth=True)
    for k, (dy, rr) in enumerate(((0.012, 0.92), (0.026, 0.8))):
        bm = cyl_bm(r_front * rr, 0.002, "Y", (0, front_y - dy, 0), seg=40)
        new_obj(f"{name}_inner{k}", bm, [M_coat_in], parent, smooth=True)
    bm = cyl_bm(r_front * 0.45, 0.001, "Y", (0, front_y - 0.04, 0), seg=32)
    new_obj(f"{name}_iris", bm, [M_inner], parent)
    if ir_ring:
        bm = bmesh.new()
        for i in range(ir_ring):
            a = 2 * math.pi * i / ir_ring
            rr = r_front + 0.012
            sphere_bm(0.0028, (rr * math.cos(a), front_y - 0.004, rr * math.sin(a)), bm=bm, seg=10)
        new_obj(f"{name}_ir", bm, [M_ir], parent, smooth=True)
    return Vector((0, front_y, 0))


# --------------------------------------------------------------------------- surveillance cameras
CAMS = {}


def build_bullet(name, wall_x, y, z, side, rest_yaw_deg, rest_tilt_deg):
    """Wall housing (open toward −Y) on the side wall; the camera slides out along −Y on twin rails.
    side = +1 for the left wall (housing extends +X from x = −1.5), −1 for the right wall."""
    hw, hh, hl = 0.20, 0.20, 0.42  # housing width (from wall), height, length (along Y)
    cx = wall_x + side * hw / 2
    # housing: 5 closed sides + open front, bevelled; dark inner liner
    bm = bmesh.new()
    t = 0.012
    box_bm(hw, hl, t, (cx, y, z + hh / 2 - t / 2), bm=bm)
    box_bm(hw, hl, t, (cx, y, z - hh / 2 + t / 2), bm=bm)
    box_bm(t, hl, hh, (wall_x + side * (hw - t / 2), y, z), bm=bm)
    box_bm(t, hl, hh, (wall_x + side * t / 2, y, z), bm=bm)
    box_bm(hw, t, hh, (cx, y + hl / 2 - t / 2, z), bm=bm)
    new_obj(f"{name}_housing", bm, [M_white], bevel=0.003)
    bm = box_bm(hw - 2 * t, hl - t, hh - 2 * t, (cx, y + t / 2, z), mat=0)
    liner = new_obj(f"{name}_liner", bm, [M_inner])
    for poly in liner.data.polygons:  # normals inward (we look into it)
        poly.flip()
    # twin rails (fixed): from the housing back to 0.36 m in front of its mouth
    rail_len = hl + 0.36
    bm = bmesh.new()
    for dz in (0.055, 0.075):
        cyl_bm(0.006, rail_len, "Y", (cx, y + hl / 2 - rail_len / 2, z + dz - 0.0), bm=bm, seg=16)
    rails = new_obj(f"{name}_rails", bm, [M_steel], smooth=True)
    rails.location.z -= 0.0

    mount = empty(f"{name}_MOUNT", (cx, y, z))  # slides along −Y
    bm = box_bm(0.06, 0.05, 0.04, (0, 0, 0.065))  # carriage on the rails
    cyl_bm(0.012, 0.05, "Z", (0, 0, 0.03), bm=bm, seg=20)  # joint stem
    new_obj(f"{name}_carriage", bm, [M_grey], mount, bevel=0.004)
    pan = empty(f"{name}_PAN", (0, 0, 0.0), mount, (0, 0, math.radians(rest_yaw_deg)))
    bm = cyl_bm(0.022, 0.02, "Z", (0, 0, 0.0), seg=28)  # pan ring
    new_obj(f"{name}_panring", bm, [M_grey], pan, smooth=True, bevel=0.002)
    tilt = empty(f"{name}_TILT", (0, 0, -0.045), pan, (math.radians(rest_tilt_deg), 0, 0))
    # yoke
    bm = box_bm(0.012, 0.03, 0.05, (0.046, 0, 0.022))
    box_bm(0.012, 0.03, 0.05, (-0.046, 0, 0.022), bm=bm)
    box_bm(0.104, 0.03, 0.012, (0, 0, 0.044), bm=bm)
    new_obj(f"{name}_yoke", bm, [M_grey], pan, bevel=0.003).location = (0, 0, -0.045)
    # body: housing tube along +Y, rear cap, front bezel ring, sun shield over the top
    L = 0.24
    bm = cyl_bm(0.04, L, "Y", (0, -0.01, 0), seg=48)
    new_obj(f"{name}_body", bm, [M_white], tilt, smooth=True, bevel=0.004)
    bm = cyl_bm(0.041, 0.012, "Y", (0, -0.01 + L / 2 + 0.006, 0), seg=48)
    new_obj(f"{name}_bezel", bm, [M_black], tilt, smooth=True, bevel=0.002)
    bm = bmesh.new()  # sun shield: curved plate (part of a tube), extends past the front
    res = bmesh.ops.create_cone(bm, cap_ends=False, segments=48, radius1=0.05, radius2=0.05, depth=L + 0.07)
    rot = Matrix.Rotation(math.radians(-90), 3, "X")
    for v in res["verts"]:
        v.co = rot @ v.co + Vector((0, 0.025, 0.0))
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < 0.012], context="VERTS")
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.003)
    new_obj(f"{name}_sunshield", bm, [M_white], tilt, smooth=True)
    bm = box_bm(0.01, 0.12, 0.016, (0, 0.0, 0.046))  # shield bracket
    new_obj(f"{name}_shieldbracket", bm, [M_grey], tilt)
    front_y = -0.01 + L / 2 + 0.013
    lens_front = lens_assembly(tilt, front_y + 0.004, 0.016, name, ir_ring=12)
    led_mat, led_node = led_material(f"{name}_LED")
    bm = sphere_bm(0.0032, (0.028, front_y + 0.001, -0.022), seg=12)
    new_obj(f"{name}_led", bm, [led_mat], tilt, smooth=True)
    CAMS[name] = dict(mount=mount, pan=pan, tilt=tilt, lens=lens_front, led=led_node, kind="bullet",
                      rest_yaw=rest_yaw_deg, rest_tilt=rest_tilt_deg, slide=Vector((0, -(hl / 2 + 0.25), 0)),
                      start=mount.location.copy())


def build_dome(name, x, y, drop, rest_yaw_deg, rest_tilt_deg):
    """Pendant turret dome: ceiling hatch (trim box) → telescopic rod lowers the turret on a short drop."""
    z_ceil = ROOM_H
    bm = bmesh.new()  # hatch trim frame (square ring) just under the ceiling
    o, i, h = 0.40, 0.30, 0.025
    for (sx, sy, cx_, cy_) in ((o, (o - i) / 2, 0, (o + i) / 4), (o, (o - i) / 2, 0, -(o + i) / 4),
                                ((o - i) / 2, i, (o + i) / 4, 0), ((o - i) / 2, i, -(o + i) / 4, 0)):
        box_bm(sx, sy, h, (x + cx_, y + cy_, z_ceil - h / 2), bm=bm)
    new_obj(f"{name}_hatch", bm, [M_white], bevel=0.003)
    bm = box_bm(i, i, 0.30, (x, y, z_ceil + 0.15 - 0.002))  # dark shaft above the opening
    shaft = new_obj(f"{name}_shaft", bm, [M_inner])
    for poly in shaft.data.polygons:
        poly.flip()
    rest_z = z_ceil + 0.11  # turret centre while retracted (inside the shaft)
    mount = empty(f"{name}_MOUNT", (x, y, rest_z))
    bm = cyl_bm(0.016, 0.9, "Z", (0, 0, 0.45 + 0.06), seg=24)  # rod (upper part hides in the ceiling void)
    new_obj(f"{name}_rod", bm, [M_steel], mount, smooth=True)
    bm = cyl_bm(0.075, 0.045, "Z", (0, 0, 0.075), seg=48, r2=0.06)  # base cup
    new_obj(f"{name}_base", bm, [M_white], mount, smooth=True, bevel=0.004)
    pan = empty(f"{name}_PAN", (0, 0, 0), mount, (0, 0, math.radians(rest_yaw_deg)))
    bm = cyl_bm(0.078, 0.022, "Z", (0, 0, 0.042), seg=48)  # pan ring / shroud collar
    bm2 = bmesh.new()
    res = bmesh.ops.create_uvsphere(bm2, u_segments=48, v_segments=24, radius=0.08)
    bmesh.ops.delete(bm2, geom=[v for v in bm2.verts if v.co.z < -0.005 or v.co.y > 0.03], context="VERTS")
    bmesh.ops.solidify(bm2, geom=bm2.faces[:], thickness=0.004)
    new_obj(f"{name}_collar", bm, [M_white], pan, smooth=True, bevel=0.003)
    new_obj(f"{name}_shroud", bm2, [M_white], pan, smooth=True)
    tilt = empty(f"{name}_TILT", (0, 0, 0), pan, (math.radians(rest_tilt_deg), 0, 0))
    bm = sphere_bm(0.068, seg=48)
    new_obj(f"{name}_ball", bm, [M_white], tilt, smooth=True)
    bm = cyl_bm(0.034, 0.02, "Y", (0, 0.062, 0), seg=48)  # black face plate
    new_obj(f"{name}_face", bm, [M_black], tilt, smooth=True, bevel=0.002)
    lens_front = lens_assembly(tilt, 0.078, 0.019, name, ir_ring=0)
    led_mat, led_node = led_material(f"{name}_LED")
    bm = sphere_bm(0.003, (0.0, 0.07, -0.026), seg=12)
    new_obj(f"{name}_led", bm, [led_mat], tilt, smooth=True)
    CAMS[name] = dict(mount=mount, pan=pan, tilt=tilt, lens=lens_front, led=led_node, kind="dome",
                      rest_yaw=rest_yaw_deg, rest_tilt=rest_tilt_deg, slide=Vector((0, 0, -(0.11 + drop))),
                      start=mount.location.copy())


BL_Y, BR_Y, DOME_Y = 7.5, 12.5, 9.0
CAM_Z = 2.62
DOME_DROP = 0.74  # pivot ends at 3.2 − 0.74 = 2.46 m
build_bullet("CCTV_bulletL", X0, BL_Y, CAM_Z, +1, 190.0, -14.0)
build_bullet("CCTV_bulletR", -X0, BR_Y, CAM_Z, -1, 172.0, -12.0)
build_dome("CCTV_dome", 0.0, DOME_Y, DOME_DROP, 180.0, -22.0)

# --------------------------------------------------------------------------- animation: slide, servo pans


def servo(u, settle=0.55):
    """Servo move 0 → 1: quick start (short smooth ramp), smooth stop with a tiny overshoot + settle."""
    u = C.clamp01(u)
    a = 0.12
    w = u * u / (2 * a) if u < a else u - a / 2
    w /= 1 - a / 2
    return C.ease_out_back(w, settle)


SCHED = {  # per camera: slide start, pan-left start, pan-right start, lock-on (track start), lag (frames)
    "CCTV_bulletL": dict(slide=484, left=510, right=535, lock=560, lag=5),
    "CCTV_dome": dict(slide=488, left=512, right=537, lock=562, lag=3),
    "CCTV_bulletR": dict(slide=492, left=514, right=539, lock=564, lag=7),
}
SLIDE_LEN, PAN_L_LEN, PAN_R_LEN = 18, 10, 13

for name, s in SCHED.items():
    c = CAMS[name]
    mount, pan = c["mount"], c["pan"]

    def mount_pose(f, c=c, s=s):
        u = C.smootherstep((f - s["slide"]) / SLIDE_LEN)
        return dict(location=tuple(c["start"] + c["slide"] * u))

    C.bake_path(mount, range(F0, F1 + 1), mount_pose)

    def pan_pose(f, c=c, s=s):
        yaw = c["rest_yaw"] + 35.0 * servo((f - s["left"]) / PAN_L_LEN) - 70.0 * servo((f - s["right"]) / PAN_R_LEN)
        return dict(rotation=(0.0, 0.0, math.radians(yaw)))

    C.bake_path(pan, range(F0, F1 + 1), pan_pose)

# --------------------------------------------------------------------------- the light point (no people)
DOME_PIVOT = CAMS["CCTV_dome"]["start"] + CAMS["CCTV_dome"]["slide"]
HOVER = Vector((0.0, 4.0, 2.64))  # where the light comes to rest, behind the film camera
LIGHT_PTS = [Vector(p) for p in ((-0.35, 16.6, 1.25), (0.25, 12.5, 1.55), (0.55, 8.6, 2.0), (0.45, 6.2, 2.4), tuple(HOVER))]
L_APPEAR, L_GO, L_ARRIVE = 550, 556, 588


def catmull(pts, t):
    n = len(pts) - 1
    t = C.clamp01(t) * n
    i = min(int(t), n - 1)
    u = t - i
    p0, p1, p2, p3 = pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, n)]
    return 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)


def light_pos(f):
    return catmull(LIGHT_PTS, C.smootherstep((f - L_GO) / (L_ARRIVE - L_GO)))


M_orb = bpy.data.materials.new("S03_light_orb")
nt = M_orb.node_tree
nt.nodes.clear()
orb_em = nt.nodes.new("ShaderNodeEmission")
orb_em.inputs["Color"].default_value = C.kelvin_rgba(5200)
out = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(orb_em.outputs[0], out.inputs["Surface"])
orb = new_obj("LIGHT_POINT", sphere_bm(0.034, seg=24), [M_orb], smooth=True)
orb.visible_shadow = False
ld = bpy.data.lights.new("LIGHT_POINT_lamp", "POINT")
ld.color = C.kelvin_rgba(5200)[:3]
ld.shadow_soft_size = 0.03
lamp = bpy.data.objects.new("LIGHT_POINT_lamp", ld)
lamp.parent = orb
world_coll.objects.link(lamp)
C.bake_path(orb, range(F0, F1 + 1), lambda f: dict(location=tuple(light_pos(f))))
for f, k in ((F0, 0.0), (L_APPEAR, 0.0), (L_GO, 1.0)):
    orb_em.inputs["Strength"].default_value = 90.0 * k
    orb_em.inputs["Strength"].keyframe_insert("default_value", frame=f)
    ld.energy = 9.0 * k
    ld.keyframe_insert("energy", frame=f)
C.set_easing(M_orb.node_tree, "EASE_IN_OUT")
C.set_easing(ld, "EASE_IN_OUT")

# --------------------------------------------------------------------------- tracking: lagged targets + constraints
BLUE, BLUE_LOCK = (0.15, 0.45, 1.0, 1.0), (0.45, 0.75, 1.0, 1.0)  # blue status LEDs; lock-on = brighter pulse
for name, s in SCHED.items():
    c = CAMS[name]
    tgt = empty(f"{name}_TARGET")
    C.bake_path(tgt, range(F0, F1 + 1), lambda f, lag=s["lag"]: dict(location=tuple(light_pos(f - lag))))
    lt = c["pan"].constraints.new("LOCKED_TRACK")
    lt.target, lt.track_axis, lt.lock_axis = tgt, "TRACK_Y", "LOCK_Z"
    dt = c["tilt"].constraints.new("DAMPED_TRACK")
    dt.target, dt.track_axis = tgt, "TRACK_Y"
    for con in (lt, dt):
        for f, v in ((F0, 0.0), (s["lock"], 0.0), (s["lock"] + 7, 1.0)):
            con.influence = v
            con.keyframe_insert("influence", frame=f)
    led = c["led"]
    for f, col, k in ((F0, BLUE, 6.0), (s["lock"] + 6, BLUE, 6.0), (s["lock"] + 7, BLUE_LOCK, 24.0), (s["lock"] + 12, BLUE, 10.0)):
        led.inputs["Color"].default_value = col
        led.inputs["Color"].keyframe_insert("default_value", frame=f)
        led.inputs["Strength"].default_value = k
        led.inputs["Strength"].keyframe_insert("default_value", frame=f)
    for idb in (c["pan"], c["tilt"]):
        for fc in C.fcurves_of(idb):
            if "influence" in fc.data_path:
                for kp in fc.keyframe_points:
                    kp.interpolation, kp.easing = "SINE", "EASE_IN_OUT"
    for fc in C.fcurves_of(led.id_data):
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT"

# --------------------------------------------------------------------------- security monitor (wall, right side)
MON_Y, MON_Z = 6.4, 2.32
mon = empty("MONITOR", (-X0 - 0.02, MON_Y, MON_Z), rot=(0, 0, math.radians(-90 + 18)))  # screen (local −Y) faces −X, turned 18° toward −Y
SW, SH = 0.80, 0.45
bm = box_bm(SW + 0.03, 0.035, SH + 0.03, (0, 0.03, 0))
new_obj("MONITOR_body", bm, [M_black], mon, bevel=0.004)
bm = box_bm(0.06, 0.16, 0.06, (0, 0.11, 0))  # wall arm
new_obj("MONITOR_arm", bm, [M_grey], mon, bevel=0.004)
mon.location = Vector((-X0 - 0.19, MON_Y, MON_Z))
scr_bm = bmesh.new()
vs = [scr_bm.verts.new(v) for v in ((-SW / 2, 0.011, -SH / 2), (SW / 2, 0.011, -SH / 2), (SW / 2, 0.011, SH / 2), (-SW / 2, 0.011, SH / 2))]
fc_ = scr_bm.faces.new(vs)
uv = scr_bm.loops.layers.uv.new("UVMap")
for loop, (a, b) in zip(fc_.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
    loop[uv].uv = (a, b)
fc_.normal_update()
if fc_.normal.y > 0:
    fc_.normal_flip()
M_screen_tmp = principled("S03_monitor_standby", (0.004, 0.006, 0.01, 1), rough=0.2)
screen = new_obj("MONITOR_screen", scr_bm, [M_screen_tmp], mon)
screen.location.y = -0.0  # front face of the body is at local y = 0.0125 − 0.0175 … screen sits on it
screen.location.y = -0.003

# --------------------------------------------------------------------------- film camera
rig, cam, focus = C.make_camera_rig("RIG_S03", lens=24.0, location=(0, 0, 4), rotation=(0, 0, 0), fstop=4.0)
cam.data.clip_start = 0.004
focus.parent = CAMS["CCTV_dome"]["tilt"]
focus.location = CAMS["CCTV_dome"]["lens"]

# Lens axis at the end: dome pivot → hover point (the dome looks back along the film camera's path)
AXIS = (HOVER - DOME_PIVOT).normalized()  # from the lens toward the camera
LENS_FRONT = DOME_PIVOT + AXIS * CAMS["CCTV_dome"]["lens"].y
CUT = LENS_FRONT - AXIS * 0.012  # EXIT point: 12 mm inside the front element
anchor = empty("EXIT_ANCHOR_C", CUT)
anchor.rotation_euler = (-AXIS).to_track_quat("-Z", "Y").to_euler()  # anchor −Z = view toward the lens
bpy.context.view_layer.update()
slab_anchor = C.slab_handoff_matrix(slab).translation.copy()

S_SPEED = C.HANDOFF_TYPES["S"]["speed"]
C_SPEED = C.HANDOFF_TYPES[C.handoff_for(SCENE_ID, "EXIT")]["speed"]
E_HOLD = 6
ENTRY_END = F0 + E_HOLD  # 456
EXIT_START = F1 - E_HOLD  # 593


def hermite(p0, m0, p1, m1, t):
    h00, h10 = 2 * t ** 3 - 3 * t ** 2 + 1, t ** 3 - 2 * t ** 2 + t
    h01, h11 = -2 * t ** 3 + 3 * t ** 2, t ** 3 - t ** 2
    return p0 * h00 + m0 * h10 + p1 * h01 + m1 * h11


P_ENTRY = slab_anchor + Vector((0, 0, -S_SPEED * (ENTRY_END - F0 + 1)))  # pose at 456
V_ENTRY = Vector((0, 0, -S_SPEED))
CRANE_END, CRANE_P, CRANE_V = 470, Vector((0.0, 2.5, 2.65)), Vector((0.0, 0.04, -0.0005))  # swoop: down → forward, no overshoot
PUSH_START = 568
S_PUSH = 3.8  # distance along the axis from the cut point at the push start
P_PUSH = CUT + AXIS * S_PUSH
V_PUSH = -AXIS * 0.055
P_EXIT0 = CUT + AXIS * (C_SPEED * E_HOLD)  # pose at 593


def cam_position(f):
    if f <= ENTRY_END:
        return slab_anchor + Vector((0, 0, -S_SPEED * (f - F0 + 1)))
    if f <= CRANE_END:
        n = CRANE_END - ENTRY_END
        return hermite(P_ENTRY, V_ENTRY * n, CRANE_P, CRANE_V * n, (f - ENTRY_END) / n)
    if f <= PUSH_START:
        n = PUSH_START - CRANE_END
        return hermite(CRANE_P, CRANE_V * n, P_PUSH, V_PUSH * n, (f - CRANE_END) / n)
    if f <= EXIT_START:
        n = EXIT_START - PUSH_START
        s = hermite(S_PUSH, -0.055 * n, C_SPEED * E_HOLD, -C_SPEED * n, (f - PUSH_START) / n)
        return CUT + AXIS * s
    return CUT + AXIS * (C_SPEED * (F1 - f))


def look_angles(d: Vector):
    """Rig euler (pitch about X, 0, yaw about Z): pitch 0 = straight down, 90° = horizontal; yaw 0 = +Y."""
    d = d.normalized()
    return math.atan2(math.hypot(d.x, d.y), -d.z), math.atan2(-d.x, d.y)


def bump(f, a, b, c_, d):
    """0 before a, eases to 1 by b, holds, eases back to 0 from c_ to d."""
    return C.smootherstep((f - a) / (b - a)) * (1 - C.smootherstep((f - c_) / (d - c_)))


prev = [None]


def cam_pose(f):
    p = cam_position(f)
    if f <= ENTRY_END:
        return dict(location=tuple(p), rotation=(0.0, 0.0, 0.0))
    target = LENS_FRONT
    pitch_t, yaw_t = look_angles(target - p)
    if f >= EXIT_START:
        pitch_t, yaw_t = look_angles(-AXIS)
    w = C.smootherstep((f - (ENTRY_END + 1)) / (CRANE_END + 8 - (ENTRY_END + 1)))  # tilt up from straight down
    yaw_off = math.radians(-13.0) * bump(f, 516, 540, 552, 568)  # glance toward the security monitor
    pitch_off = math.radians(-6.0) * bump(f, 516, 540, 552, 568)  # … which hangs a little lower
    return dict(location=tuple(p), rotation=(pitch_t * w + pitch_off * w, 0.0, (yaw_t + yaw_off) * w))


C.bake_path(rig, range(ENTRY_END + 1, EXIT_START), cam_pose)
entry_anchor = empty("ENTRY_ANCHOR_S", slab_anchor)
bpy.context.view_layer.update()
C.key_handoff(rig, cam, SCENE_ID, "ENTRY", entry_anchor)
C.key_handoff(rig, cam, SCENE_ID, "EXIT", anchor)
C.set_lens(cam, 24.0, frame=ENTRY_END + 1, allow_special=True)
C.set_lens(cam, 35.0, frame=CRANE_END + 14)
for fc in C.fcurves_of(cam.data):
    for kp in fc.keyframe_points:
        if ENTRY_END < kp.co.x < EXIT_START:
            kp.interpolation, kp.easing = "SINE", "EASE_IN_OUT"
# DOF off during the slab pass (storyboard), on in the corridor
for f, v in ((F0, False), (ENTRY_END + 4, True)):
    cam.data.dof.use_dof = v
    cam.data.dof.keyframe_insert("use_dof", frame=f)

# Slab isolation while the camera is inside the bottom deck (local z −1.2 … −1.05 → frames 450 … 453)
C.key_slab_isolation(F0, 453)

# --------------------------------------------------------------------------- probes, glare
pd = bpy.data.lightprobes.new("CORR_irradiance", "VOLUME")
probe = bpy.data.objects.new("CORR_irradiance", pd)
probe.location = (0.0, CORR_L / 2, ROOM_H / 2)
probe.scale = (CORR_W / 2 - 0.05, CORR_L / 2 - 0.05, ROOM_H / 2 - 0.02)
for prop, val in (("resolution_x", 4), ("resolution_y", 24), ("resolution_z", 5), ("capture_world", True),
                  ("dilation_radius", 2.0), ("surface_bias", 0.1), ("escape_bias", 0.2)):
    if hasattr(pd, prop):
        setattr(pd, prop, val)
world_coll.objects.link(probe)

ng = bpy.data.node_groups.new("S03_COMPOSITE", "CompositorNodeTree")
ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
rl = ng.nodes.new("CompositorNodeRLayers")
gl = ng.nodes.new("CompositorNodeGlare")
for t in ("Bloom", "Fog Glow"):
    try:
        gl.inputs["Type"].default_value = t
        break
    except TypeError:
        pass
for k, v in (("Threshold", 2.0), ("Strength", 0.6), ("Size", 0.5), ("Saturation", 1.0)):
    if k in gl.inputs:
        gl.inputs[k].default_value = v
go = ng.nodes.new("NodeGroupOutput")
ng.links.new(rl.outputs["Image"], gl.inputs["Image"])
ng.links.new(gl.outputs[0], go.inputs[0])
sc.compositing_node_group = ng
sc.render.use_compositing = True


def bake_probes():
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = probe
    probe.select_set(True)
    try:
        bpy.ops.object.lightprobe_cache_bake(subset="ALL")
        print("PROBES_BAKED")
    except RuntimeError as e:
        print(f"PROBE_BAKE_FAILED {e}")


sc.frame_set(520)
bake_probes()

# --------------------------------------------------------------------------- feeds: render the cameras' own views
FEED_CAMS = {}
for name, c in CAMS.items():
    fcd = bpy.data.cameras.new(f"{name}_FEEDCAM")
    fcd.lens, fcd.sensor_width, fcd.clip_start = 18.0, 36.0, 0.02  # wide CCTV view (virtual camera, not a film lens)
    fco = bpy.data.objects.new(f"{name}_FEEDCAM", fcd)
    world_coll.objects.link(fco)
    fco.parent = c["tilt"]
    fco.location = c["lens"] + Vector((0, 0.012, 0))
    fco.rotation_euler = (math.radians(90), 0, 0)
    FEED_CAMS[name] = fco

if not SKIP_FEEDS:
    film_cam = sc.camera
    keep = (sc.render.resolution_percentage, sc.eevee.taa_render_samples, sc.render.use_compositing, sc.render.filepath)
    sc.render.resolution_percentage = 25  # 480 × 270
    sc.eevee.taa_render_samples = 8
    sc.render.use_compositing = False
    screen.hide_render = True
    for name, fco in FEED_CAMS.items():
        sc.camera = fco
        out_dir = FEED_DIR / name
        out_dir.mkdir(parents=True, exist_ok=True)
        for f in range(FEED_FROM, F1 + 1):
            sc.frame_set(f)
            sc.render.filepath = str(out_dir / f"{f:04d}")
            bpy.ops.render.render(write_still=True)
        print("FEED", name, "done")
    screen.hide_render = False
    sc.camera = film_cam
    sc.render.resolution_percentage, sc.eevee.taa_render_samples, sc.render.use_compositing, sc.render.filepath = keep


# --------------------------------------------------------------------------- monitor material: 3 live feeds, CCTV look
def build_monitor_material():
    m = bpy.data.materials.new("S03_monitor_feeds")
    nt = m.node_tree
    nt.nodes.clear()
    N, L = nt.nodes, nt.links

    def mnode(op, a, b=None):
        n = N.new("ShaderNodeMath")
        n.operation = op
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                L.new(v, n.inputs[i])
        return n.outputs[0]

    uvn = N.new("ShaderNodeUVMap")
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(uvn.outputs[0], sep.inputs[0])
    u, v = sep.outputs["X"], sep.outputs["Y"]
    G = 0.008  # gutter
    split = 0.64
    # tiles: big left = dome (u 0..split), right top = bullet R, right bottom = bullet L
    tiles = [("CCTV_dome", 0.0, split - G / 2, 0.0, 1.0), ("CCTV_bulletR", split + G / 2, 1.0, 0.5 + G / 2, 1.0),
             ("CCTV_bulletL", split + G / 2, 1.0, 0.0, 0.5 - G / 2)]
    acc = None
    for name, u0, u1, v0, v1 in tiles:
        lu = mnode("DIVIDE", mnode("SUBTRACT", u, u0), u1 - u0)
        lv = mnode("DIVIDE", mnode("SUBTRACT", v, v0), v1 - v0)
        inside = mnode("MULTIPLY", mnode("MULTIPLY", mnode("GREATER_THAN", lu, 0.0), mnode("LESS_THAN", lu, 1.0)),
                       mnode("MULTIPLY", mnode("GREATER_THAN", lv, 0.0), mnode("LESS_THAN", lv, 1.0)))
        # cover-crop the 16:9 feed into the tile (aspect of tile in screen units)
        tile_aspect = ((u1 - u0) * SW) / ((v1 - v0) * SH)
        if tile_aspect < 16 / 9:  # tile narrower → crop sides
            k = tile_aspect / (16 / 9)
            lu2 = mnode("ADD", mnode("MULTIPLY", lu, k), (1 - k) / 2)
            lv2 = lv
        else:
            k = (16 / 9) / tile_aspect
            lu2 = lu
            lv2 = mnode("ADD", mnode("MULTIPLY", lv, k), (1 - k) / 2)
        cv = N.new("ShaderNodeCombineXYZ")
        L.new(lu2, cv.inputs[0])
        L.new(lv2, cv.inputs[1])
        tex = N.new("ShaderNodeTexImage")
        first = FEED_DIR / name / f"{FEED_FROM:04d}.png"
        img = bpy.data.images.load(str(first), check_existing=True)
        img.source = "SEQUENCE"
        tex.image = img
        tex.extension = "EXTEND"
        iu = tex.image_user
        iu.frame_duration = F1 - FEED_FROM + 1
        iu.frame_start = FEED_FROM
        iu.frame_offset = FEED_FROM - 1
        iu.use_auto_refresh = True
        L.new(cv.outputs[0], tex.inputs["Vector"])
        mx = N.new("ShaderNodeMix")
        mx.data_type = "RGBA"
        L.new(inside, mx.inputs["Factor"])
        if acc is None:
            mx.inputs["A"].default_value = (0.012, 0.014, 0.016, 1)  # gutters
        else:
            L.new(acc, mx.inputs["A"])
        L.new(tex.outputs["Color"], mx.inputs["B"])
        acc = mx.outputs["Result"]
    # CCTV look: mostly desaturated, slightly cool-green, gentle contrast, fine scanlines, vignette
    hsv = N.new("ShaderNodeHueSaturation")
    hsv.inputs["Saturation"].default_value = 0.35
    L.new(acc, hsv.inputs["Color"])
    tint = N.new("ShaderNodeMix")
    tint.data_type = "RGBA"
    tint.blend_type = "MULTIPLY"
    tint.inputs["Factor"].default_value = 1.0
    tint.inputs["B"].default_value = (0.86, 1.0, 0.95, 1)
    L.new(hsv.outputs[0], tint.inputs["A"])
    scan = mnode("ADD", mnode("MULTIPLY", mnode("SINE", mnode("MULTIPLY", v, 2 * math.pi * 180)), 0.06), 0.94)
    vig = mnode("SUBTRACT", 1.0, mnode("MULTIPLY", mnode("ADD", mnode("POWER", mnode("SUBTRACT", u, 0.5), 2.0),
                                                       mnode("POWER", mnode("SUBTRACT", v, 0.5), 2.0)), 0.9))
    gain = mnode("MULTIPLY", scan, vig)
    on = N.new("ShaderNodeValue")
    on.name = on.label = "feeds_on"
    on.outputs[0].default_value = 0.0
    on.outputs[0].keyframe_insert("default_value", frame=F0)
    on.outputs[0].default_value = 1.0
    on.outputs[0].keyframe_insert("default_value", frame=FEED_FROM)
    g2 = mnode("MULTIPLY", gain, on.outputs[0])
    sm = N.new("ShaderNodeMix")
    sm.data_type = "RGBA"
    sm.blend_type = "MULTIPLY"
    sm.inputs["Factor"].default_value = 1.0
    L.new(tint.outputs["Result"], sm.inputs["A"])
    cg = N.new("ShaderNodeCombineColor")
    for i in range(3):
        L.new(g2, cg.inputs[i])
    L.new(cg.outputs[0], sm.inputs["B"])
    em = N.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 1.6
    L.new(sm.outputs["Result"], em.inputs["Color"])
    # glossy glass front over the emission
    gls = N.new("ShaderNodeBsdfGlossy")
    gls.inputs["Roughness"].default_value = 0.08
    gls.inputs["Color"].default_value = (0.05, 0.05, 0.05, 1)
    add = N.new("ShaderNodeAddShader")
    L.new(em.outputs[0], add.inputs[0])
    L.new(gls.outputs[0], add.inputs[1])
    o = N.new("ShaderNodeOutputMaterial")
    L.new(add.outputs[0], o.inputs["Surface"])
    for fc in C.fcurves_of(nt):
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT"
    return m


if (FEED_DIR / "CCTV_dome" / f"{FEED_FROM:04d}.png").exists():
    screen.data.materials[0] = build_monitor_material()
else:
    print("NOTE: feeds not rendered yet — monitor shows standby (run without --skip-feeds)")

sc.camera = cam
sc.frame_set(F0)
sc["s03_notes"] = "ENTRY S (slab) 450–456, EXIT C (lens pass into CCTV_dome) 593–599. Feeds: renders/_cctv_feeds/."
print("saved", C.save_scene(SCENE_ID))
