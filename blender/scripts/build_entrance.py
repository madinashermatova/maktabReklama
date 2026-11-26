"""Builds the 3D replica of the REAL school entrance (assets/reference/entrance_front.jpg) → blender/kit/entrance.blend
and renders the photo-match view + a 50 % overlay on the photo.

    blender -b --factory-startup --python blender/scripts/build_entrance.py -- [--samples 64] [--res 50] [--no-render]

CAMERA SOLVE (photo 1280 × 720, see docs/storyboard.md → "1 → 2"):
  * camera level (verticals vertical), entrance facade parallel to the image plane (yaw < 1°)
  * vanishing point of the street direction = principal point = (681, 478) px  (roof edges, plinth, wall cable)
    → lens shift; 478 ≈ the centre of a 4:3 frame cropped to 16:9
  * focal length from the square checker paving: f ≈ 545 px  (≈ 15.3 mm on a 36 mm sensor; ±10 %)
  * metric scale ASSUMED: camera height 1.40 m (booth door ≈ 2.2 m, paving tiles ≈ 0.24 m) → facade plane at 8.48 m
WORLD: camera at (0, 0, 1.40) looking +Y; X right, Z up; ground z = 0; entrance facade plane y = 8.48.
Every element is placed by back-projecting measured photo pixels onto the plane it lies on (facade, side wall,
ground), so the replica overlays the photo by construction. Parts no photo shows (roof backs, courtyard depth,
building lengths) are neutral and contradict nothing visible.
"""

from __future__ import annotations

import math
import random
import sys
import time
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as C  # noqa: E402
import build_kit as K  # noqa: E402
from common.brand import SIGNBOARD_TEXT  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default


# --------------------------------------------------------------------------- camera solve
IMG_W, IMG_H = 1280, 720
F_PX = 545.0
PPX, PPY = 681.0, 478.0
CAM_H = 1.40
FACADE = F_PX * CAM_H / (568.0 - PPY)  # pillar/booth base at y = 568 px → 8.48 m
LENS_MATCH = 36.0 * F_PX / IMG_W  # 15.33 mm, sensor 36 mm horizontal fit
PHOTO_PATH = C.ASSETS_DIR / "reference" / "entrance_front.jpg"
FONT_PATH = C.ASSETS_DIR / "fonts" / "Montserrat-Bold.ttf"
TEX_DIR = C.ASSETS_DIR / "textures"


def bp(x, y, depth):
    """Photo pixel (x, y) on the plane at forward distance `depth` → world point."""
    return Vector(((x - PPX) * depth / F_PX, depth, CAM_H + (PPY - y) * depth / F_PX))


def depth_on_wall(x, wall_x):
    """Forward distance of image column x on a receding wall plane X = wall_x."""
    return wall_x * F_PX / (x - PPX)


def ground_depth(y):
    return F_PX * CAM_H / (y - PPY)


# --------------------------------------------------------------------------- scene setup
C.reset_scene()
sc = bpy.context.scene
sc.name = "ENTRANCE"
C.apply_render_settings(sc, samples=int(arg("--samples", "64")))
sc.render.resolution_percentage = int(arg("--res", "50"))
root = bpy.data.collections.new("ENTRANCE_REPLICA")
sc.collection.children.link(root)


def coll(name):
    c = bpy.data.collections.new(name)
    root.children.link(c)
    return c


def obj(name, bm, mats, c, bevel=0.004, smooth=False):
    return K.finish_object(name, bm, mats, c, bevel=bevel, smooth=smooth)


def box(bm, x0, x1, y0, y1, z0, z1, mi=0):
    K.add_box(bm, min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1), min(z0, z1), max(z0, z1), mi)


# --------------------------------------------------------------------------- materials
def m_simple(name, hexc, rough=0.6, metal=0.0, vary=0.0, coat=0.0):
    return K.mat_simple(name, hexc, rough=rough, metal=metal, vary=vary, coat=coat)


def m_masked(name, hexc, mask_file, tile_m, rough=0.45, metal=0.6, glass=False):
    """Laser-cut / etched panel: image mask on 1 UV unit = 1 m (box_uv), repeated every `tile_m` metres."""
    m, nt, b = K.new_material(name)
    img = bpy.data.images.load(str(mask_file), check_existing=True)
    img.colorspace_settings.name = "Non-Color"
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Cubic"
    nt.links.new(K.uv_vec(nt, scale=(1 / tile_m, 1 / tile_m, 1)), tex.inputs["Vector"])
    K.bsdf_set(b, color=C.hex_rgba(hexc), rough=rough, metal=metal)
    if glass:  # etched glass: frosted where the mask is metal-white, clear in the gaps
        K.bsdf_set(b, transmission=1.0, metal=0.0)
        nt.links.new(K.map_range(nt, tex.outputs["Color"], 0.05, 0.45), b.inputs["Roughness"])
        if "Thin Wall" in b.inputs:
            b.inputs["Thin Wall"].default_value = True
    else:
        nt.links.new(tex.outputs["Color"], b.inputs["Alpha"])
    for prop, val in (("surface_render_method", "DITHERED"), ("use_raytrace_refraction", glass)):
        try:
            setattr(m, prop, val)
        except (AttributeError, TypeError):
            pass
    return m


def m_paving():
    m, nt, b = K.new_material("ENT_paving_checker")
    vec = K.uv_vec(nt)
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.offset, br.offset_frequency = 0.0, 1
    for k, v in (("Scale", 1.0), ("Brick Width", 0.24), ("Row Height", 0.24), ("Mortar Size", 0.0025),
                 ("Mortar Smooth", 0.4), ("Bias", 0.0), ("Color1", C.hex_rgba("#ADB1B6")), ("Color2", C.hex_rgba("#7C8187")),
                 ("Mortar", C.hex_rgba("#5E6266"))):
        K._sock(br, k, v)
    nt.links.new(vec, br.inputs["Vector"])
    ck = nt.nodes.new("ShaderNodeTexChecker")
    ck.inputs["Scale"].default_value = 1.0 / 0.48 * 2  # checker cell = 0.24 m (Generated scale ×2)
    ck.inputs["Color1"].default_value = (1, 1, 1, 1)
    ck.inputs["Color2"].default_value = (0.78, 0.79, 0.8, 1)
    nt.links.new(vec, ck.inputs["Vector"])
    col = K.mix_color(nt, br.outputs["Color"], ck.outputs["Color"], 0.75, "MULTIPLY")
    col = K.mix_color(nt, col, K.ramp(nt, K.noise(nt, vec, 1.5, 6.0, 0.6).outputs["Fac"],
                                      [(0.3, (0.88, 0.88, 0.88, 1)), (0.7, (1.0, 1.0, 1.0, 1))]), 1.0, "MULTIPLY")
    nt.links.new(col, b.inputs["Base Color"])
    nt.links.new(K.map_range(nt, K.noise(nt, vec, 30.0, 4.0, 0.6).outputs["Fac"], 0.55, 0.8), b.inputs["Roughness"])
    inv = nt.nodes.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    nt.links.new(br.outputs["Fac"], inv.inputs[1])
    K.bump(nt, b, inv.outputs[0], 0.25, 0.003)
    return m


def m_plaster(name, hexc, stain=0.10, dirt=0.22, rough=0.88):
    """Weathered render: large soft tonal blotches, faint vertical rain stains, fine trowel bump, and dirt that
    darkens the bottom ~0.5 m of every wall (world Z), broken up by noise."""
    m, nt, b = K.new_material(name)
    base = C.hex_rgba(hexc)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    pos = geo.outputs["Position"]
    blot = K.noise(nt, pos, 0.35, 4.0, 0.55)
    col = K.ramp(nt, blot.outputs["Fac"], [(0.35, K.shade(base, 0.94)), (0.5, base), (0.68, K.shade(base, 1.025))])
    mp = nt.nodes.new("ShaderNodeMapping")  # stretched in Z → vertical streaks
    mp.inputs["Scale"].default_value = (3.0, 3.0, 0.25)
    nt.links.new(pos, mp.inputs["Vector"])
    streak = K.noise(nt, mp.outputs["Vector"], 2.5, 6.0, 0.6)
    s_mask = K.map_range(nt, streak.outputs["Fac"], -0.9, 1.0)  # → mostly < 0, clamped below
    cl = nt.nodes.new("ShaderNodeClamp")
    nt.links.new(s_mask, cl.inputs["Value"])
    s_amt = nt.nodes.new("ShaderNodeMath")
    s_amt.operation = "MULTIPLY"
    s_amt.inputs[1].default_value = stain
    nt.links.new(cl.outputs[0], s_amt.inputs[0])
    col = K.mix_color(nt, col, K.shade(base, 0.72), s_amt.outputs[0])
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(pos, sep.inputs[0])
    zr = nt.nodes.new("ShaderNodeMapRange")  # 1 at the ground → 0 at 0.55 m
    zr.inputs["From Min"].default_value, zr.inputs["From Max"].default_value = 0.0, 0.55
    zr.inputs["To Min"].default_value, zr.inputs["To Max"].default_value = 1.0, 0.0
    nt.links.new(sep.outputs["Z"], zr.inputs["Value"])
    dn = K.noise(nt, pos, 3.0, 5.0, 0.6)
    dm = nt.nodes.new("ShaderNodeMath")
    dm.operation = "MULTIPLY"
    dm.use_clamp = True
    nt.links.new(zr.outputs["Result"], dm.inputs[0])
    nt.links.new(K.map_range(nt, dn.outputs["Fac"], 0.2, 1.4), dm.inputs[1])
    dm2 = nt.nodes.new("ShaderNodeMath")
    dm2.operation = "MULTIPLY"
    dm2.inputs[1].default_value = dirt
    nt.links.new(dm.outputs[0], dm2.inputs[0])
    col = K.mix_color(nt, col, C.hex_rgba("#4A4238"), dm2.outputs[0])
    nt.links.new(col, b.inputs["Base Color"])
    nt.links.new(K.map_range(nt, blot.outputs["Fac"], rough - 0.06, rough + 0.04), b.inputs["Roughness"])
    K.bump(nt, b, K.noise(nt, pos, 140.0, 8.0, 0.7).outputs["Fac"], 0.22, 0.003)
    return m


