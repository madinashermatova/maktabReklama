"""Builds the shared 3D kit: blender/kit/school_kit.blend   (design language A — fixed, docs/design-language.md)

    blender -b --factory-startup --python blender/scripts/build_kit.py -- [--out path.blend]

Contents (all real-world scale, metres, 1 UV unit = 1 m). Use pieces as collection instances.
  KIT_pieces (excluded from the view layer)
    PIECE_wall_segment     3.0 m wall, 0.20 m thick, 3.5 m tall (3.2 m room + 0.3 m above the ceiling to the slab)
    PIECE_wall_window      3.0 m wall, 2.4 × 2.0 m window (sill 0.90 m), graphite frame, mullion, glass, oak sill
    PIECE_door_frame       3.0 m wall, 1.0 × 2.2 m oak door: lining, architraves, leaf, lever handles, skirting
    PIECE_floor_area       3.0 × 3.0 m oak plank floor (top at z = 0)
    PIECE_ceiling_panel    3.0 × 3.0 m tile ceiling (underside at z = 0 → place at room height); 4 downlights
                           (spot, shared light data KIT_downlight) + linear LED slot (area, KIT_ledstrip)
    PIECE_skirting         3.0 m oak skirting, 80 mm
    PIECE_corner_post      0.2 × 0.2 m post closing the outside corner where two walls meet
    PIECE_desk_double      1.30 × 0.55 m student desk, 0.76 m high: oak top, graphite tube frame, shelf, rubber glides
    PIECE_chair            school chair, seat 0.43 m: bent graphite tube frame, oak plywood seat + curved back, glides
    PIECE_monitor          unbranded 24" monitor; emissive screen + area light (KIT_screen)
    PIECE_led_accent       3.0 m LED accent channel, light facing −Z (KIT_accent)
    PIECE_exterior_backdrop  schoolyard, lawn, trees, neighbouring low buildings — exterior side = local +Y
  Wall convention: wall runs along +X from x = 0; INTERIOR face is the y = 0 plane; body extends to +Y.
  KIT_* materials (procedural PBR), LIGHTS/LIGHT_<preset> + worlds W_<preset>, CAM_RIG.
"""

from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as C  # noqa: E402

# --------------------------------------------------------------------------- design language A (fixed)

P = dict(
    label="A — Warm modern",
    wall="#ECE6DC", accent="#2F6E73", accent2="#E3A33B",
    wood_light="#CDAE88", wood_dark="#5B3F2C",
    frame="#2E3135", ceiling="#F3F1EC", fabric="#2F6E73", concrete="#9A9893",
)

ROOM_HEIGHT = 3.2
MODULE = 3.0
WALL_T = 0.20
WALL_ABOVE_CEILING = 0.30
HDRI_DIR = C.ASSETS_DIR / "hdri"

# --------------------------------------------------------------------------- node helpers


def _sock(node, name, value):
    if name in node.inputs:
        node.inputs[name].default_value = value
    else:
        setattr(node, name.lower().replace(" ", "_"), value)


def _ensure_nodes(idb):
    if idb.node_tree is None:
        idb.use_nodes = True


def new_material(name: str):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    _ensure_nodes(m)
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    m.use_fake_user = True
    return m, nt, bsdf


def bsdf_set(bsdf, **kw):
    names = {
        "color": "Base Color", "rough": "Roughness", "metal": "Metallic", "ior": "IOR",
        "transmission": "Transmission Weight", "coat": "Coat Weight", "coat_rough": "Coat Roughness",
        "sheen": "Sheen Weight", "sheen_rough": "Sheen Roughness", "sss": "Subsurface Weight",
    }
    for k, v in kw.items():
        bsdf.inputs[names[k]].default_value = v


def uv_vec(nt, scale=(1.0, 1.0, 1.0)):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = scale
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
    return mp.outputs["Vector"]


def noise(nt, vec, scale, detail=4.0, rough=0.5):
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    n.inputs["Roughness"].default_value = rough
    nt.links.new(vec, n.inputs["Vector"])
    return n


def ramp(nt, fac, stops):
    r = nt.nodes.new("ShaderNodeValToRGB")
    els = r.color_ramp.elements
    els[0].position, els[0].color = stops[0]
    els[1].position, els[1].color = stops[-1]
    for pos, col in stops[1:-1]:
        els.new(pos).color = col
    nt.links.new(fac, r.inputs["Fac"])
    return r.outputs["Color"]


def map_range(nt, value, a, b):
    m = nt.nodes.new("ShaderNodeMapRange")
    m.inputs["To Min"].default_value = a
    m.inputs["To Max"].default_value = b
    nt.links.new(value, m.inputs["Value"])
    return m.outputs["Result"]


def bump(nt, bsdf, height, strength, distance=0.01):
    b = nt.nodes.new("ShaderNodeBump")
    b.inputs["Strength"].default_value = strength
    b.inputs["Distance"].default_value = distance
    nt.links.new(height, b.inputs["Height"])
    nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])


def mix_color(nt, a, b, fac, blend="MIX"):
    m = nt.nodes.new("ShaderNodeMix")
    m.data_type = "RGBA"
    m.blend_type = blend
    if isinstance(fac, float):
        m.inputs["Factor"].default_value = fac
    else:
        nt.links.new(fac, m.inputs["Factor"])
    for sock, v in ((m.inputs[6], a), (m.inputs[7], b)):
        if isinstance(v, tuple):
            sock.default_value = v
        else:
            nt.links.new(v, sock)
    return m.outputs[2]


def per_object_variation(nt, color, amount=0.08):
    """Slight per-object brightness variation (furniture, buildings) so copies are not identical."""
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    f = map_range(nt, oi.outputs["Random"], 1.0 - amount, 1.0 + amount * 0.6)
    mul = nt.nodes.new("ShaderNodeVectorMath")
    mul.operation = "SCALE"
    nt.links.new(color, mul.inputs[0])
    nt.links.new(f, mul.inputs["Scale"])
    return mul.outputs[0]


def shade(rgba, f):
    return tuple(c * f for c in rgba[:3]) + (1.0,)


