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
from mathutils import Vector

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


def m_emit_letters():
    m = bpy.data.materials.new("ENT_sign_letters")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = C.hex_rgba("#FFC93C")  # warm yellow; moderate strength so AgX keeps the hue
    em.inputs["Strength"].default_value = 3.0
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
    booth_glass=m_masked("ENT_booth_glass_etched", "#DDE3E6", TEX_DIR / "booth_glass_pattern.png", 0.30, glass=True),
    wall_light=m_simple("ENT_wall_light_grey", "#D3D5D7", rough=0.85, vary=0.03),
    wall_left=m_simple("ENT_boundary_wall", "#C4C6C8", rough=0.85, vary=0.03),
    coping=m_simple("ENT_coping", "#9DA0A4", rough=0.6),
    plinth=m_simple("ENT_plinth_grey", "#80848A", rough=0.7),
    cream=m_simple("ENT_cream_render", "#E0D3B6", rough=0.85, vary=0.02),
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
    shutter=m_simple("ENT_roller_shutter", "#9EA2A6", rough=0.5, metal=0.5),
    box_grey=m_simple("ENT_electric_box", "#D9DADB", rough=0.5),
    courtyard_wall=m_simple("ENT_courtyard_wall", "#9EA1A4", rough=0.8),
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
    box(bgl, x0 + 0.05, x1 - 0.05, FACADE - 0.012, FACADE - 0.006, 0.12, dz1 - 0.05)
obj("booth_door_frames", bm, [M["gate_frame"]], c, bevel=0.002)
g = obj("booth_door_glass_patterned", bgl, [M["booth_glass"]], c, bevel=0)
g.visible_shadow = False
bm = bmesh.new()  # dark interior behind the glass
box(bm, b_x0 + 0.05, b_x1 - 0.05, FACADE + 0.15, FACADE + 0.2, 0.0, dz1)
obj("booth_interior", bm, [M["door_dark"]], c, bevel=0)

# --------------------------------------------------------------------------- boundary walls on the facade line
c = coll("ENT_walls")
lw_top = bp(0, 385, FACADE).z
bm = bmesh.new()
lw_x0 = bp(0, 568, FACADE).x - 4.0
box(bm, lw_x0, LP_X0, FACADE, FACADE + 0.3, 0, lw_top)
obj("left_boundary_wall", bm, [M["wall_left"]], c, bevel=0.004)
bm = bmesh.new()
box(bm, lw_x0, LP_X0, FACADE - 0.05, FACADE + 0.35, lw_top, lw_top + 0.1)
obj("left_wall_coping", bm, [M["coping"]], c, bevel=0.004)


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
niche("left_shutter_arch", 230, 305, 428, 562, depth=0.1, mat_in=M["shutter"])
niche("left_small_arch", 35, 100, 428, 470, depth=0.15, mat_in=M["fascia_light"])
bm = bmesh.new()
eb0, eb1 = bp(100, 540, FACADE), bp(150, 490, FACADE)
box(bm, eb0.x, eb1.x, FACADE - 0.18, FACADE, eb0.z, eb1.z)
obj("electrical_box", bm, [M["box_grey"]], c, bevel=0.01)
p0, p1 = bp(176, 560, FACADE - 0.06), bp(176, 400, FACADE - 0.06)
K.tube("left_wall_pipe", [[tuple(p0), tuple(p1), tuple(p1 + Vector((0, 0.06, 0.1)))]], 0.035, M["pipe"], c, fillet=0.05)

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
bm_f, bm_g = bmesh.new(), bmesh.new()
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
bm_f, bm_g = bmesh.new(), bmesh.new()
for f in range(3):
    z0 = 1.0 + f * 3.1
    y = L_FRONT + 1.6
    while y < 44:
        box(bm_f, LX - 0.02, LX + 0.06, y - 0.06, y + 1.26, z0 - 0.06, z0 + 1.56)
        box(bm_g, LX + 0.06, LX + 0.07, y + 0.07, y + 1.13, z0 + 0.07, z0 + 1.43)  # glass in front of the white frame
        box(bm_f, LX - 0.02, LX + 0.12, y - 0.1, y + 1.3, z0 - 0.1, z0 - 0.04)  # sill
        y += 2.6