def m_frosted(name, hexc, mask_file, tile_m, etch=0.12):
    """Frosted security glass with an etched geometric pattern — opaque-looking (no refraction needed):
    soft satin sheen, pattern slightly lighter and rougher."""
    m, nt, b = K.new_material(name)
    img = bpy.data.images.load(str(mask_file), check_existing=True)
    img.colorspace_settings.name = "Non-Color"
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    nt.links.new(K.uv_vec(nt, scale=(1 / tile_m, 1 / tile_m, 1)), tex.inputs["Vector"])
    base = C.hex_rgba(hexc)
    nt.links.new(K.mix_color(nt, K.shade(base, 1.0 + etch), base, tex.outputs["Color"]), b.inputs["Base Color"])
    nt.links.new(K.map_range(nt, tex.outputs["Color"], 0.38, 0.12), b.inputs["Roughness"])
    K.bsdf_set(b, coat=0.6, coat_rough=0.05)
    return m


def m_emit_letters():
    m = bpy.data.materials.new("ENT_sign_letters")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = C.hex_rgba("#FFC93C")  # warm yellow; moderate strength so AgX keeps the hue
    em.inputs["Strength"].default_value = 4.0
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m


Mk = K.build_materials()  # kit materials (glass, frame, leaves, bark, steel …)
M = dict(
    pillar=m_simple("ENT_pillar_dark_grey", "#45484D", rough=0.45, coat=0.2),
    groove=m_simple("ENT_pillar_groove", "#D9DADB", rough=0.35, metal=0.3),
    sign_board=m_simple("ENT_sign_board", "#1C232C", rough=0.35, coat=0.4),
    sign_edge=m_simple("ENT_sign_edge", "#C9CDD6", rough=0.3, metal=0.5),
    letters=m_emit_letters(),
    soffit=m_simple("ENT_soffit", "#B9BBBE", rough=0.7),
    gate=m_masked("ENT_gate_lasercut", "#2B2E32", TEX_DIR / "gate_pattern.png", 0.42, rough=0.4, metal=0.7),
    gate_frame=m_simple("ENT_gate_frame", "#2B2E32", rough=0.4, metal=0.6),
    booth=m_simple("ENT_booth_wall", "#55585D", rough=0.55),
    booth_roof=m_simple("ENT_booth_roof", "#4B4E53", rough=0.5),
    fascia_light=m_simple("ENT_fascia_light", "#E6E7E8", rough=0.4),
    booth_glass=m_frosted("ENT_booth_glass_frosted", "#8F989E", TEX_DIR / "booth_glass_pattern.png", 0.22),
    booth_glass_dark=m_frosted("ENT_booth_glass_tinted", "#5D666D", TEX_DIR / "booth_glass_pattern.png", 0.22, etch=0.25),
    wall_light=m_plaster("ENT_wall_light_grey", "#D3D5D7"),
    wall_left=m_plaster("ENT_boundary_wall", "#C4C6C8", stain=0.14, dirt=0.3),
    wall_left_b=m_plaster("ENT_boundary_wall_light", "#CFD1D3", stain=0.12, dirt=0.28),
    wall_frame=m_simple("ENT_wall_frame_grey", "#8E9196", rough=0.7),
    coping=m_simple("ENT_coping", "#9DA0A4", rough=0.6),
    plinth=m_simple("ENT_plinth_grey", "#80848A", rough=0.7),
    cream=m_plaster("ENT_cream_render", "#E0D3B6", stain=0.12, dirt=0.15),
    roof_brown=m_simple("ENT_roof_brown", "#6A4631", rough=0.5, metal=0.2),
    pvc=m_simple("ENT_window_frame_white", "#E9E9E6", rough=0.4),
    win_frame_grey=m_simple("ENT_window_frame_grey", "#A7ABB0", rough=0.45),
    win_glass=m_simple("ENT_window_glass_dark", "#59626B", rough=0.05, coat=0.8),
    pipe=m_simple("ENT_downpipe", "#A3A6AA", rough=0.4, metal=0.4),
    canopy=m_simple("ENT_canopy_frame_white", "#EEEEEC", rough=0.35, metal=0.2),
    cable=m_simple("ENT_cable", "#6E7378", rough=0.4, metal=0.6),
    cctv=m_simple("ENT_cctv_housing", "#ECECEA", rough=0.35),
    lens=m_simple("ENT_cctv_lens", "#101114", rough=0.05, coat=1.0),
    paving=m_paving(),
    asphalt=K.mat_concrete("ENT_asphalt", "#76787B", rough=0.85),
    kerb_line=m_simple("ENT_kerb_line", "#D9DAD8", rough=0.6),
    shutter=m_simple("ENT_roller_shutter", "#878B90", rough=0.55, metal=0.15),
    box_grey=m_simple("ENT_electric_box", "#D9DADB", rough=0.5),
    courtyard_wall=m_plaster("ENT_courtyard_render", "#D9D4CB", stain=0.1, dirt=0.25),
    ac=m_simple("ENT_ac_unit", "#E4E5E3", rough=0.45),
    ac_grille=m_simple("ENT_ac_grille", "#3B3E42", rough=0.5, metal=0.5),
    wood_door=m_simple("ENT_wood_door", "#6B4A30", rough=0.45, coat=0.3),
    palm=m_simple("ENT_palm_leaf", "#3E6B2E", rough=0.55),
    door_dark=m_simple("ENT_door_dark", "#2E3034", rough=0.4),
    pot=m_simple("ENT_planter_pot", "#5B4636", rough=0.7),
    lamp=K.mat_emit("ENT_niche_lamp", 4000, 3.0),
)
M["leaves"] = Mk["leaves"]
M["bark"] = Mk["bark"]

# --------------------------------------------------------------------------- ground
c = coll("ENT_ground")
yl0, yl1 = ground_depth(665), ground_depth(705)  # kerb line (300, 665) → (1100, 705)
p_l, p_r = bp(300, 665, yl0), bp(1100, 705, yl1)
bm = bmesh.new()  # paving: everything beyond the kerb line (the line is slightly skewed in the photo)
slope = (p_r.y - p_l.y) / (p_r.x - p_l.x)
xs = (-30.0, 30.0)
ys = [p_l.y + slope * (x - p_l.x) for x in xs]
vs = [bm.verts.new(v) for v in ((xs[0], ys[0], 0), (xs[1], ys[1], 0), (xs[1], 60, 0), (xs[0], 60, 0))]
bm.faces.new(vs)
obj("paving", bm, [M["paving"]], c, bevel=0)
bm = bmesh.new()
vs = [bm.verts.new(v) for v in ((xs[0], ys[0] - 0.12, 0.004), (xs[1], ys[1] - 0.12, 0.004), (xs[1], ys[1], 0.004), (xs[0], ys[0], 0.004))]
bm.faces.new(vs)
obj("kerb_line", bm, [M["kerb_line"]], c, bevel=0)
bm = bmesh.new()
vs = [bm.verts.new(v) for v in ((xs[0], -10, -0.01), (xs[1], -10, -0.01), (xs[1], ys[1], -0.01), (xs[0], ys[0], -0.01))]
bm.faces.new(vs)
obj("street_asphalt", bm, [M["asphalt"]], c, bevel=0)

# --------------------------------------------------------------------------- entrance: pillars, sign, soffit
c = coll("ENT_entrance")
PW = 0.78  # square pillars
LP_X0 = bp(345, 568, FACADE).x
RP_X0 = bp(812, 568, FACADE).x
PILLAR_TOP = 4.45
groove_z = [0.62 + k * 0.64 for k in range(6)]
bm, bg = bmesh.new(), bmesh.new()
for x0 in (LP_X0, RP_X0):
    box(bm, x0, x0 + PW, FACADE, FACADE + PW, 0, PILLAR_TOP)
    for z in groove_z:  # horizontal grooves: 18 mm light inlay, slightly recessed look via bevelled edges
        box(bg, x0 - 0.004, x0 + PW + 0.004, FACADE - 0.004, FACADE + PW + 0.004, z - 0.009, z + 0.009)
obj("pillars", bm, [M["pillar"]], c, bevel=0.006)
obj("pillar_grooves", bg, [M["groove"]], c, bevel=0)

SIGN_Y = FACADE - 0.22
s_l, s_r = bp(272, 280, SIGN_Y), bp(925, 218, SIGN_Y)
bm = bmesh.new()
box(bm, s_l.x, s_r.x, SIGN_Y, FACADE + 0.25, s_l.z, s_r.z)
obj("sign_board", bm, [M["sign_board"]], c, bevel=0.008)
bm = bmesh.new()
box(bm, s_l.x, s_r.x, SIGN_Y - 0.012, FACADE + 0.25, s_r.z - 0.03, s_r.z + 0.004)
obj("sign_top_edge", bm, [M["sign_edge"]], c, bevel=0.002)
bm = bmesh.new()  # passage roof / soffit behind the sign (seen from below)
soff_z = bp(500, 292, FACADE).z
box(bm, s_l.x + 0.2, s_r.x - 0.2, FACADE - 0.05, FACADE + 1.55, soff_z, s_l.z)
obj("passage_soffit", bm, [M["soffit"]], c, bevel=0.004)