# --------------------------------------------------------------------------- materials


def mat_paint(name, hex_color, rough=0.85, vary=False):
    m, nt, b = new_material(name)
    col = C.hex_rgba(hex_color)
    if vary:
        rgb = nt.nodes.new("ShaderNodeRGB")
        rgb.outputs[0].default_value = col
        nt.links.new(per_object_variation(nt, rgb.outputs[0], 0.06), b.inputs["Base Color"])
    else:
        bsdf_set(b, color=col)
    bsdf_set(b, rough=rough)
    bump(nt, b, noise(nt, uv_vec(nt), 320.0, 6.0, 0.6).outputs["Fac"], 0.04)
    return m


def mat_wood(name, hex_color, planks=False, rough=0.42, coat=0.0, vary=False):
    m, nt, b = new_material(name)
    base = C.hex_rgba(hex_color)
    vec = uv_vec(nt)
    g = noise(nt, uv_vec(nt, scale=(0.8, 22.0, 1.0)), 5.0, 8.0, 0.62)
    col = ramp(nt, g.outputs["Fac"], [(0.30, shade(base, 0.74)), (0.55, base), (0.75, shade(base, 1.1))])
    height = g.outputs["Fac"]
    if planks:
        br = nt.nodes.new("ShaderNodeTexBrick")
        br.offset, br.offset_frequency = 0.5, 1
        for k, v in (("Scale", 1.0), ("Brick Width", 1.2), ("Row Height", 0.15), ("Mortar Size", 0.0015),
                     ("Mortar Smooth", 0.2), ("Color1", (1, 1, 1, 1)), ("Color2", (0.84, 0.84, 0.84, 1)),
                     ("Mortar", (0.3, 0.3, 0.3, 1))):
            _sock(br, k, v)
        nt.links.new(vec, br.inputs["Vector"])
        col = mix_color(nt, col, br.outputs["Color"], 1.0, "MULTIPLY")
        inv = nt.nodes.new("ShaderNodeMath")
        inv.operation = "SUBTRACT"
        inv.inputs[0].default_value = 1.0
        nt.links.new(br.outputs["Fac"], inv.inputs[1])
        height = inv.outputs[0]
    if vary:
        col = per_object_variation(nt, col, 0.08)
    nt.links.new(col, b.inputs["Base Color"])
    nt.links.new(map_range(nt, g.outputs["Fac"], rough - 0.08, rough + 0.08), b.inputs["Roughness"])
    bump(nt, b, height, 0.25 if planks else 0.08, 0.002)
    if coat:
        bsdf_set(b, coat=coat, coat_rough=0.18)
    return m


def mat_concrete(name, hex_color, rough=0.8):
    m, nt, b = new_material(name)
    base = C.hex_rgba(hex_color)
    vec = uv_vec(nt)
    n1 = noise(nt, vec, 2.5, 10.0, 0.6)
    nt.links.new(ramp(nt, n1.outputs["Fac"], [(0.35, shade(base, 0.86)), (0.5, base), (0.68, shade(base, 1.08))]),
                 b.inputs["Base Color"])
    n2 = noise(nt, vec, 60.0, 4.0, 0.6)
    nt.links.new(map_range(nt, n2.outputs["Fac"], rough - 0.1, rough + 0.1), b.inputs["Roughness"])
    bump(nt, b, n2.outputs["Fac"], 0.06)
    return m


def mat_simple(name, hex_color, rough=0.5, metal=0.0, coat=0.0, vary=0.0):
    m, nt, b = new_material(name)
    col = C.hex_rgba(hex_color)
    if vary:
        rgb = nt.nodes.new("ShaderNodeRGB")
        rgb.outputs[0].default_value = col
        nt.links.new(per_object_variation(nt, rgb.outputs[0], vary), b.inputs["Base Color"])
    else:
        bsdf_set(b, color=col)
    bsdf_set(b, rough=rough, metal=metal)
    if coat:
        bsdf_set(b, coat=coat, coat_rough=0.2)
    return m


def mat_metal(name, hex_color, rough, brushed=False):
    m, nt, b = new_material(name)
    bsdf_set(b, color=C.hex_rgba(hex_color), metal=1.0, rough=rough)
    if brushed:
        n = noise(nt, uv_vec(nt, scale=(1.0, 260.0, 1.0)), 4.0, 6.0, 0.6)
        nt.links.new(map_range(nt, n.outputs["Fac"], rough - 0.07, rough + 0.07), b.inputs["Roughness"])
    return m


def mat_glass(name):
    m, nt, b = new_material(name)
    bsdf_set(b, color=C.hex_rgba("#F1F6F4"), rough=0.0, ior=1.5, transmission=1.0)
    if "Thin Wall" in b.inputs:
        b.inputs["Thin Wall"].default_value = True
    for prop, val in (("use_raytrace_refraction", True), ("surface_render_method", "DITHERED")):
        try:
            setattr(m, prop, val)
        except (AttributeError, TypeError):
            pass
    return m


def mat_grass(name):
    m, nt, b = new_material(name)
    vec = uv_vec(nt)
    n = noise(nt, vec, 1.2, 6.0, 0.6)
    nt.links.new(ramp(nt, n.outputs["Fac"], [(0.3, C.hex_rgba("#3C6E26")), (0.7, C.hex_rgba("#6A9A3A"))]),
                 b.inputs["Base Color"])
    bsdf_set(b, rough=0.75, sheen=0.3, sheen_rough=0.4)
    bump(nt, b, noise(nt, vec, 420.0, 2.0, 0.5).outputs["Fac"], 0.5, 0.01)
    return m