obj("left_window_frames", bm_f, [M["pvc"]], c, bevel=0.004)
obj("left_window_glass", bm_g, [M["win_glass"]], c, bevel=0)

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
c = coll("ENT_courtyard")
CY_BACK = 16.0
bm = bmesh.new()
box(bm, -9.0, 1.5, CY_BACK, CY_BACK + 0.3, 0, 3.3)
obj("courtyard_back_wall", bm, [M["courtyard_wall"]], c, bevel=0.004)
d0, d1 = bp(505, 520, CY_BACK - 0.01), bp(560, 435, CY_BACK - 0.01)
bm = bmesh.new()
box(bm, d0.x, d1.x, CY_BACK - 0.05, CY_BACK, 0, d1.z)
obj("courtyard_door", bm, [M["door_dark"]], c, bevel=0.004)
bm = bmesh.new()
w0, w1 = bp(420, 395, 20.0), bp(520, 360, 20.0)
box(bm, w0.x - 2.0, w1.x, 20.0, 26.0, 0, w1.z)
obj("courtyard_white_block", bm, [M["fascia_light"]], c, bevel=0.01)
bm = bmesh.new()
box(bm, -1.5, 6.0, 19.0, 30.0, 0, 4.2)
obj("courtyard_building_right", bm, [M["wall_light"]], c, bevel=0.01)
rnd = random.Random(3)
for i, x_px in enumerate((450, 585, 665)):
    yp = 12.5
    p = bp(x_px, 539, yp)
    bm = bmesh.new()
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=0.2, radius2=0.26, depth=0.5)
    bmesh.ops.translate(bm, verts=res["verts"], vec=(p.x, yp, 0.25))
    obj(f"planter_{i}", bm, [M["pot"]], c, bevel=0, smooth=True)
    blades = []
    for k in range(26):  # spiky dracaena-like leaves
        a = rnd.uniform(0, 2 * math.pi)
        lean = rnd.uniform(0.25, 0.75)
        L = rnd.uniform(0.7, 1.3)
        base = Vector((p.x, yp, 0.48))
        tip = base + Vector((math.cos(a) * lean * L, math.sin(a) * lean * L, L * math.sqrt(1 - lean * lean * 0.6)))
        mid = base.lerp(tip, 0.5) + Vector((0, 0, 0.1))
        blades.append([tuple(base), tuple(mid), tuple(tip)])
    K.tube(f"planter_{i}_leaves", blades, 0.018, M["leaves"], c, fillet=0.2)
pole_b = bp(495, 600, 22.0)
pole_t = bp(495, 330, 22.0)
K.tube("street_light_pole", [[(pole_b.x, 22.0, 0), (pole_t.x, 22.0, pole_t.z), (pole_t.x + 0.6, 22.0, pole_t.z + 0.4),
                              (pole_t.x + 1.6, 22.0, pole_t.z + 0.3)]], 0.07, M["pipe"], c, fillet=0.5)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit_building as KB  # noqa: E402

leaf_mats = dict(Mk)
leaf_mats.update(KB.exterior_materials())
# the courtyard tree in the photo is in pale autumn foliage: tan / ochre leaves
for key in ("leaves", "leaf_card"):
    mat = leaf_mats[key].copy()
    mat.name = f"ENT_{key}_autumn"
    rmp = next(n for n in mat.node_tree.nodes if n.type == "VALTORGB")
    for el, hx in zip(rmp.color_ramp.elements, ("#7A5A2E", "#B08850", "#D6B27A")):
        el.color = C.hex_rgba(hx)
    leaf_mats[key] = mat
tree_base = bp(640, 600, 26.0)
KB.make_tree("courtyard_tree", (tree_base.x, 26.0, 0.0), c, leaf_mats, random.Random(9), height=9.0, crown_r=3.0,
             clusters=40, cards_per_vert=0.45, leaf_size=0.3)

# --------------------------------------------------------------------------- light: morning sun from the right, natural sky
lights = coll("ENT_lights")
w = K.sky_world("W_entrance_morning", seen_strength=0.16, ambient_strength=0.085)
sc.world = w
sun = K.sun("SUN_entrance_morning", lights, 34, 22, 6.5, 5400, angle_deg=1.2)
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

out_blend = C.KIT_DIR / "entrance.blend"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(out_blend), check_existing=False, relative_remap=True)
print(f"ENTRANCE_SAVED {out_blend}  facade={FACADE:.2f} m lens_match={LENS_MATCH:.2f} mm")

if "--no-render" not in argv:
    out = C.RENDERS_DIR / "_entrance"
    out.mkdir(parents=True, exist_ok=True)
    for cam, fname in ((cam_match, "entrance_match_960.png"), (cam_film, "entrance_s02_start_960.png")):
        sc.camera = cam
        sc.render.filepath = str(out / fname)
        t0 = time.perf_counter()
        bpy.ops.render.render(write_still=True)
        print(f"ENTRANCE_RENDERED {fname} {time.perf_counter() - t0:.1f} s")