# Signboard text — exactly as the real sign (common/brand.py → SIGNBOARD_TEXT), Montserrat Bold, never Bfont
font = bpy.data.fonts.load(str(FONT_PATH), check_existing=True)
cu = bpy.data.curves.new("sign_text", "FONT")
cu.body = SIGNBOARD_TEXT
cu.font = cu.font_bold = font
cu.align_x, cu.align_y = "CENTER", "CENTER"
cu.size = 0.6
cu.extrude = 0.012
cu.materials.append(M["letters"])
txt = bpy.data.objects.new("sign_text", cu)
c.objects.link(txt)
t_l, t_r = bp(322, 244, SIGN_Y - 0.02), bp(868, 244, SIGN_Y - 0.02)
txt.location = ((t_l.x + t_r.x) / 2, SIGN_Y - 0.015, t_l.z)
txt.rotation_euler = (math.radians(90), 0, 0)
bpy.context.view_layer.update()
width_now = txt.dimensions.x
txt.scale = ((t_r.x - t_l.x) / width_now,) * 3  # letter size & spacing to the photographed width
txt["text_check"] = SIGNBOARD_TEXT

# --------------------------------------------------------------------------- gate (laser-cut, two leaves)
c = coll("ENT_gate")
GY = FACADE + 0.02
g_l, g_r = bp(413, 575, GY), bp(640, 575, GY)
g_top = bp(413, 393, GY).z
g_mid = bp(500, 575, GY).x
fz = [(bp(0, 420, GY).z, g_top), (0.08, bp(0, 535, GY).z)]  # perforated top frieze, bottom kick panel
bm, bp_ = bmesh.new(), bmesh.new()
for x0, x1 in ((g_l.x, g_mid), (g_mid, g_r.x)):
    t = 0.05
    for xx in (x0, x1 - t):
        box(bm, xx, xx + t, GY, GY + 0.06, 0.06, g_top)  # stiles
    for z0, z1 in fz:
        box(bm, x0, x1, GY, GY + 0.06, z0 - t / 2, z0 + t / 2)
        box(bm, x0, x1, GY, GY + 0.06, z1 - t / 2, z1 + t / 2)
        box(bp_, x0 + t, x1 - t, GY + 0.025, GY + 0.035, z0 + t / 2, z1 - t / 2)
    # open middle: slim vertical bars every 0.11 m
    zb0, zb1 = fz[1][1], fz[0][0]
    n = int((x1 - x0) / 0.11)
    for k in range(1, n):
        xx = x0 + k * (x1 - x0) / n
        box(bm, xx - 0.009, xx + 0.009, GY + 0.02, GY + 0.04, zb0, zb1)
obj("gate_frame", bm, [M["gate_frame"]], c, bevel=0.003)
obj("gate_lasercut_panels", bp_, [M["gate"]], c, bevel=0)

# --------------------------------------------------------------------------- guard booth (right of the gate)
c = coll("ENT_booth")
b_x0, b_x1 = bp(695, 568, FACADE).x, RP_X0
roof_l, roof_r = bp(683, 372, FACADE - 0.2), bp(872, 336, FACADE - 0.2)
bm = bmesh.new()
box(bm, b_x0, b_x1, FACADE, FACADE + 2.4, 0, roof_l.z)
obj("booth_body", bm, [M["booth"]], c, bevel=0.006)
bm = bmesh.new()
box(bm, roof_l.x, roof_r.x, FACADE - 0.2, FACADE + 2.7, roof_l.z + 0.07, roof_r.z)
obj("booth_roof", bm, [M["booth_roof"]], c, bevel=0.006)
bm = bmesh.new()
box(bm, roof_l.x, roof_r.x, FACADE - 0.2 - 0.004, FACADE + 2.7, roof_l.z, roof_l.z + 0.07)
obj("booth_roof_fascia", bm, [M["fascia_light"]], c, bevel=0.002)
bm, bgl = bmesh.new(), bmesh.new()
d1x0, d1x1 = bp(700, 0, FACADE).x, bp(755, 0, FACADE).x
d2x1 = bp(805, 0, FACADE).x
dz1 = bp(0, 395, FACADE).z
for x0, x1 in ((d1x0, d1x1), (d1x1, d2x1)):
    for xx in (x0, x1 - 0.05):
        box(bm, xx, xx + 0.05, FACADE - 0.03, FACADE + 0.02, 0.0, dz1)
    box(bm, x0, x1, FACADE - 0.03, FACADE + 0.02, dz1 - 0.05, dz1)
    box(bm, x0, x1, FACADE - 0.03, FACADE + 0.02, 0.0, 0.12)
    box(bm, x0, x1, FACADE - 0.03, FACADE + 0.02, 1.0, 1.05)  # mid rail
obj("booth_door_frames", bm, [M["gate_frame"]], c, bevel=0.002)
# as photographed: left door = laser-cut metal top panel over pale frosted glass; right door = darker etched glass
top_pz = bp(0, 440, FACADE).z
bgl, bdk, bpn = bmesh.new(), bmesh.new(), bmesh.new()
box(bpn, d1x0 + 0.05, d1x1 - 0.05, FACADE - 0.02, FACADE - 0.012, top_pz, dz1 - 0.05)
box(bgl, d1x0 + 0.05, d1x1 - 0.05, FACADE - 0.012, FACADE - 0.006, 0.12, top_pz)
box(bgl, d1x0 + 0.05, d1x1 - 0.05, FACADE - 0.010, FACADE - 0.006, top_pz, dz1 - 0.05)  # glass behind the panel
box(bdk, d1x1 + 0.05, d2x1 - 0.05, FACADE - 0.012, FACADE - 0.006, 0.12, dz1 - 0.05)
obj("booth_door_glass_frosted", bgl, [M["booth_glass"]], c, bevel=0)
obj("booth_door_glass_etched", bdk, [M["booth_glass_dark"]], c, bevel=0)
obj("booth_door_lasercut_panel", bpn, [M["gate"]], c, bevel=0)
bm = bmesh.new()  # dark interior behind the glass
box(bm, b_x0 + 0.05, b_x1 - 0.05, FACADE + 0.15, FACADE + 0.2, 0.0, dz1)
obj("booth_interior", bm, [M["door_dark"]], c, bevel=0)

# --------------------------------------------------------------------------- boundary walls on the facade line
c = coll("ENT_walls")
lw_top = bp(0, 392, FACADE).z
lw_x0 = bp(0, 568, FACADE).x - 4.0


def px_x(x, y_=FACADE):
    return bp(x, 0, y_).x


def px_z(y, y_=FACADE):
    return bp(0, y, y_).z


def rounded_top_fill(bm, x0, x1, z_top, r, yf, yb):
    """Quarter-round infills in the two top corners of a rectangular opening → rounded-top opening."""
    for cx, sgn in ((x0 + r, -1), (x1 - r, 1)):
        pts = [(cx + sgn * r, z_top)]
        for k in range(0, 9):
            a = math.radians(90 * k / 8)
            pts.append((cx + sgn * r * math.sin(a), z_top - r + r * math.cos(a)))
        vf = [bm.verts.new((x, yf, z)) for x, z in pts]
        vb = [bm.verts.new((x, yb, z)) for x, z in pts]
        bm.faces.new(vf)
        bm.faces.new(list(reversed(vb)))
        for i in range(len(pts)):
            j = (i + 1) % len(pts)
            bm.faces.new([vf[i], vf[j], vb[j], vb[i]])


# The left boundary wall exactly as photographed (left → right):
#  segment A (… → x 178 px), set 4 cm back: two rounded-top window openings in grey rectangular surrounds
#  (one cut by the photo's left edge), an electrical box, a downpipe that curves up-left to the coping;
#  segment B (x 178 → left pillar), lighter: grey-framed doorway = rounded-top transom window over a rolling shutter.
A_Y, B_Y = FACADE + 0.04, FACADE
ax0, ax1 = lw_x0, px_x(178, A_Y)
win_z0, win_z1 = px_z(452, A_Y), px_z(432, A_Y)
win_specs = [(px_x(-14, A_Y), px_x(25, A_Y)), (px_x(41, A_Y), px_x(97, A_Y))]
openings = [(x0 - ax0, x1 - ax0, win_z0, win_z1) for x0, x1 in win_specs]
bm = K.wall_bm(ax1 - ax0, lw_top, 0.3, openings)
bmesh.ops.translate(bm, verts=bm.verts, vec=(ax0, A_Y, 0))
obj("left_wall_A", bm, [M["wall_left"]], c, bevel=0.003)
bm, bfill = bmesh.new(), bmesh.new()
fr = 0.09  # grey rectangular surround around each opening (photo: x 35–110 px, y 423–455 px)
for (x0, x1), (fx0, fx1) in zip(win_specs, ((px_x(-20, A_Y), px_x(32, A_Y)), (px_x(35, A_Y), px_x(110, A_Y)))):
    fz0, fz1 = px_z(456, A_Y), px_z(423, A_Y)
    box(bm, fx0, fx1, A_Y - 0.03, A_Y, fz1 - fr, fz1)
    box(bm, fx0, fx1, A_Y - 0.03, A_Y, fz0, fz0 + 0.05)
    box(bm, fx0, x0, A_Y - 0.03, A_Y, fz0, fz1)
    box(bm, x1, fx1, A_Y - 0.03, A_Y, fz0, fz1)
    rounded_top_fill(bfill, x0, x1, win_z1, 0.16, A_Y - 0.001, A_Y + 0.3)