def mat_leaves(name):
    m, nt, b = new_material(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n = noise(nt, tc.outputs["Object"], 3.0, 8.0, 0.65)
    col = ramp(nt, n.outputs["Fac"], [(0.35, C.hex_rgba("#2C5520")), (0.55, C.hex_rgba("#4C7B2C")), (0.75, C.hex_rgba("#7FA348"))])
    nt.links.new(per_object_variation(nt, col, 0.15), b.inputs["Base Color"])
    bsdf_set(b, rough=0.7, sss=0.15)
    bump(nt, b, noise(nt, tc.outputs["Object"], 40.0, 2.0, 0.5).outputs["Fac"], 0.6, 0.05)
    return m


def mat_screen(name):
    """Generic unbranded UI glow: dark navy with soft panels (real UI comes from Remotion later)."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    _ensure_nodes(m)
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    br = nt.nodes.new("ShaderNodeTexBrick")
    for k, v in (("Scale", 1.0), ("Brick Width", 0.16), ("Row Height", 0.05), ("Mortar Size", 0.012),
                 ("Color1", C.hex_rgba("#3A6EA8")), ("Color2", C.hex_rgba("#20406A")), ("Mortar", C.hex_rgba("#0E1A2C"))):
        _sock(br, k, v)
    br.offset = 0.0
    nt.links.new(tc.outputs["UV"], br.inputs["Vector"])
    nt.links.new(br.outputs["Color"], em.inputs["Color"])
    em.inputs["Strength"].default_value = 2.0
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    m.use_fake_user = True
    return m


def mat_emit(name, kelvin=4000, strength=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    _ensure_nodes(m)
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = C.kelvin_rgba(kelvin)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    m.use_fake_user = True
    return m


def mat_ceiling(name, hex_color):
    m, nt, b = new_material(name)
    vec = uv_vec(nt)
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.offset = 0.0
    base = C.hex_rgba(hex_color)
    for k, v in (("Scale", 1.0), ("Brick Width", 0.6), ("Row Height", 0.6), ("Mortar Size", 0.004),
                 ("Color1", base), ("Color2", shade(base, 0.985)), ("Mortar", shade(base, 0.72))):
        _sock(br, k, v)
    nt.links.new(vec, br.inputs["Vector"])
    nt.links.new(br.outputs["Color"], b.inputs["Base Color"])
    bsdf_set(b, rough=0.92)
    sub = nt.nodes.new("ShaderNodeMath")
    sub.operation = "SUBTRACT"
    nt.links.new(noise(nt, vec, 250.0, 3.0, 0.5).outputs["Fac"], sub.inputs[0])
    nt.links.new(br.outputs["Fac"], sub.inputs[1])
    bump(nt, b, sub.outputs[0], 0.15, 0.003)
    return m


def build_materials() -> dict:
    M = {
        "wall_paint": mat_paint("KIT_wall_paint", P["wall"]),
        "wall_accent": mat_paint("KIT_wall_accent", P["accent"], rough=0.75),
        "accent2": mat_paint("KIT_accent2", P["accent2"], rough=0.6),
        "wood_light": mat_wood("KIT_wood_light", P["wood_light"], vary=True),
        "wood_dark": mat_wood("KIT_wood_dark", P["wood_dark"], rough=0.38, vary=True),
        "floor": mat_wood("KIT_floor", P["wood_light"], planks=True, rough=0.42, coat=0.2),
        "steel_brushed": mat_metal("KIT_steel_brushed", "#B9BDC1", 0.28, brushed=True),
        "chrome": mat_metal("KIT_chrome", "#EDEDEF", 0.04),
        "glass": mat_glass("KIT_glass"),
        "grass_artificial": mat_grass("KIT_grass_artificial"),
        "fabric": mat_simple("KIT_fabric", P["fabric"], rough=0.9),
        "board": mat_simple("KIT_board", "#F4F5F3", rough=0.12, coat=0.5),
        "concrete": mat_concrete("KIT_concrete", P["concrete"]),
        "ceiling": mat_ceiling("KIT_ceiling", P["ceiling"]),
        "frame": mat_simple("KIT_frame_metal", P["frame"], rough=0.38, coat=0.15, vary=0.04),
        "trim": mat_simple("KIT_downlight_trim", "#F0F0EE", rough=0.3),
        "rubber": mat_simple("KIT_rubber", "#1B1B1C", rough=0.75),
        "plastic_dark": mat_simple("KIT_plastic_dark", "#232427", rough=0.45),
        "edge_band": mat_simple("KIT_edge_band", "#3A3B3D", rough=0.35),
        "screen": mat_screen("KIT_screen_emit"),
        "downlight_emit": mat_emit("KIT_downlight_emit"),
        "ledstrip_emit": mat_emit("KIT_ledstrip_emit"),
        "accent_emit": mat_emit("KIT_accent_emit"),
        # exterior
        "leaves": mat_leaves("KIT_leaves"),
        "bark": mat_simple("KIT_bark", "#4A3A2C", rough=0.9),
        "plaster_ext": mat_paint("KIT_plaster_exterior", "#E4D8C4", rough=0.9, vary=True),
        "window_ext": mat_simple("KIT_window_exterior", "#55656F", rough=0.06, coat=0.6),
        "paving": mat_concrete("KIT_paving", "#B7B1A6", rough=0.85),
        "line_paint": mat_simple("KIT_line_paint", "#F2F2EE", rough=0.6),
    }
    M["skirting"] = M["sill"] = M["door"] = M["wood_light"]
    return M


# --------------------------------------------------------------------------- geometry helpers


def box_uv(bm):
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        n = f.normal
        axis = max(range(3), key=lambda i: abs(n[i]))
        for loop in f.loops:
            co = loop.vert.co
            loop[uv].uv = (co.y, co.z) if axis == 0 else (co.x, co.z) if axis == 1 else (co.x, co.y)


def add_box(bm, x0, x1, y0, y1, z0, z1, mat_index=0):
    vs = [bm.verts.new(c) for c in ((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                                    (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))]
    for idx in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        bm.faces.new([vs[i] for i in idx]).material_index = mat_index


def add_cylinder(bm, cx, cy, z0, z1, r, segments=32, mat_index=0):
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=segments, radius1=r, radius2=r, depth=z1 - z0)
    bmesh.ops.translate(bm, verts=res["verts"], vec=(cx, cy, (z0 + z1) / 2))
    for f in {f for v in res["verts"] for f in v.link_faces}:
        f.material_index = mat_index
        f.smooth = len(f.verts) == 4


def add_rounded_slab(bm, cx, cy, cz, w, d, t, r, segments=6, mat_index=0, plane="XY"):
    """Rounded-rectangle board: w × d in `plane`, thickness t along the third axis, corner radius r."""
    pts = []
    for qx, qy, a0 in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        ccx, ccy = qx * (w / 2 - r), qy * (d / 2 - r)
        for s in range(segments + 1):
            a = math.radians(a0 + 90 * s / segments)
            pts.append((ccx + r * math.cos(a), ccy + r * math.sin(a)))
    def place(u, v, h):
        if plane == "XY":
            return (cx + u, cy + v, cz + h)
        if plane == "XZ":
            return (cx + u, cy + h, cz + v)
        return (cx + h, cy + u, cz + v)  # YZ
    bot = [bm.verts.new(place(u, v, -t / 2)) for u, v in pts]
    top = [bm.verts.new(place(u, v, t / 2)) for u, v in pts]
    n = len(pts)
    bm.faces.new(top).material_index = mat_index
    bm.faces.new(list(reversed(bot))).material_index = mat_index
    for i in range(n):
        j = (i + 1) % n
        f = bm.faces.new([bot[i], bot[j], top[j], top[i]])
        f.material_index = mat_index
        f.smooth = True


def wall_bm(W, H, T, opening=None):
    """Clean all-quad wall slab around an optional opening (x0, x1, z0, z1); z0 = 0 → door."""
    xs, zs = {0.0, W}, {0.0, H}
    if opening:
        x0, x1, z0, z1 = opening
        xs |= {x0, x1}
        zs |= {z0, z1}
    xs, zs = sorted(xs), sorted(zs)
    nx, nz = len(xs) - 1, len(zs) - 1
    bm = bmesh.new()
    V = {}

    def v(i, k, side):
        if (i, k, side) not in V:
            V[(i, k, side)] = bm.verts.new((xs[i], side * T, zs[k]))
        return V[(i, k, side)]

    def solid(i, k):
        if i < 0 or k < 0 or i >= nx or k >= nz:
            return False
        return not (opening and xs[i] >= x0 and xs[i + 1] <= x1 and zs[k] >= z0 and zs[k + 1] <= z1)

    for i in range(nx):
        for k in range(nz):
            if not solid(i, k):
                continue
            bm.faces.new([v(i, k, 0), v(i + 1, k, 0), v(i + 1, k + 1, 0), v(i, k + 1, 0)])
            bm.faces.new([v(i, k, 1), v(i, k + 1, 1), v(i + 1, k + 1, 1), v(i + 1, k, 1)])
            if not solid(i - 1, k):
                bm.faces.new([v(i, k, 0), v(i, k + 1, 0), v(i, k + 1, 1), v(i, k, 1)])
            if not solid(i + 1, k):
                bm.faces.new([v(i + 1, k, 0), v(i + 1, k, 1), v(i + 1, k + 1, 1), v(i + 1, k + 1, 0)])
            if not solid(i, k - 1):
                bm.faces.new([v(i, k, 0), v(i, k, 1), v(i + 1, k, 1), v(i + 1, k, 0)])
            if not solid(i, k + 1):
                bm.faces.new([v(i, k + 1, 0), v(i + 1, k + 1, 0), v(i + 1, k + 1, 1), v(i, k + 1, 1)])
    return bm


def finish_object(name, bm, mats, coll, bevel=0.004, smooth=False, segments=2):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    box_uv(bm)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    if smooth:
        for poly in me.polygons:
            poly.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    if bevel:
        bv = ob.modifiers.new("Bevel", "BEVEL")
        bv.width, bv.segments = bevel, segments
        bv.limit_method = "ANGLE"
        bv.angle_limit = math.radians(40)
        bv.harden_normals = False
    return ob


def fillet_polyline(points, r, steps=6):
    """Round the interior corners of a polyline (bent-tube look)."""
    pts = [Vector(p) for p in points]
    out = [pts[0]]
    for a, b, c in zip(pts, pts[1:], pts[2:]):
        u, w = (a - b).normalized(), (c - b).normalized()
        ang = u.angle(w)
        d = min(r / max(math.tan(ang / 2), 1e-4), (a - b).length * 0.45, (c - b).length * 0.45)
        p1, p2 = b + u * d, b + w * d
        for s in range(steps + 1):
            t = s / steps
            out.append((1 - t) ** 2 * p1 + 2 * (1 - t) * t * b + t ** 2 * p2)
    out.append(pts[-1])
    return out


def tube(name, polylines, radius, mat, coll, fillet=0.06):
    """Round steel tube(s) along polylines, filleted bends, capped ends."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = 4
    cu.use_fill_caps = True
    for pl in polylines:
        pts = fillet_polyline(pl, fillet) if len(pl) > 2 else [Vector(p) for p in pl]
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts) - 1)
        for spt, p in zip(sp.points, pts):
            spt.co = (p.x, p.y, p.z, 1.0)
    cu.materials.append(mat)
    ob = bpy.data.objects.new(name, cu)
    coll.objects.link(ob)
    return ob