obj("left_wall_A_window_surrounds", bm, [M["wall_frame"]], c, bevel=0.003)
obj("left_wall_A_window_round_tops", bfill, [M["wall_left"]], c, bevel=0)

bx0, bx1 = px_x(178, B_Y), LP_X0
d_x0, d_x1 = px_x(236, B_Y), px_x(303, B_Y)
d_z1 = px_z(432, B_Y)
bm = K.wall_bm(bx1 - bx0, lw_top, 0.3, [(d_x0 - bx0, d_x1 - bx0, 0.0, d_z1)])
bmesh.ops.translate(bm, verts=bm.verts, vec=(bx0, B_Y, 0))
obj("left_wall_B", bm, [M["wall_left_b"]], c, bevel=0.003)
bm = bmesh.new()  # grey door surround (x 228–312, y 420–558 px), 3 cm proud
sx0, sx1, sz1 = px_x(228, B_Y), px_x(312, B_Y), px_z(420, B_Y)
box(bm, sx0, sx1, B_Y - 0.03, B_Y, d_z1, sz1)
box(bm, sx0, d_x0, B_Y - 0.03, B_Y, 0.0, d_z1)
box(bm, d_x1, sx1, B_Y - 0.03, B_Y, 0.0, d_z1)
tr_z0 = px_z(450, B_Y)
box(bm, d_x0, d_x1, B_Y + 0.05, B_Y + 0.09, tr_z0 - 0.04, tr_z0)  # transom bar / shutter box
obj("left_door_surround", bm, [M["wall_frame"]], c, bevel=0.003)
bfill = bmesh.new()
rounded_top_fill(bfill, d_x0, d_x1, d_z1, 0.22, B_Y - 0.001, B_Y + 0.3)
obj("left_door_transom_round_top", bfill, [M["wall_left_b"]], c, bevel=0)
bm = bmesh.new()  # rolling shutter: 40 rounded slats, 10 cm back from the wall face
n_sl = 40
for k in range(n_sl):
    z0 = 0.02 + k * (tr_z0 - 0.06) / n_sl
    box(bm, d_x0 + 0.03, d_x1 - 0.03, B_Y + 0.10, B_Y + 0.12, z0, z0 + (tr_z0 - 0.06) / n_sl - 0.006)
obj("left_rolling_shutter", bm, [M["shutter"]], c, bevel=0.004)
for x0, x1, y_, z0, z1, nm in ((ax0, ax1, A_Y, lw_top, lw_top + 0.09, "A"), (bx0, bx1, B_Y, lw_top, lw_top + 0.09, "B")):
    bm = bmesh.new()
    box(bm, x0, x1, y_ - 0.05, y_ + 0.35, z0, z1)
    obj(f"left_wall_coping_{nm}", bm, [M["coping"]], c, bevel=0.004)
bm = bmesh.new()  # small switch box on segment B beside the pillar (x 340 px, y 458–470 px)
box(bm, px_x(335, B_Y), px_x(345, B_Y), B_Y - 0.06, B_Y, px_z(472, B_Y), px_z(456, B_Y))
obj("left_switch_box", bm, [M["box_grey"]], c, bevel=0.005)


def niche(name, x0px, x1px, top_px, bot_px, depth=0.12, mat_in=None, frame=True, wall_y=FACADE, lamp=False):
    """Arched wall niche: recessed panel with a semicircular head and a light surround."""
    a, b = bp(x0px, bot_px, wall_y), bp(x1px, top_px, wall_y)
    w = b.x - a.x
    r = w / 2
    z_spring = b.z - r
    bm = bmesh.new()
    pts = [(a.x, a.z), (b.x, a.z), (b.x, z_spring)]
    for k in range(1, 16):
        ang = math.pi * k / 16
        pts.append((a.x + r + r * math.cos(ang), z_spring + r * math.sin(ang)))
    pts.append((a.x, z_spring))
    v_back = [bm.verts.new((x, wall_y - 0.003 + depth, z)) for x, z in pts]
    bm.faces.new(v_back)
    obj(f"{name}_back", bm, [mat_in or M["wall_light"]], c, bevel=0)
    if frame:  # surround: thin raised band following the outline
        cu = bpy.data.curves.new(f"{name}_surround", "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = 0.035
        cu.bevel_resolution = 1
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts) - 1)
        for spt, (x, z) in zip(sp.points, pts):
            spt.co = (x, wall_y - 0.02, z, 1)
        cu.materials.append(M["coping"])
        ob = bpy.data.objects.new(f"{name}_surround", cu)
        c.objects.link(ob)
    if lamp:
        bm = bmesh.new()
        box(bm, a.x + r - 0.18, a.x + r + 0.18, wall_y + depth - 0.08, wall_y + depth - 0.003, z_spring + r * 0.55,
            z_spring + r * 0.75)
        obj(f"{name}_lamp", bm, [M["lamp"]], c, bevel=0.01)


# left wall: roller-shutter door with arched head, small arched opening, electrical box, pipe
bm = bmesh.new()
eb0, eb1 = bp(103, 542, A_Y), bp(150, 490, A_Y)
box(bm, eb0.x, eb1.x, A_Y - 0.16, A_Y, eb0.z, eb1.z)
obj("electrical_box", bm, [M["box_grey"]], c, bevel=0.01)
py_ = A_Y - 0.05  # downpipe: vertical at x 175 px, curving up-left to the coping outlet at x 152 px
pts = [bp(175, 562, py_), bp(175, 430, py_), bp(168, 412, py_), bp(152, 402, py_), bp(150, 394, py_ + 0.08)]
K.tube("left_wall_downpipe", [[tuple(p) for p in pts]], 0.035, M["pipe"], c, fillet=0.08)

# right low wall with arched niche + lamp, annex roof and terrace railing above
RW_X1 = 5.10
rw_top = bp(0, 385, FACADE).z
bm = bmesh.new()
box(bm, RP_X0 + PW, RW_X1, FACADE, FACADE + 0.3, 0, rw_top)
obj("right_low_wall", bm, [M["wall_light"]], c, bevel=0.004)
bm = bmesh.new()
box(bm, RP_X0 + PW, RW_X1, FACADE - 0.05, FACADE + 0.35, rw_top, rw_top + 0.1)
obj("right_wall_coping", bm, [M["coping"]], c, bevel=0.004)
niche("right_arch_niche", 915, 1000, 420, 560, depth=0.14, mat_in=M["fascia_light"], lamp=True)
annex_z = bp(0, 360, FACADE + 0.6).z
bm = bmesh.new()
box(bm, RP_X0 + PW, RW_X1, FACADE + 0.3, FACADE + 3.5, rw_top + 0.1, annex_z)
obj("right_annex", bm, [M["wall_light"]], c, bevel=0.004)
rails = []
ry = FACADE + 1.0
for z in (annex_z + 0.95, annex_z + 0.5):
    rails.append([(RP_X0 + PW + 0.2, ry, z), (RW_X1 - 0.15, ry, z)])
for k in range(9):
    x = RP_X0 + PW + 0.2 + k * (RW_X1 - 0.35 - RP_X0 - PW) / 8
    rails.append([(x, ry, annex_z), (x, ry, annex_z + 0.95)])
K.tube("terrace_railing", rails, 0.02, Mk["steel_brushed"], c, fillet=0.02)

# --------------------------------------------------------------------------- right building (light grey, grey plinth)
c = coll("ENT_right_building")
RX = RW_X1
EAVE_R = 7.48
bm = bmesh.new()
box(bm, RX, RX + 10, 2.5, 40, 0, EAVE_R)
obj("right_building", bm, [M["wall_light"]], c, bevel=0.01)
bm = bmesh.new()
plinth_z = bp(1090, 506, depth_on_wall(1090, RX)).z
box(bm, RX - 0.04, RX + 0.01, 2.5, FACADE, 0, plinth_z)
obj("right_plinth", bm, [M["plinth"]], c, bevel=0.006)
bm = bmesh.new()  # roof: shallow pitch up to a ridge 5 m in, overhang 0.35 m, grey edge
for ya, yb in ((2.2, 40.3),):
    vs = [bm.verts.new(v) for v in ((RX - 0.35, ya, EAVE_R - 0.02), (RX - 0.35, yb, EAVE_R - 0.02),
                                    (RX + 5.0, yb, EAVE_R + 1.6), (RX + 5.0, ya, EAVE_R + 1.6))]
    bm.faces.new(vs)
r = obj("right_roof", bm, [M["coping"]], c, bevel=0)
r.modifiers.new("Thick", "SOLIDIFY").thickness = 0.12
K.tube("right_gutter", [[(RX - 0.32, 2.2, EAVE_R - 0.08), (RX - 0.32, 40.3, EAVE_R - 0.08)]], 0.06, M["pipe"], c, fillet=0)
dp_y = depth_on_wall(1070, RX)
K.tube("right_downpipe", [[(RX - 0.32, dp_y, EAVE_R - 0.1), (RX - 0.1, dp_y, EAVE_R - 0.5), (RX - 0.1, dp_y, 0.25),
                           (RX - 0.25, dp_y, 0.05)]], 0.05, M["pipe"], c, fillet=0.15)