def piece_collection(parent, name):
    coll = bpy.data.collections.new(f"PIECE_{name}")
    parent.children.link(coll)
    return coll


# --------------------------------------------------------------------------- architecture pieces


def build_architecture(M, parent):
    H, W, T = ROOM_HEIGHT, MODULE, WALL_T
    HW = ROOM_HEIGHT + WALL_ABOVE_CEILING

    c = piece_collection(parent, "wall_segment")
    finish_object("wall_segment", wall_bm(W, HW, T), [M["wall_paint"]], c)

    c = piece_collection(parent, "wall_window")
    ox0, ox1, oz0, oz1 = 0.3, 2.7, 0.9, 2.9
    finish_object("wall_window", wall_bm(W, HW, T, (ox0, ox1, oz0, oz1)), [M["wall_paint"]], c)
    fw, fy0, fy1 = 0.06, 0.06, 0.14
    mid = (ox0 + ox1) / 2
    bm = bmesh.new()
    add_box(bm, ox0, ox1, fy0, fy1, oz0, oz0 + fw)
    add_box(bm, ox0, ox1, fy0, fy1, oz1 - fw, oz1)
    add_box(bm, ox0, ox0 + fw, fy0, fy1, oz0 + fw, oz1 - fw)
    add_box(bm, ox1 - fw, ox1, fy0, fy1, oz0 + fw, oz1 - fw)
    add_box(bm, mid - 0.025, mid + 0.025, fy0, fy1, oz0 + fw, oz1 - fw)
    finish_object("window_frame", bm, [M["frame"]], c, bevel=0.003)
    bm = bmesh.new()
    add_box(bm, ox0 + fw, mid - 0.025, 0.096, 0.104, oz0 + fw, oz1 - fw)
    add_box(bm, mid + 0.025, ox1 - fw, 0.096, 0.104, oz0 + fw, oz1 - fw)
    glass = finish_object("window_glass", bm, [M["glass"]], c, bevel=0)
    glass.visible_shadow = False
    bm = bmesh.new()
    add_box(bm, ox0 - 0.05, ox1 + 0.05, -0.04, fy0, oz0 - 0.03, oz0)
    finish_object("window_sill", bm, [M["sill"]], c, bevel=0.004)

    c = piece_collection(parent, "door_frame")
    dx0, dx1, dh = 1.0, 2.0, 2.2
    finish_object("door_wall", wall_bm(W, HW, T, (dx0, dx1, 0.0, dh)), [M["wall_paint"]], c)
    lt, aw, at = 0.025, 0.07, 0.015
    bm = bmesh.new()
    add_box(bm, dx0, dx0 + lt, 0, T, 0, dh)
    add_box(bm, dx1 - lt, dx1, 0, T, 0, dh)
    add_box(bm, dx0, dx1, 0, T, dh - lt, dh)
    for y0, y1 in ((-at, 0.0), (T, T + at)):
        add_box(bm, dx0 - aw, dx0, y0, y1, 0, dh + aw)
        add_box(bm, dx1, dx1 + aw, y0, y1, 0, dh + aw)
        add_box(bm, dx0, dx1, y0, y1, dh, dh + aw)
    finish_object("door_casing", bm, [M["door"]], c, bevel=0.003)
    bm = bmesh.new()
    add_box(bm, dx0 + lt + 0.003, dx1 - lt - 0.003, 0.08, 0.12, 0.01, dh - lt - 0.003)
    finish_object("door_leaf", bm, [M["door"]], c, bevel=0.003)
    bm = bmesh.new()
    hx, hz = dx1 - lt - 0.09, 1.05
    for yf, sign in ((0.08, -1), (0.12, 1)):
        y_out = yf + sign * 0.012
        rose = bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=0.026, radius2=0.026, depth=0.012)
        bmesh.ops.rotate(bm, verts=rose["verts"], cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "X"))
        bmesh.ops.translate(bm, verts=rose["verts"], vec=(hx, (yf + y_out) / 2, hz))
        y_a, y_b = sorted((y_out, y_out + sign * 0.05))
        add_box(bm, hx - 0.01, hx + 0.01, y_a, y_b, hz - 0.01, hz + 0.01)
        tip = y_b if sign > 0 else y_a
        add_box(bm, hx - 0.13, hx + 0.01, *sorted((tip - sign * 0.02, tip)), hz - 0.01, hz + 0.01)
    finish_object("door_handle", bm, [M["steel_brushed"]], c, bevel=0.002)
    bm = bmesh.new()
    add_box(bm, 0.0, dx0 - aw, -0.015, 0.0, 0.0, 0.08)
    add_box(bm, dx1 + aw, W, -0.015, 0.0, 0.0, 0.08)
    finish_object("door_skirting", bm, [M["skirting"]], c, bevel=0.002)

    c = piece_collection(parent, "floor_area")
    bm = bmesh.new()
    add_box(bm, 0, W, 0, W, -0.02, 0.0)
    finish_object("floor_area", bm, [M["floor"]], c, bevel=0)

    # Ceiling panel: every visible fixture has a real light under it.
    c = piece_collection(parent, "ceiling_panel")
    bm = bmesh.new()
    add_box(bm, 0, W, 0, W, 0.0, 0.03)
    finish_object("ceiling_panel", bm, [M["ceiling"]], c, bevel=0)
    bm = bmesh.new()
    spots = [(0.75, 0.75), (2.25, 0.75), (0.75, 2.25), (2.25, 2.25)]
    for x, y in spots:
        add_cylinder(bm, x, y, -0.008, 0.0, 0.095, mat_index=0)
        add_cylinder(bm, x, y, -0.010, -0.008, 0.072, mat_index=1)
    add_box(bm, 0.3, 2.7, 1.47, 1.53, -0.008, 0.0, mat_index=0)
    add_box(bm, 0.32, 2.68, 1.48, 1.52, -0.010, -0.008, mat_index=2)
    finish_object("ceiling_fixtures", bm, [M["trim"], M["downlight_emit"], M["ledstrip_emit"]], c, bevel=0.001)
    dl = bpy.data.lights.new("KIT_downlight", "SPOT")
    dl.energy, dl.spot_size, dl.spot_blend, dl.shadow_soft_size = 0.0, math.radians(95), 0.85, 0.07
    dl.shadow_maximum_resolution = 0.01
    for i, (x, y) in enumerate(spots):
        ob = bpy.data.objects.new(f"downlight_{i}", dl)
        ob.location = (x, y, -0.012)
        c.objects.link(ob)
    ls = bpy.data.lights.new("KIT_ledstrip", "AREA")
    ls.shape, ls.size, ls.size_y, ls.energy = "RECTANGLE", 2.36, 0.04, 0.0
    ls.shadow_maximum_resolution = 0.02
    ob = bpy.data.objects.new("ledstrip_light", ls)
    ob.location = (1.5, 1.5, -0.012)
    c.objects.link(ob)

    c = piece_collection(parent, "corner_post")
    bm = bmesh.new()
    add_box(bm, 0, T, 0, T, 0, HW)
    finish_object("corner_post", bm, [M["wall_paint"]], c)

    c = piece_collection(parent, "skirting")
    bm = bmesh.new()
    add_box(bm, 0, W, -0.015, 0.0, 0.0, 0.08)
    finish_object("skirting", bm, [M["skirting"]], c, bevel=0.002)