cab_a, cab_b = bp(1100, 293, depth_on_wall(1100, RX)), bp(1260, 230, depth_on_wall(1260, RX))
K.tube("right_wall_cable", [[(RX - 0.03, cab_b.y, cab_b.z), (RX - 0.03, cab_a.y, cab_a.z), (RX - 0.03, FACADE + 1, cab_a.z + 0.1)]],
       0.008, M["cable"], c, fillet=0)
bm_f, bm_g = bmesh.new(), bmesh.new()  # no grilles here: the photo shows plain framed windows
# photographed window boxes (x0, x1, top, bottom px) incl. their grey surrounds, back-projected onto the wall
for x0p, x1p, top_px, bot_px in ((1188, 1248, 2, 78), (1093, 1135, 68, 150), (1015, 1040, 152, 215),
                                 (963, 990, 200, 265), (930, 948, 228, 290)):
    ya, yb = depth_on_wall(x1p, RX), depth_on_wall(x0p, RX)
    ym = (ya + yb) / 2
    zt, zb = bp((x0p + x1p) / 2, top_px, ym).z, bp((x0p + x1p) / 2, bot_px, ym).z
    s = 0.09  # surround width
    box(bm_f, RX - 0.05, RX + 0.02, ya, yb, zb, zt)
    box(bm_g, RX - 0.07, RX - 0.05, ya + s, yb - s, zb + s, zt - s)
obj("right_window_frames", bm_f, [M["win_frame_grey"]], c, bevel=0.004)
obj("right_window_glass", bm_g, [M["win_glass"]], c, bevel=0)
# CCTV camera on the corner bracket, aimed at the gate
cc_y = depth_on_wall(1065, RX)
cc = bp(1065, 215, cc_y)
bm = bmesh.new()
box(bm, RX - 0.25, RX, cc_y - 0.03, cc_y + 0.03, cc.z - 0.03, cc.z + 0.03)  # arm
box(bm, RX - 0.02, RX, cc_y - 0.08, cc_y + 0.08, cc.z - 0.1, cc.z + 0.1)  # wall plate
obj("cctv_bracket", bm, [M["cctv"]], c, bevel=0.005)
bm = bmesh.new()
box(bm, -0.09, 0.09, -0.32, 0.0, -0.07, 0.07)
K.add_box(bm, -0.11, 0.11, -0.36, 0.02, 0.07, 0.09)  # sun hood
cam_body = obj("cctv_camera", bm, [M["cctv"]], c, bevel=0.01)
cam_body.location = (RX - 0.3, cc_y, cc.z - 0.05)
cam_body.rotation_euler = (math.radians(-12), 0, math.radians(-125))
bm = bmesh.new()
K.add_cylinder(bm, 0, 0, -0.005, 0.005, 0.04, segments=24)
lens = obj("cctv_lens", bm, [M["lens"]], c, bevel=0)
lens.parent = cam_body
lens.location = (0, -0.325, 0)
lens.rotation_euler = (math.radians(90), 0, 0)

# --------------------------------------------------------------------------- left building (3 storeys, cream, brown roof edge)
c = coll("ENT_left_building")
LX = -9.3  # side wall plane; eave from the photographed roof line: Z − 1.4 = 0.929·|X|
EAVE_L = CAM_H + 0.929 * abs(LX)
L_FRONT = depth_on_wall(210, LX)
bm = bmesh.new()
box(bm, LX - 14, LX, L_FRONT, 45, 0, EAVE_L)
obj("left_building", bm, [M["cream"]], c, bevel=0.01)
bm = bmesh.new()  # low-pitch brown roof rising to the left, 0.45 m overhang on the street side and front
vs = [bm.verts.new(v) for v in ((LX + 0.45, L_FRONT - 0.45, EAVE_L - 0.05), (LX + 0.45, 45, EAVE_L - 0.05),
                                (LX - 7.0, 45, EAVE_L + 1.1), (LX - 7.0, L_FRONT - 0.45, EAVE_L + 1.1))]
bm.faces.new(vs)
rf = obj("left_roof", bm, [M["roof_brown"]], c, bevel=0)
rf.modifiers.new("Thick", "SOLIDIFY").thickness = 0.1
bm = bmesh.new()  # brown fascia along the street-side eave and the front edge
box(bm, LX + 0.4, LX + 0.5, L_FRONT - 0.45, 45, EAVE_L - 0.3, EAVE_L)
box(bm, LX - 14, LX + 0.5, L_FRONT - 0.5, L_FRONT - 0.4, EAVE_L - 0.3, EAVE_L)
obj("left_roof_fascia", bm, [M["roof_brown"]], c, bevel=0.005)
bm_f, bm_g, bm_m = bmesh.new(), bmesh.new(), bmesh.new()
for f in range(3):
    z0 = 1.0 + f * 3.1
    y = L_FRONT + 1.6
    while y < 44:
        box(bm_f, LX - 0.02, LX + 0.06, y - 0.06, y + 1.26, z0 - 0.06, z0 + 1.56)
        box(bm_g, LX + 0.06, LX + 0.07, y + 0.07, y + 1.13, z0 + 0.07, z0 + 1.43)  # glass in front of the white frame
        box(bm_f, LX - 0.02, LX + 0.12, y - 0.1, y + 1.3, z0 - 0.1, z0 - 0.04)  # sill
        y += 2.6
        box(bm_m, LX + 0.07, LX + 0.085, y + 0.58, y + 0.62, z0 + 0.07, z0 + 1.43)  # mullion (multi-pane, as photo)
        box(bm_m, LX + 0.07, LX + 0.085, y + 0.07, y + 1.13, z0 + 1.0, z0 + 1.04)  # transom
        if f == 0:  # ground floor (hidden behind the boundary wall in the photo): steel security grilles
            for k in range(1, 9):
                box(bm_m, LX + 0.1, LX + 0.115, y + k * 0.133 - 0.007, y + k * 0.133 + 0.007, z0, z0 + 1.5)
obj("left_window_frames", bm_f, [M["pvc"]], c, bevel=0.004)
obj("left_window_glass", bm_g, [M["win_glass"]], c, bevel=0)
obj("left_window_muntins", bm_m, [M["pvc"]], c, bevel=0.002)
# canopy support pole on the left building side (photo: white pole at x ≈ 230 px from the front rail down)
pole_x = LX + 0.5
pole_y = depth_on_wall(229, pole_x)
K.tube("canopy_left_pole", [[(pole_x, pole_y, 0.0), (pole_x, pole_y, bp(229, 128, pole_y).z)]], 0.06, M["canopy"], c, fillet=0)
# loose service cables along the cream facade (the photo shows several thin cables there)
cab = []
for k, (za, zb) in enumerate(((7.6, 7.1), (4.6, 4.3), (6.1, 5.4))):
    ya, yb = L_FRONT + 0.4, L_FRONT + 9.0 + 3 * k
    pts = []
    for t in range(9):
        tt = t / 8
        pts.append((LX + 0.05 + 0.02 * k, ya + (yb - ya) * tt, za + (zb - za) * tt - 0.25 * math.sin(math.pi * tt)))
    cab.append(pts)
cab.append([(LX + 0.05, L_FRONT + 0.5, 7.6), (LX + 0.05, L_FRONT + 0.5, 0.4)])  # vertical drop to the ground
K.tube("left_facade_cables", cab, 0.009, M["cable"], c, fillet=0)
# AC units further along the cream facade, beyond what the photo shows (revealed only after the gate)
bm = bmesh.new()
for ay, az in ((L_FRONT + 22.0, 4.9), (L_FRONT + 25.0, 8.0)):
    box(bm, LX, LX + 0.32, ay - 0.42, ay + 0.42, az, az + 0.6)
obj("left_ac_units", bm, [M["ac"]], c, bevel=0.015)

# --------------------------------------------------------------------------- tensile canopy frame with cables
c = coll("ENT_canopy")
fr_r = bp(1025, 105, depth_on_wall(1025, RX - 0.35))
fr_l = bp(225, 130, depth_on_wall(225, LX + 0.5))
br_r = bp(915, 186, depth_on_wall(915, RX - 0.35))
BR_LX = -6.0
br_l = bp(415, 207, depth_on_wall(415, BR_LX))


def truss(name, a: Vector, b: Vector):
    """Twin-tube white rail with short clamps every 1.2 m (the photographed rails read as doubled tubes)."""
    d = (b - a)
    up = Vector((0, 0, 0.09))
    K.tube(f"{name}_tubes", [[tuple(a), tuple(b)], [tuple(a + up), tuple(b + up)]], 0.035, M["canopy"], c, fillet=0)
    bm = bmesh.new()
    n = max(2, int(d.length / 1.2))
    for k in range(n + 1):
        p = a + d * (k / n)
        box(bm, p.x - 0.03, p.x + 0.03, p.y - 0.05, p.y + 0.05, p.z - 0.05, p.z + 0.14)
    obj(f"{name}_clamps", bm, [M["canopy"]], c, bevel=0.005)


truss("canopy_front_rail", fr_l, fr_r)
truss("canopy_back_rail", br_l, br_r)
# wall brackets
K.tube("canopy_brackets", [[tuple(fr_r), (RX, fr_r.y, fr_r.z + 0.3)], [tuple(br_r), (RX, br_r.y, br_r.z + 0.3)],
                           [tuple(fr_l), (LX, fr_l.y, fr_l.z + 0.3)], [tuple(br_l), (LX, br_l.y + 0.5, br_l.z + 0.6)]],
       0.03, M["canopy"], c, fillet=0)
cables = []
n = 8
for k in range(n + 1):
    t = k / n
    a = fr_l.lerp(fr_r, t)
    b1 = br_l.lerp(br_r, min(1, t + 0.06))
    b2 = br_l.lerp(br_r, max(0, t - 0.06))
    cables += [[tuple(a), tuple(b1)], [tuple(a), tuple(b2)]]
K.tube("canopy_cables", cables, 0.006, M["cable"], c, fillet=0)

# --------------------------------------------------------------------------- behind the gate: courtyard
# What the photo shows through the gate: a light single-storey facade ~3.6 m high with a dark central doorway,
# spiky potted plants in front, the cream left building and a golden tree rising behind it, sky above.
c = coll("ENT_courtyard")
CY = 16.5
cy_top = 3.6
door_x0, door_x1 = px_x(505, CY), px_x(560, CY)
door_z1 = px_z(435, CY)
win_x = [(-9.0, -7.6), (-2.6, -1.3), (0.4, 1.7)]
ops = [(door_x0 + 12.0, door_x1 + 12.0, 0.0, door_z1)] + [(a + 12.0, b + 12.0, 0.9, 2.5) for a, b in win_x]
bm = K.wall_bm(16.0, cy_top, 0.3, ops)
bmesh.ops.translate(bm, verts=bm.verts, vec=(-12.0, CY, 0))
obj("courtyard_facade", bm, [M["courtyard_wall"]], c, bevel=0.003)
bm = bmesh.new()  # roof slab + coping, plinth band
box(bm, -12.1, 4.1, CY - 0.06, CY + 6.0, cy_top, cy_top + 0.14)
box(bm, -12.0, 4.0, CY - 0.03, CY, 0.0, 0.35)
obj("courtyard_coping_plinth", bm, [M["coping"]], c, bevel=0.004)
bm = bmesh.new()  # interior shell so the openings have depth
box(bm, -12.0, 4.0, CY + 0.3, CY + 5.0, -0.01, 0.0)
box(bm, -12.0, 4.0, CY + 5.0, CY + 5.05, 0.0, cy_top)
box(bm, -12.0, 4.0, CY + 0.3, CY + 5.0, cy_top - 0.02, cy_top)
obj("courtyard_interior", bm, [M["door_dark"]], c, bevel=0)
# carved wooden double door with a pointed-arch surround (traditional Uzbek doorway), glazed top lights
bm, bw = bmesh.new(), bmesh.new()
mid = (door_x0 + door_x1) / 2
for x0, x1 in ((door_x0 + 0.04, mid - 0.005), (mid + 0.005, door_x1 - 0.04)):
    box(bw, x0, x1, CY + 0.1, CY + 0.15, 0.0, door_z1 - 0.05)
    for zc in (0.35, 0.95, 1.55):  # raised carved panels
        box(bw, x0 + 0.07, x1 - 0.07, CY + 0.085, CY + 0.1, zc, zc + 0.45)
obj("courtyard_door_leaves", bw, [M["wood_door"]], c, bevel=0.006)
arch = []
r_a = (door_x1 - door_x0) / 2 + 0.12
for k in range(0, 13):
    a = math.radians(180 * k / 12)
    arch.append((mid - r_a * math.cos(a), CY - 0.02, door_z1 + 0.05 + 0.55 * math.sin(a) ** 1.4))
K.tube("courtyard_door_arch", [[(door_x0 - 0.12, CY - 0.02, 0.0)] + arch + [(door_x1 + 0.12, CY - 0.02, 0.0)]], 0.05,
       M["coping"], c, fillet=0.02)
bg_, bgr = bmesh.new(), bmesh.new()
for a, b in win_x:  # windows: dark glass with white frames and decorative steel grilles
    box(bg_, a, b, CY + 0.12, CY + 0.13, 0.9, 2.5)
    for k in range(1, 7):
        xx = a + k * (b - a) / 7
        box(bgr, xx - 0.01, xx + 0.01, CY - 0.04, CY - 0.02, 0.92, 2.48)
    for zz in (1.3, 1.7, 2.1):
        box(bgr, a + 0.02, b - 0.02, CY - 0.05, CY - 0.03, zz - 0.01, zz + 0.01)
obj("courtyard_window_glass", bg_, [M["win_glass"]], c, bevel=0)
obj("courtyard_window_grilles", bgr, [M["gate_frame"]], c, bevel=0.002)
# AC units only where the photo cannot see (behind the left pillar / behind the booth) — revealed on the move in
bm, bg2 = bmesh.new(), bmesh.new()
for ax, az in ((-9.9, 2.75), (2.6, 2.75)):
    box(bm, ax - 0.42, ax + 0.42, CY - 0.3, CY, az, az + 0.6)
    bg2.verts.ensure_lookup_table()
    n_before = len(bg2.verts)
    K.add_cylinder(bg2, 0, 0, 0, 0.01, 0.2, segments=24)
    bg2.verts.ensure_lookup_table()
    new_v = bg2.verts[n_before:]
    bmesh.ops.rotate(bg2, verts=new_v, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "X"))
    bmesh.ops.translate(bg2, verts=new_v, vec=(ax + 0.12, CY - 0.305, az + 0.3))
obj("courtyard_ac_units", bm, [M["ac"]], c, bevel=0.015)
obj("courtyard_ac_fans", bg2, [M["ac_grille"]], c, bevel=0)
K.tube("courtyard_ac_pipes", [[(-9.9 + 0.3, CY - 0.15, 2.75), (-9.9 + 0.3, CY - 0.05, 0.4)],
                              [(2.6 - 0.3, CY - 0.15, 2.75), (2.6 - 0.3, CY - 0.05, 0.4)]], 0.02, M["pipe"], c, fillet=0)

# potted palms (spiky, like the photographed plants): large planters, arching fronds with leaflets
rnd = random.Random(3)
bm_leaf = bmesh.new()
uvl = bm_leaf.loops.layers.uv.verify()
stems = []
for i, (x_px, yp) in enumerate(((450, 12.5), (585, 12.8), (665, 12.4), (540, 14.8))):
    p = bp(x_px, 539, yp)
    bm = bmesh.new()
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=28, radius1=0.24, radius2=0.31, depth=0.62)
    bmesh.ops.translate(bm, verts=res["verts"], vec=(p.x, yp, 0.31))
    obj(f"planter_{i}", bm, [M["pot"]], c, bevel=0, smooth=True)
    for k in range(14):
        a = rnd.uniform(0, 2 * math.pi)
        L = rnd.uniform(0.9, 1.5)
        lift = rnd.uniform(0.55, 0.95)
        base = Vector((p.x, yp, 0.6))
        d = Vector((math.cos(a), math.sin(a), 0))
        pts = [base + d * (L * t) + Vector((0, 0, L * lift * math.sin(math.pi * 0.62 * t)))for t in (0, 0.25, 0.5, 0.75, 1.0)]
        stems.append([tuple(v) for v in pts])
        for j in range(1, 18):  # leaflets along the frond, both sides, drooping
            t = j / 18
            q = base + d * (L * t) + Vector((0, 0, L * lift * math.sin(math.pi * 0.62 * t)))
            for sgn in (-1, 1):
                side = Vector((-d.y, d.x, 0)) * sgn
                ln = 0.28 * (1 - 0.6 * abs(t - 0.4))
                tip = q + side * ln + Vector((0, 0, -0.12)) + d * 0.08
                w_ = d * 0.018
                f = bm_leaf.faces.new([bm_leaf.verts.new(v) for v in (q - w_, q + w_, tip + w_ * 0.2, tip - w_ * 0.2)])
                for loop, uvc in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
                    loop[uvl].uv = uvc
K.tube("palm_stems", stems, 0.012, M["palm"], c, fillet=0.1)
me = bpy.data.meshes.new("palm_leaflets")
bm_leaf.to_mesh(me)
bm_leaf.free()
me.materials.append(M["palm"])
pl = bpy.data.objects.new("palm_leaflets", me)
c.objects.link(pl)

pole_b = bp(495, 600, 22.0)
pole_t = bp(495, 330, 22.0)
K.tube("street_light_pole", [[(pole_b.x, 22.0, 0), (pole_t.x, 22.0, pole_t.z), (pole_t.x + 0.6, 22.0, pole_t.z + 0.4),
                              (pole_t.x + 1.6, 22.0, pole_t.z + 0.3)]], 0.07, M["pipe"], c, fillet=0.5)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit_building as KB  # noqa: E402

leaf_mats = dict(Mk)
leaf_mats.update(KB.exterior_materials())
# the photographed tree: sparse, fine golden-tan autumn leaves on slender dark branches
leaf_gold = leaf_mats["leaf_card"].copy()
leaf_gold.name = "ENT_leaf_card_autumn"
rmp = next(n for n in leaf_gold.node_tree.nodes if n.type == "VALTORGB")
for el, hx in zip(rmp.color_ramp.elements, ("#8A5A22", "#C98E3A", "#E6BE6E")):
    el.color = C.hex_rgba(hx)
bark_dark = m_simple("ENT_bark_dark", "#3B2F27", rough=0.85)
tree_base = bp(640, 600, 26.0)
KB.make_branching_tree("courtyard_tree", (tree_base.x, 26.0, 0.0), c, bark_dark, leaf_gold, random.Random(11),
                       height=9.4, depth=6, leaf_size=0.15, leaves_per_twig=500, trunk_r=0.17)