# --------------------------------------------------------------------------- furniture & fixtures


def build_furniture(M, parent):
    # Student desk (two places): origin = floor centre, front edge (student side) toward −Y.
    c = piece_collection(parent, "desk_double")
    DW, DD, DH = 1.30, 0.55, 0.76
    bm = bmesh.new()
    add_rounded_slab(bm, 0, 0, DH - 0.0125, DW, DD, 0.025, 0.025, segments=5)
    finish_object("desk_top", bm, [M["wood_light"]], c, bevel=0.004, segments=3)
    bm = bmesh.new()
    add_rounded_slab(bm, 0, 0, DH - 0.0255, DW - 0.004, DD - 0.004, 0.0015, 0.024, segments=5)
    finish_object("desk_edge_band", bm, [M["edge_band"]], c, bevel=0)
    s, ix, iy = 0.035, DW / 2 - 0.06, DD / 2 - 0.05  # tube size, leg inset
    bm = bmesh.new()
    for x in (-ix, ix):
        for y in (-iy, iy):
            add_box(bm, x - s / 2, x + s / 2, y - s / 2, y + s / 2, 0.018, DH - 0.025)
    for y in (-iy, iy):  # aprons under the top
        add_box(bm, -ix, ix, y - 0.01, y + 0.01, DH - 0.06, DH - 0.025)
    for x in (-ix, ix):  # side rails top + low
        add_box(bm, x - 0.01, x + 0.01, -iy, iy, DH - 0.06, DH - 0.025)
        add_box(bm, x - 0.012, x + 0.012, -iy, iy, 0.11, 0.135)
    add_box(bm, -ix, ix, -0.012, 0.012, 0.11, 0.135)  # footrest stretcher
    frame = finish_object("desk_frame", bm, [M["frame"]], c, bevel=0.006, segments=3)
    bm = bmesh.new()  # book shelf (perforated look via bump-less thin sheet)
    add_box(bm, -ix + 0.02, ix - 0.02, -0.02, iy - 0.015, 0.585, 0.59)
    add_box(bm, -ix + 0.02, ix - 0.02, iy - 0.02, iy - 0.015, 0.59, 0.66)
    finish_object("desk_shelf", bm, [M["frame"]], c, bevel=0.002)
    bm = bmesh.new()
    for x in (-ix, ix):
        for y in (-iy, iy):
            add_cylinder(bm, x, y, 0.0, 0.018, 0.016, segments=20)
    finish_object("desk_glides", bm, [M["rubber"]], c, bevel=0.002)
    frame["kit_piece_note"] = "steel tube 35 mm, rounded by bevel"

    # School chair: origin = floor centre, seat front toward −Y.
    c = piece_collection(parent, "chair")
    hx, SH = 0.2, 0.43
    loops = []
    for x in (-hx, hx):
        loops.append([(x, 0.21, 0.018), (x, 0.17, SH - 0.02), (x, 0.205, 0.84)])  # back leg → back post
        loops.append([(x, -0.19, 0.018), (x, -0.19, SH - 0.02), (x, 0.16, SH - 0.02)])  # front leg → seat rail
    loops.append([(-hx, -0.17, SH - 0.03), (hx, -0.17, SH - 0.03)])  # seat cross bars
    loops.append([(-hx, 0.15, SH - 0.03), (hx, 0.15, SH - 0.03)])
    tube("chair_frame", loops, 0.011, M["frame"], c, fillet=0.07)
    bm = bmesh.new()
    add_rounded_slab(bm, 0, -0.01, SH + 0.006, 0.43, 0.40, 0.012, 0.05, segments=6)
    finish_object("chair_seat", bm, [M["wood_light"]], c, bevel=0.003, segments=3)
    bm = bmesh.new()
    add_rounded_slab(bm, 0, 0.215, 0.73, 0.42, 0.19, 0.011, 0.045, segments=6, plane="XZ")
    back = finish_object("chair_back", bm, [M["wood_light"]], c, bevel=0.003, segments=3)
    # subdivide-free bend: curve the backrest around the sitter
    bm2 = bmesh.new()
    bm2.from_mesh(back.data)
    for v in bm2.verts:
        v.co.y += 0.35 * (v.co.x ** 2)  # ~1.3 cm deeper at the edges
    bm2.to_mesh(back.data)
    bm2.free()
    bm = bmesh.new()
    for x in (-hx, hx):
        for y in (0.21, -0.19):
            add_cylinder(bm, x, y, 0.0, 0.02, 0.013, segments=16)
    finish_object("chair_glides", bm, [M["rubber"]], c, bevel=0.002)

    # Monitor (unbranded), screen faces −Y.
    c = piece_collection(parent, "monitor")
    bm = bmesh.new()
    add_rounded_slab(bm, 0, 0.04, 0.006, 0.22, 0.17, 0.012, 0.03)
    add_box(bm, -0.025, 0.025, 0.06, 0.08, 0.012, 0.25)
    finish_object("monitor_stand", bm, [M["plastic_dark"]], c, bevel=0.004)
    bm = bmesh.new()
    add_rounded_slab(bm, 0, 0.045, 0.37, 0.55, 0.33, 0.025, 0.01, plane="XZ")
    finish_object("monitor_body", bm, [M["plastic_dark"]], c, bevel=0.003)
    bm = bmesh.new()
    add_box(bm, -0.265, 0.265, 0.0315, 0.0325, 0.215, 0.515)
    scr = finish_object("monitor_screen", bm, [M["screen"]], c, bevel=0)
    uv = scr.data.uv_layers.active.data  # 0..1 UV across the screen for the UI texture
    for poly in scr.data.polygons:
        for li in poly.loop_indices:
            co = scr.data.vertices[scr.data.loops[li].vertex_index].co
            uv[li].uv = ((co.x + 0.265) / 0.53, (co.z - 0.215) / 0.30)
    sl = bpy.data.lights.new("KIT_screen", "AREA")
    sl.shape, sl.size, sl.size_y, sl.energy, sl.use_shadow = "RECTANGLE", 0.53, 0.30, 0.0, False
    ob = bpy.data.objects.new("screen_light", sl)
    ob.location = (0, 0.03, 0.365)
    ob.rotation_euler = (math.radians(90), 0, 0)  # area light faces its −Z → world −Y
    c.objects.link(ob)

    # LED accent channel 3 m, light faces −Z
    c = piece_collection(parent, "led_accent")
    bm = bmesh.new()
    add_box(bm, 0, MODULE, -0.012, 0.012, 0.0, 0.014, mat_index=0)
    add_box(bm, 0.01, MODULE - 0.01, -0.009, 0.009, -0.002, 0.0, mat_index=1)
    finish_object("led_accent_channel", bm, [M["steel_brushed"], M["accent_emit"]], c, bevel=0.001)
    al = bpy.data.lights.new("KIT_accent", "AREA")
    al.shape, al.size, al.size_y, al.energy, al.use_shadow = "RECTANGLE", MODULE - 0.02, 0.018, 0.0, False
    ob = bpy.data.objects.new("accent_light", al)
    ob.location = (MODULE / 2, 0, -0.004)
    c.objects.link(ob)


# --------------------------------------------------------------------------- exterior backdrop (exterior = local +Y)


def build_exterior(M, parent):
    c = piece_collection(parent, "exterior_backdrop")
    rnd = random.Random(7)
    bm = bmesh.new()
    add_box(bm, -70, 70, 0.2, 140, -0.30, -0.15)
    finish_object("yard_paving", bm, [M["paving"]], c, bevel=0)
    bm = bmesh.new()  # painted court lines on the yard
    for y in (5.0, 17.0):
        add_box(bm, -12, 12, y - 0.05, y + 0.05, -0.15, -0.148)
    for x in (-12.0, 12.0, 0.0):
        add_box(bm, x - 0.05, x + 0.05, 5.0, 17.0, -0.15, -0.148)
    finish_object("yard_lines", bm, [M["line_paint"]], c, bevel=0)
    bm = bmesh.new()
    add_box(bm, -70, 70, 20.0, 30.0, -0.15, -0.10)
    add_box(bm, -70, -16, 2.0, 20.0, -0.15, -0.10)
    add_box(bm, 16, 70, 2.0, 20.0, -0.15, -0.10)
    finish_object("lawn", bm, [M["grass_artificial"]], c, bevel=0)

    # Trees: trunk + displaced leafy crown clusters
    tex = bpy.data.textures.new("KIT_crown_noise", "CLOUDS")
    tex.noise_scale = 0.9
    for i in range(14):
        if i < 9:  # row of trees on the lawn beyond the yard
            x, y = rnd.uniform(-45, 45), rnd.uniform(21, 29)
        else:  # a few closer trees at the sides of the yard
            x, y = rnd.choice((-1, 1)) * rnd.uniform(22, 45), rnd.uniform(10, 18)
        h = rnd.uniform(2.6, 3.6)
        r = rnd.uniform(2.0, 3.2)
        bm = bmesh.new()
        res = bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.18, radius2=0.11, depth=h + r * 0.6)
        bmesh.ops.translate(bm, verts=res["verts"], vec=(x, y, -0.15 + (h + r * 0.6) / 2))
        finish_object(f"tree_trunk_{i}", bm, [M["bark"]], c, bevel=0, smooth=True)
        for k in range(3):
            bm = bmesh.new()
            bmesh.ops.create_icosphere(bm, subdivisions=3, radius=r * rnd.uniform(0.6, 0.85))
            off = Vector((rnd.uniform(-0.6, 0.6) * r, rnd.uniform(-0.5, 0.5) * r, rnd.uniform(-0.2, 0.4) * r))
            bmesh.ops.scale(bm, vec=(1.0, 1.0, rnd.uniform(0.8, 1.0)), verts=bm.verts)
            bmesh.ops.translate(bm, verts=bm.verts, vec=Vector((x, y, h + r * 0.5)) + off)
            crown = finish_object(f"tree_crown_{i}_{k}", bm, [M["leaves"]], c, bevel=0, smooth=True)
            d = crown.modifiers.new("Leafy", "DISPLACE")
            d.texture, d.strength, d.texture_coords = tex, r * 0.35, "GLOBAL"

    # Neighbouring low buildings (2–3 storeys) with window bands facing the school (−Y faces)
    for x0, x1, y0, depth, height in ((-70, -30, 75, 14, 7.2), (-18, 14, 88, 12, 10.4), (26, 66, 72, 14, 7.2)):
        bm = bmesh.new()
        add_box(bm, x0, x1, y0, y0 + depth, -0.15, height)
        add_box(bm, x0 - 0.15, x1 + 0.15, y0 - 0.15, y0 + depth + 0.15, height, height + 0.6)  # parapet
        finish_object(f"building_{x0}", bm, [M["plaster_ext"]], c, bevel=0.02)
        bm = bmesh.new()
        floors = int(height // 3.4) + 1
        for f in range(floors):
            z = 0.9 + f * 3.4
            if z + 1.6 > height:
                break
            xx = x0 + 1.5
            while xx + 1.8 < x1 - 1.0:
                add_box(bm, xx, xx + 1.8, y0 - 0.03, y0, z, z + 1.6)
                xx += 3.0
        finish_object(f"building_windows_{x0}", bm, [M["window_ext"]], c, bevel=0)


# --------------------------------------------------------------------------- lighting presets


def hdri_world(name, hdri_file, rotation_deg, seen_strength, ambient_hex, ambient_strength):
    """The camera (and rays through glass) see an HDRI; diffuse lighting uses a neutral ambient colour.
    Interiors are lit by the kit's real lights + sun; the HDRI only provides the view and reflections."""
    w = bpy.data.worlds.new(name)
    _ensure_nodes(w)
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value = (0, 0, math.radians(rotation_deg))
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(str(hdri_file), check_existing=True)
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
    seen = nt.nodes.new("ShaderNodeBackground")
    seen.inputs["Strength"].default_value = seen_strength
    nt.links.new(env.outputs["Color"], seen.inputs["Color"])
    amb = nt.nodes.new("ShaderNodeBackground")
    amb.inputs["Color"].default_value = C.hex_rgba(ambient_hex)
    amb.inputs["Strength"].default_value = ambient_strength
    lp = nt.nodes.new("ShaderNodeLightPath")
    mx_f = nt.nodes.new("ShaderNodeMath")
    mx_f.operation = "MAXIMUM"
    nt.links.new(lp.outputs["Is Camera Ray"], mx_f.inputs[0])
    nt.links.new(lp.outputs["Is Transmission Ray"], mx_f.inputs[1])
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mx_f.outputs[0], mix.inputs["Fac"])
    nt.links.new(amb.outputs[0], mix.inputs[1])
    nt.links.new(seen.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    w.use_fake_user = True
    return w


def sun(name, coll, elevation_deg, azimuth_deg, energy, kelvin, angle_deg=2.0):
    """azimuth = compass direction the light COMES FROM (0 = +X, 90 = +Y)."""
    d = bpy.data.lights.new(name, "SUN")
    d.energy, d.use_temperature, d.temperature, d.angle = energy, True, kelvin, math.radians(angle_deg)
    d.use_shadow_jitter = True  # soft, accurate penumbra in final renders
    ob = bpy.data.objects.new(name, d)
    el, az = math.radians(elevation_deg), math.radians(azimuth_deg)
    towards = -Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))
    ob.rotation_euler = towards.to_track_quat("-Z", "Y").to_euler()
    coll.objects.link(ob)
    return ob