# --------------------------------------------------------------------------- light: low morning sun, natural sky
lights = coll("ENT_lights")
w = K.sky_world("W_entrance_morning", seen_strength=0.16, ambient_strength=0.085)
sc.world = w
# low morning sun from behind-right of the entrance (az 75°, el 26°): long shadows of pillars, booth, gate and
# canopy fall across the paving toward the camera; the right building shades a strip along its wall
sun = K.sun("SUN_entrance_morning", lights, 26, 75, 7.0, 4700, angle_deg=0.6)
sun.data.shadow_maximum_resolution = 0.001  # thin cables and gate bars must cast crisp shadows
if hasattr(sun.data, "shadow_filter_radius"):
    sun.data.shadow_filter_radius = 0.5
C.sync_sky_to_sun(w, sun)
# neutral ambient fill: shaded walls in the photo are neutral grey, not sky-blue
for bgn in [n for n in w.node_tree.nodes if n.type == "BACKGROUND"]:
    if abs(bgn.inputs["Strength"].default_value - 0.085) < 1e-6:
        for lk in list(bgn.inputs["Color"].links):
            w.node_tree.links.remove(lk)
        bgn.inputs["Color"].default_value = C.hex_rgba("#E2E3E5")
        bgn.inputs["Strength"].default_value = 0.42
# a few soft clouds: fBm noise on the sky dome (projected on a plane), mixed over the sky colour
nt = w.node_tree
sky = next(n for n in nt.nodes if n.type == "TEX_SKY")
tc = nt.nodes.new("ShaderNodeTexCoord")
sep = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(tc.outputs["Generated"], sep.inputs[0])
div = nt.nodes.new("ShaderNodeCombineXYZ")
for i, axis in enumerate(("X", "Y")):
    dv = nt.nodes.new("ShaderNodeMath")
    dv.operation = "DIVIDE"
    nt.links.new(sep.outputs[axis], dv.inputs[0])
    mx = nt.nodes.new("ShaderNodeMath")
    mx.operation = "MAXIMUM"
    mx.inputs[1].default_value = 0.08
    nt.links.new(sep.outputs["Z"], mx.inputs[0])
    nt.links.new(mx.outputs[0], dv.inputs[1])
    nt.links.new(dv.outputs[0], div.inputs[i])
nz = nt.nodes.new("ShaderNodeTexNoise")
nz.inputs["Scale"].default_value = 1.1
nz.inputs["Detail"].default_value = 8.0
nz.inputs["Roughness"].default_value = 0.6
mp = nt.nodes.new("ShaderNodeMapping")
mp.inputs["Scale"].default_value = (1.0, 2.4, 1.0)
nt.links.new(div.outputs[0], mp.inputs["Vector"])
nt.links.new(mp.outputs[0], nz.inputs["Vector"])
cover = K.map_range(nt, nz.outputs["Fac"], -2.6, 1.0)  # sparse: a few soft clouds
cl = nt.nodes.new("ShaderNodeMath")
cl.operation = "MAXIMUM"
cl.inputs[1].default_value = 0.0
cl.use_clamp = True
nt.links.new(cover, cl.inputs[0])
hz = nt.nodes.new("ShaderNodeMath")  # fade clouds toward the horizon
hz.operation = "MULTIPLY"
hz.use_clamp = True
hz.inputs[1].default_value = 4.0
nt.links.new(sep.outputs["Z"], hz.inputs[0])
fac = nt.nodes.new("ShaderNodeMath")
fac.operation = "MULTIPLY"
fac.use_clamp = True
nt.links.new(cl.outputs[0], fac.inputs[0])
nt.links.new(hz.outputs[0], fac.inputs[1])
fac2 = nt.nodes.new("ShaderNodeMath")
fac2.operation = "MULTIPLY"
fac2.use_clamp = True
fac2.inputs[1].default_value = 0.85
nt.links.new(fac.outputs[0], fac2.inputs[0])
mixc = nt.nodes.new("ShaderNodeMix")
mixc.data_type = "RGBA"
nt.links.new(fac2.outputs[0], mixc.inputs["Factor"])
mixc.inputs[7].default_value = (2.6, 2.6, 2.7, 1.0)  # cloud radiance (sky node values are physical, ~1–3)
for link in list(nt.links):
    if link.from_node == sky:
        to = link.to_socket
        nt.links.remove(link)
        nt.links.new(mixc.outputs[2], to)
nt.links.new(sky.outputs["Color"], mixc.inputs[6])  # after re-wiring, so this link is not caught by the loop
for look in ("AgX - Medium High Contrast", "Medium High Contrast"):
    try:
        sc.view_settings.look = look
        break
    except TypeError:
        pass

# --------------------------------------------------------------------------- cameras
cams = coll("ENT_cameras")


def make_cam(name, lens, zoom=1.0):
    """Photo-match camera. zoom > 1 = the photo pushed in by that factor around the image centre (Remotion side),
    which equals lens × zoom with shifts × zoom — the in-film dissolve uses zoom = 18 / 15.33 → 18 mm (lens rule)."""
    cd = bpy.data.cameras.new(name)
    cd.sensor_fit, cd.sensor_width = "HORIZONTAL", 36.0
    cd.lens = lens * zoom
    cd.shift_x = -(PPX - IMG_W / 2) / IMG_W * zoom
    cd.shift_y = (PPY - IMG_H / 2) / IMG_W * zoom
    cd.clip_start, cd.clip_end = 0.05, 600
    cd.dof.use_dof = False
    ob = bpy.data.objects.new(name, cd)
    ob.location = (0, 0, CAM_H)
    ob.rotation_euler = (math.radians(90), 0, 0)
    cams.objects.link(ob)
    return ob


cam_match = make_cam("CAM_PHOTO_MATCH", LENS_MATCH)
cam_match["note"] = "Measurement camera = the photo's full frame (15.3 mm). Not a film shot (lens rule ≥ 18 mm)."
DISSOLVE_ZOOM = 18.0 / LENS_MATCH  # photo pushed in 1.174× → exactly the 18 mm special lens (lens rule)
cam_film = make_cam("CAM_S02_START", LENS_MATCH, zoom=DISSOLVE_ZOOM)
cam_film["note"] = "Scene 2 first frame: the photo, pushed in 1.174× (around the image centre) in Remotion, dissolves into this 18 mm view."
sc["photo_solve"] = dict(f_px=F_PX, ppx=PPX, ppy=PPY, cam_h=CAM_H, facade=FACADE, lens_match=LENS_MATCH,
                         dissolve_zoom=DISSOLVE_ZOOM)
sc.camera = cam_match

# --------------------------------------------------------------------------- sign glow: compositor glare (beauty only)
ng = bpy.data.node_groups.new("ENT_COMPOSITE", "CompositorNodeTree")
ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
rl = ng.nodes.new("CompositorNodeRLayers")
gl = ng.nodes.new("CompositorNodeGlare")
for t in ("Bloom", "Fog Glow"):
    try:
        gl.inputs["Type"].default_value = t
        break
    except TypeError:
        pass
for k, v in (("Threshold", 1.6), ("Strength", 0.55), ("Size", 0.55), ("Saturation", 1.0)):
    if k in gl.inputs:
        gl.inputs[k].default_value = v
go = ng.nodes.new("NodeGroupOutput")
ng.links.new(rl.outputs["Image"], gl.inputs["Image"])
ng.links.new(gl.outputs[0], go.inputs[0])
sc.compositing_node_group = ng
sc.render.use_compositing = True

# --------------------------------------------------------------------------- scene-2 opening move (hand-off window)
S2 = C.get_scene_def("s02_turnstile")
F0 = S2["from"]  # 270
BLEND_FRAMES = 30  # ~1 s: projected photo -> real 3D materials
V0, V1 = 0.03, 0.07  # m/frame: matches the photo push-in at the cut, then gathers pace toward the gate


def cam_path(f):
    t = f - F0
    acc = (V1 - V0) / BLEND_FRAMES
    if t <= BLEND_FRAMES:
        y = V0 * t + 0.5 * acc * t * t
    else:
        y = V0 * BLEND_FRAMES + 0.5 * acc * BLEND_FRAMES ** 2 + V1 * (t - BLEND_FRAMES)
    return dict(location=(0.0, y, CAM_H), rotation=(math.radians(90), 0.0, 0.0))


C.bake_path(cam_film, range(F0, F0 + BLEND_FRAMES + 16), cam_path)
sc.frame_start, sc.frame_end = F0, F0 + BLEND_FRAMES + 15
sc.render.fps = 30

# --------------------------------------------------------------------------- photo projection (hand-off layer)
# The sky-corrected hero photo is projected from the matched camera onto the replica. It is rendered as its own
# RGBA layer (scene ENTRANCE_PROJ, Standard view transform -> the photo's exact pixels) and laid over the 3D beauty
# render: final = beauty * (1 - a) + photo * a   (tools/composite_handoff.py now, Remotion in the assembly).
#   a    = in-frame * visible-from-projector (depth test) * fade(t, stretch)
#   fade = clamp(1 - t * (1 + 2 * (1 - stretch)))  -- grazing / stretched surfaces hand over to 3D first
HERO = C.ASSETS_DIR / "hero" / "entrance_hero_1920.png"
DEPTH_EXR = C.RENDERS_DIR / "_entrance" / "proj_depth.exr"
proj_only = bpy.data.collections.new("PROJ_ONLY")
SKY_Y = 380.0
bm = bmesh.new()  # sky card filling the photo frame far away (receives the photo's sky)
c0, c1 = bp(-40, IMG_H + 40, SKY_Y), bp(IMG_W + 40, -40, SKY_Y)
box(bm, c0.x, c1.x, SKY_Y, SKY_Y + 0.1, c0.z, c1.z)
me = bpy.data.meshes.new("proj_sky_card")
bm.to_mesh(me)
bm.free()
proj_only.objects.link(bpy.data.objects.new("proj_sky_card", me))