def build_lighting(root):
    lights = bpy.data.collections.new("LIGHTS")
    root.children.link(lights)

    def preset(name, cfg):
        coll = bpy.data.collections.new(f"LIGHT_{name}")
        lights.children.link(coll)
        coll["preset"] = json.dumps(cfg)
        return coll

    off = dict(watts=0.0, kelvin=4000, emit=0.0)

    # day_interior: sun through the windows + ceiling lights on at a classroom level
    hdri_world("W_day_interior", HDRI_DIR / "forest.exr", 200, 0.9, "#E9E2D6", 0.45)
    c = preset("day_interior", dict(
        world="W_day_interior", exposure=0.0,
        downlight=dict(watts=9.0, kelvin=4000, emit=18.0),
        ledstrip=dict(watts=10.0, kelvin=4000, emit=10.0),
        accent=off, screen=dict(watts=1.5, kelvin=6500, emit=2.5),
    ))
    sun("SUN_day_interior", c, 32, 15, 7.5, 5300)

    # warm_interior: evening; white ceiling stays white — warmth only from 3000 K light colour
    hdri_world("W_warm_interior", HDRI_DIR / "sunset.exr", 200, 0.35, "#F2F1EE", 0.38)
    preset("warm_interior", dict(
        world="W_warm_interior", exposure=0.0,
        downlight=dict(watts=24.0, kelvin=3000, emit=45.0),
        ledstrip=dict(watts=26.0, kelvin=3000, emit=16.0),
        accent=off, screen=dict(watts=1.5, kelvin=6500, emit=2.5),
    ))

    # tech_dark: neutral dark room; colour only from LED accents, LED slots and screens
    hdri_world("W_tech_dark", HDRI_DIR / "night.exr", 200, 0.25, "#101113", 0.6)
    preset("tech_dark", dict(
        world="W_tech_dark", exposure=0.4,
        downlight=dict(watts=7.0, kelvin=3800, emit=12.0),
        ledstrip=dict(watts=4.0, rgb=[0.50, 0.25, 1.0], emit=14.0),
        accent=dict(watts=30.0, rgb=[0.12, 0.38, 1.0], emit=25.0),
        screen=dict(watts=4.0, kelvin=8000, emit=4.0),
    ))

    # outdoor_day: high sun, HDRI sky, brighter cool ambient; interior fixtures off
    hdri_world("W_outdoor_day", HDRI_DIR / "forest.exr", 200, 1.0, "#DCE3EA", 0.8)
    c = preset("outdoor_day", dict(
        world="W_outdoor_day", exposure=0.0,
        downlight=off, ledstrip=off, accent=off, screen=dict(watts=0.0, kelvin=6500, emit=1.0),
    ))
    sun("SUN_outdoor_day", c, 52, 35, 8.0, 5600, angle_deg=1.0)


# --------------------------------------------------------------------------- main


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = Path(argv[argv.index("--out") + 1]) if "--out" in argv else C.KIT_DIR / "school_kit.blend"

    C.reset_scene()
    sc = bpy.context.scene
    sc.name = "KIT"
    C.apply_render_settings(sc)
    sc["kit_design_language"] = P["label"]

    root = sc.collection
    pieces = bpy.data.collections.new("KIT_pieces")
    root.children.link(pieces)
    M = build_materials()
    build_architecture(M, pieces)
    build_furniture(M, pieces)
    build_exterior(M, pieces)
    for coll in pieces.children:
        try:
            coll.asset_mark()
        except (AttributeError, RuntimeError):
            pass
    build_lighting(root)

    rig_coll = bpy.data.collections.new("CAM_RIG")
    root.children.link(rig_coll)
    rig, cam, focus = C.make_camera_rig("RIG", lens=35, location=(4.5, 0.8, 1.55), focus_location=(4.5, 5.0, 1.2))
    for ob in (rig, cam, focus):
        for uc in list(ob.users_collection):
            uc.objects.unlink(ob)
        rig_coll.objects.link(ob)

    C._find_layer_collection(bpy.context.view_layer.layer_collection, "KIT_pieces").exclude = True
    C.apply_lighting_preset("day_interior")

    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(out), check_existing=False, relative_remap=True)
    print(f"KIT_OK {P['label']} → {out}")


if __name__ == "__main__":
    main()