def math_n(nt, op, a, b=None, clamp=False):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    n.use_clamp = clamp
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            nt.links.new(v, n.inputs[i])
    return n.outputs[0]


def projection_uv(nt):
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sep.inputs[0])
    X, Y, Z = sep.outputs["X"], sep.outputs["Y"], sep.outputs["Z"]
    ys = math_n(nt, "MAXIMUM", Y, 0.05)
    u = math_n(nt, "DIVIDE", math_n(nt, "ADD", math_n(nt, "DIVIDE", math_n(nt, "MULTIPLY", X, F_PX), ys), PPX), IMG_W)
    vimg = math_n(nt, "SUBTRACT", PPY, math_n(nt, "DIVIDE", math_n(nt, "MULTIPLY", math_n(nt, "SUBTRACT", Z, CAM_H), F_PX), ys))
    v = math_n(nt, "SUBTRACT", 1.0, math_n(nt, "DIVIDE", vimg, IMG_H))
    cv = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(u, cv.inputs[0])
    nt.links.new(v, cv.inputs[1])
    return geo, sep, u, v, cv.outputs[0]


def emission_out(nt, color, strength=1.0):
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = strength
    if isinstance(color, tuple):
        em.inputs["Color"].default_value = color
    else:
        nt.links.new(color, em.inputs["Color"])
    return out, em


# depth material: emission = forward distance from the projector (= world Y for this level, +Y-facing camera)
m_depth = bpy.data.materials.new("PROJ_depth")
m_depth.use_nodes = True
nt = m_depth.node_tree
nt.nodes.clear()
geo, sep, *_ = projection_uv(nt)
cy_ = nt.nodes.new("ShaderNodeCombineXYZ")
for i in range(3):
    nt.links.new(sep.outputs["Y"], cy_.inputs[i])
out, em = emission_out(nt, cy_.outputs[0])
nt.links.new(em.outputs[0], out.inputs["Surface"])

# projection material
m_proj = bpy.data.materials.new("PROJ_photo")
m_proj.use_nodes = True
nt = m_proj.node_tree
nt.nodes.clear()
geo, sep, u, v, uv = projection_uv(nt)
hero_img = bpy.data.images.load(str(HERO), check_existing=True)
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image, tex.extension, tex.interpolation = hero_img, "CLIP", "Cubic"
nt.links.new(uv, tex.inputs["Vector"])
dtex = nt.nodes.new("ShaderNodeTexImage")
dtex.extension, dtex.interpolation = "EXTEND", "Closest"
nt.links.new(uv, dtex.inputs["Vector"])
Y = sep.outputs["Y"]
dsep = nt.nodes.new("ShaderNodeSeparateColor")
nt.links.new(dtex.outputs["Color"], dsep.inputs[0])
vis = math_n(nt, "LESS_THAN", Y, math_n(nt, "ADD", math_n(nt, "MULTIPLY", dsep.outputs[0], 1.015), 0.05))
inf = math_n(nt, "MULTIPLY", math_n(nt, "MULTIPLY", math_n(nt, "GREATER_THAN", u, 0.0), math_n(nt, "LESS_THAN", u, 1.0)),
             math_n(nt, "MULTIPLY", math_n(nt, "GREATER_THAN", v, 0.0), math_n(nt, "LESS_THAN", v, 1.0)))
inf = math_n(nt, "MULTIPLY", inf, math_n(nt, "GREATER_THAN", Y, 0.1))
toP = nt.nodes.new("ShaderNodeVectorMath")
toP.operation = "SUBTRACT"
toP.inputs[0].default_value = (0.0, 0.0, CAM_H)
nt.links.new(geo.outputs["Position"], toP.inputs[1])
nrm = nt.nodes.new("ShaderNodeVectorMath")
nrm.operation = "NORMALIZE"
nt.links.new(toP.outputs[0], nrm.inputs[0])
dot = nt.nodes.new("ShaderNodeVectorMath")
dot.operation = "DOT_PRODUCT"
nt.links.new(nrm.outputs[0], dot.inputs[0])
nt.links.new(geo.outputs["Normal"], dot.inputs[1])
st = nt.nodes.new("ShaderNodeMapRange")
st.interpolation_type = "SMOOTHSTEP"
st.inputs["From Min"].default_value, st.inputs["From Max"].default_value = 0.06, 0.3
nt.links.new(math_n(nt, "ABSOLUTE", dot.outputs["Value"]), st.inputs["Value"])
tval = nt.nodes.new("ShaderNodeValue")
tval.name = tval.label = "handoff_t"
for fr, val in ((F0, 0.0), (F0 + BLEND_FRAMES, 1.0)):
    tval.outputs[0].default_value = val
    tval.outputs[0].keyframe_insert("default_value", frame=fr)
for fc in C.fcurves_of(nt):
    for kp in fc.keyframe_points:
        kp.interpolation, kp.easing = "BEZIER", "EASE_IN_OUT"
        kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"
grow = math_n(nt, "ADD", 1.0, math_n(nt, "MULTIPLY", math_n(nt, "SUBTRACT", 1.0, st.outputs["Result"]), 2.0))
fade = math_n(nt, "SUBTRACT", 1.0, math_n(nt, "MULTIPLY", tval.outputs[0], grow), clamp=True)
alpha = math_n(nt, "MULTIPLY", math_n(nt, "MULTIPLY", inf, vis), fade)
out, em = emission_out(nt, tex.outputs["Color"])
tr = nt.nodes.new("ShaderNodeBsdfTransparent")
mx = nt.nodes.new("ShaderNodeMixShader")
nt.links.new(alpha, mx.inputs["Fac"])
nt.links.new(tr.outputs[0], mx.inputs[1])
nt.links.new(em.outputs[0], mx.inputs[2])
nt.links.new(mx.outputs[0], out.inputs["Surface"])
try:
    m_proj.surface_render_method = "BLENDED"
except (AttributeError, TypeError):
    pass


def aux_scene(name, material, transparent):
    s = bpy.data.scenes.new(name)
    s.collection.children.link(root)
    s.collection.children.link(proj_only)
    C.apply_render_settings(s, transparent=transparent)
    s.view_settings.view_transform = "Standard"
    s.view_settings.look = "None"
    s.view_settings.exposure = 0.0
    w0 = bpy.data.worlds.new(f"{name}_black")
    w0.use_nodes = True
    w0.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.0
    s.world = w0
    s.view_layers[0].material_override = material
    s.frame_start, s.frame_end = sc.frame_start, sc.frame_end
    s.render.fps = 30
    s.render.use_compositing = False
    try:
        s.eevee.use_raytracing = False
    except AttributeError:
        pass
    return s


sc_depth = aux_scene("ENTRANCE_DEPTH", m_depth, False)
sc_depth.camera = cam_match
sc_depth.render.resolution_percentage = 100
sc_depth.eevee.taa_render_samples = 1
sc_depth.render.filter_size = 0.0
sc_depth.render.image_settings.file_format = "OPEN_EXR"
sc_depth.render.image_settings.color_depth = "32"
sc_depth.render.image_settings.color_mode = "RGB"
sc_proj = aux_scene("ENTRANCE_PROJ", m_proj, True)
sc_proj.camera = cam_film
sc_proj.eevee.taa_render_samples = 16
sc_proj.render.image_settings.color_depth = "16"
sc_proj["note"] = "Photo-projection layer for the 1->2 hand-off. Composite over the beauty pass with its alpha."

out_blend = C.KIT_DIR / "entrance.blend"
bpy.context.window.scene = sc
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(out_blend), check_existing=False, relative_remap=True)
print(f"ENTRANCE_SAVED {out_blend}  facade={FACADE:.2f} m lens_match={LENS_MATCH:.2f} mm")

if "--no-render" not in argv:
    out_dir = C.RENDERS_DIR / "_entrance"
    out_dir.mkdir(parents=True, exist_ok=True)

    def render(scene, cam, frame, path):
        scene.camera = cam
        scene.frame_set(frame)
        scene.render.filepath = str(path)
        t0 = time.perf_counter()
        bpy.ops.render.render(write_still=True, scene=scene.name)
        print(f"ENTRANCE_RENDERED {Path(path).name} {time.perf_counter() - t0:.1f} s")

    render(sc_depth, cam_match, F0, DEPTH_EXR)
    depth_img = bpy.data.images.load(str(DEPTH_EXR), check_existing=False)
    depth_img.colorspace_settings.name = "Non-Color"
    dtex.image = depth_img
    render(sc, cam_match, F0, out_dir / "entrance_match_960_v2.png")
    for f in (F0, F0 + BLEND_FRAMES // 2, F0 + BLEND_FRAMES):
        render(sc, cam_film, f, out_dir / f"handoff_beauty_{f:04d}.png")
        render(sc_proj, cam_film, f, out_dir / f"handoff_proj_{f:04d}.png")
    bpy.ops.wm.save_as_mainfile(filepath=str(out_blend), check_existing=False, relative_remap=True)
