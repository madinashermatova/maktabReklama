"""The school cafeteria's glass wall + interior — ONE definition shared by scene 2 (seen from the courtyard, outside)
and scene 8 (inside), so both show the same building (user, 2026-11-27: the building straight ahead after the entrance
turnstile is the cafeteria, with a glass facade).

    import kit_cafeteria as KC
    M = KC.materials()
    KC.glass_wall(coll, M, x0, x1, y, z0, z1, door_x=...)        # facade plane y = outer glass face, inside = +Y
    KC.interior(coll, M, x0, x1, y0, y1, h, rnd)               # furnished room behind it (+Y side) — scene 8 only
    M["glass"] = KC.mirror_glass()                              # scene 2 (outside): reflective tinted glass, no interior

Glass wall (design language A shell): slim graphite (#2E3135) mullions on a 1.6 m-ish module, one transom at door
height (2.7 m), large clear panes, a frameless glass double door with two steel pull bars.
Interior (scene 8 atmosphere, docs/design-language.md → Room atmospheres): cream walls, terracotta tile floor, white
ceiling with warm downlights, long light-oak tables with benches in rows parallel to the glass, warm pendant lamps
(2700 K) over every table, unbranded blue-and-white ceramic plates/bowls, a serving counter along the back wall.
No people, no text, no logos.
"""

from __future__ import annotations

import math

import bmesh
import bpy
from mathutils import Vector

import _common as C
import build_kit as K

FRAME_HEX = "#2E3135"  # design language A graphite frames (build_kit P["frame"])
OAK_HEX = "#CDAE88"  # design language A light oak (build_kit P["wood_light"])
WARM_K = 2700


def materials():
    M = {}
    M["glass"] = K.mat_glass("CAF_glass")
    gb = next(n for n in M["glass"].node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    K.bsdf_set(gb, color=C.hex_rgba("#E4ECE8"), ior=1.6)  # clear float glass, faint green edge tint, a touch more facade reflection
    M["frame"] = K.mat_simple("CAF_frame_graphite", FRAME_HEX, rough=0.38, coat=0.15)
    M["steel"] = K.mat_metal("CAF_steel_brushed", "#C3C6C9", 0.25, brushed=True)
    M["wall"] = K.mat_simple("CAF_wall_cream", "#EFE4D2", rough=0.85)
    M["ceiling"] = K.mat_simple("CAF_ceiling_white", "#F3F1EC", rough=0.8)
    M["oak"] = K.mat_wood("CAF_oak", OAK_HEX, vary=True)

    m, nt, b = K.new_material("CAF_terracotta_floor")  # 300 mm terracotta tiles, cream joints, satin
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.offset, br.offset_frequency = 0.0, 1
    for k, v in (("Scale", 1.0), ("Brick Width", 0.3), ("Row Height", 0.3), ("Mortar Size", 0.004),
                 ("Mortar Smooth", 0.2), ("Bias", 0.0), ("Color1", C.hex_rgba("#B4623F")), ("Color2", C.hex_rgba("#A6583A")),
                 ("Mortar", C.hex_rgba("#D9CDB8"))):
        K._sock(br, k, v)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tc.outputs["Object"], br.inputs["Vector"])
    nt.links.new(br.outputs["Color"], b.inputs["Base Color"])
    K.bsdf_set(b, rough=0.32)
    M["floor"] = m

    m, nt, b = K.new_material("CAF_terracotta")  # pendant shades, counter front, accents
    K.bsdf_set(b, color=C.hex_rgba("#B5643F"), rough=0.55)
    M["terracotta"] = m

    m, nt, b = K.new_material("CAF_ceramic_blue_white")  # unbranded blue-and-white glaze: concentric cobalt rings
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wv = nt.nodes.new("ShaderNodeTexWave")
    wv.wave_type = "RINGS"
    wv.inputs["Scale"].default_value = 14.0
    wv.inputs["Distortion"].default_value = 1.5
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    nt.links.new(K.ramp(nt, wv.outputs["Fac"], [(0.55, C.hex_rgba("#F4F3EE")), (0.72, C.hex_rgba("#1F4E9A"))]),
                 b.inputs["Base Color"])
    K.bsdf_set(b, rough=0.12, coat=0.6)
    M["ceramic"] = m

    M["warm_emit"] = K.mat_emit("CAF_warm_emit", kelvin=WARM_K, strength=12.0)
    M["downlight_emit"] = K.mat_emit("CAF_downlight_emit", kelvin=3000, strength=6.0)
    return M


def mirror_glass():
    """Reflective tinted facade glass (one-way-mirror look) for the OUTSIDE view (scene 2, user 2026-11-28): opaque,
    cool grey-blue metallic reflection of the sky, courtyard and palms; the interior is revealed only in scene 8."""
    m, nt, b = K.new_material("CAF_glass_mirror")
    K.bsdf_set(b, color=C.hex_rgba("#8C9AA3"), rough=0.02, metal=1.0, coat=1.0, coat_rough=0.01)
    return m


def _box(bm, x0, x1, y0, y1, z0, z1):
    K.add_box(bm, min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1), min(z0, z1), max(z0, z1))


def glass_wall(coll, M, x0, x1, y, z0, z1, door_x=None, module=1.6, transom=2.7):
    """Curtain wall between x0 and x1, outer glass face at y (inside = +Y). Returns the door centre x."""
    n = max(1, round((x1 - x0) / module))
    mod = (x1 - x0) / n
    xs = [x0 + k * mod for k in range(n + 1)]
    if door_x is not None:  # the door = the two panes either side of the mullion nearest door_x
        dk = min(range(1, n), key=lambda k: abs(xs[k] - door_x))
        door_x = xs[dk]
    fd = 0.14  # frame depth
    bm = bmesh.new()
    for k, x in enumerate(xs):
        if door_x is not None and k == dk:
            continue  # no mullion between the two door leaves (meeting stiles instead)
        hw = 0.035 if k in (0, n) else 0.025
        _box(bm, x - hw, x + hw, y - 0.02, y + fd, z0, z1)
    _box(bm, x0, x1, y - 0.02, y + fd, z1 - 0.08, z1)  # head
    _box(bm, x0, x1, y - 0.03, y + fd, z0, z0 + 0.05)  # sill
    _box(bm, x0, x1, y - 0.02, y + fd, transom - 0.03, transom + 0.03)  # transom
    if door_x is not None:
        for sx in (-1, 1):  # door leaf stiles / rails (slim)
            for a, b_ in ((door_x + sx * 0.012, door_x + sx * 0.05), (door_x + sx * (mod - 0.05), door_x + sx * (mod - 0.012))):
                _box(bm, a, b_, y + 0.03, y + 0.08, z0 + 0.05, transom - 0.03)
            _box(bm, door_x, door_x + sx * mod, y + 0.03, y + 0.08, z0 + 0.05, z0 + 0.12)
    K.finish_object("cafeteria_glass_frames", bm, [M["frame"]], coll, bevel=0.003)

    bm = bmesh.new()  # one clear pane plane behind the frames (the frames cover the joints)
    vs = [bm.verts.new(v) for v in ((x0, y + 0.05, z0 + 0.05), (x1, y + 0.05, z0 + 0.05), (x1, y + 0.05, z1 - 0.08),
                                    (x0, y + 0.05, z1 - 0.08))]
    bm.faces.new(vs)
    K.finish_object("cafeteria_glass_panes", bm, [M["glass"]], coll, bevel=0)

    if door_x is not None:
        hs = []
        for sx in (-1, 1):
            hx = door_x + sx * 0.14
            for side_y in (y - 0.07, y + 0.17):
                hs.append([(hx, side_y, 0.85), (hx, side_y, 1.95)])
        K.tube("cafeteria_door_pulls", hs, 0.016, M["steel"], coll, fillet=0)
        bm = bmesh.new()
        for sx in (-1, 1):
            hx = door_x + sx * 0.14
            for side_y, dy in ((y - 0.07, 0.07), (y + 0.17, -0.07)):
                for zz in (0.95, 1.85):
                    _box(bm, hx - 0.008, hx + 0.008, min(side_y, side_y + dy), max(side_y, side_y + dy), zz - 0.008, zz + 0.008)
        K.finish_object("cafeteria_door_pull_standoffs", bm, [M["steel"]], coll, bevel=0)
    return door_x


def interior(coll, M, x0, x1, y0, y1, h, rnd, counter_x=None):
    """Furnished cafeteria room x0..x1 × y0..y1 (glass wall at y0), clear height h."""
    bm = bmesh.new()
    _box(bm, x0, x1, y0, y1, -0.02, 0.0)
    K.finish_object("cafeteria_floor", bm, [M["floor"]], coll, bevel=0)
    bm = bmesh.new()
    _box(bm, x0 - 0.2, x1 + 0.2, y1, y1 + 0.2, 0.0, h + 0.3)
    _box(bm, x0 - 0.2, x0, y0, y1, 0.0, h + 0.3)
    _box(bm, x1, x1 + 0.2, y0, y1, 0.0, h + 0.3)
    K.finish_object("cafeteria_walls", bm, [M["wall"]], coll, bevel=0)
    bm = bmesh.new()
    _box(bm, x0, x1, y0, y1, h, h + 0.02)
    K.finish_object("cafeteria_ceiling", bm, [M["ceiling"]], coll, bevel=0)

    # warm downlights in the ceiling (emissive discs + a few area lights for the room fill)
    bm = bmesh.new()
    gx = max(2, round((x1 - x0) / 2.4))
    for i in range(gx):
        for j, yy in enumerate((y0 + 1.0, y0 + (y1 - y0) * 0.5, y1 - 1.0)):
            cx = x0 + (i + 0.5) * (x1 - x0) / gx
            res = bmesh.ops.create_circle(bm, cap_ends=True, segments=20, radius=0.08)
            bmesh.ops.translate(bm, verts=res["verts"], vec=(cx, yy, h - 0.002))
    K.finish_object("cafeteria_downlights", bm, [M["downlight_emit"]], coll, bevel=0)
    fill = bpy.data.lights.new("CAF_fill", "AREA")
    fill.shape, fill.size, fill.size_y = "RECTANGLE", x1 - x0 - 1.0, y1 - y0 - 1.0
    fill.energy = 140.0 * (x1 - x0) * (y1 - y0) / 75.0
    fill.use_shadow = True
    if hasattr(fill, "temperature"):
        fill.temperature = 3000
    else:
        fill.color = C.kelvin_rgba(3000)[:3]
    fo = bpy.data.objects.new("CAF_fill", fill)
    fo.location = ((x0 + x1) / 2, (y0 + y1) / 2, h - 0.05)
    coll.objects.link(fo)

    # serving counter along the back wall (oak top, terracotta front)
    cx0, cx1 = (counter_x if counter_x else (x0 + 1.0, x0 + 5.0))
    bm = bmesh.new()
    _box(bm, cx0, cx1, y1 - 0.75, y1 - 0.02, 0.0, 0.9)
    K.finish_object("cafeteria_counter_front", bm, [M["terracotta"]], coll, bevel=0.004)
    bm = bmesh.new()
    _box(bm, cx0 - 0.03, cx1 + 0.03, y1 - 0.8, y1 - 0.02, 0.9, 0.94)
    K.finish_object("cafeteria_counter_top", bm, [M["oak"]], coll, bevel=0.003)

    # long tables in rows parallel to the glass, benches both sides, ceramics, warm pendants
    T_L, T_W, T_H = 2.4, 0.8, 0.75
    rows = [y0 + 1.35, y0 + 1.35 + 1.9] if (y1 - y0) > 4.2 else [y0 + (y1 - y0) * 0.4]
    n_t = max(1, int((x1 - x0 - 0.8) // (T_L + 0.9)))
    gap = (x1 - x0 - n_t * T_L) / (n_t + 1)
    bm_top, bm_leg, bm_cer, bm_shade, bm_glow = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
    cords = []
    for ry in rows:
        for t in range(n_t):
            tx0 = x0 + gap + t * (T_L + gap)
            tx1 = tx0 + T_L
            _box(bm_top, tx0, tx1, ry - T_W / 2, ry + T_W / 2, T_H - 0.04, T_H)
            for sy in (-1, 1):  # benches
                by = ry + sy * (T_W / 2 + 0.28)
                _box(bm_top, tx0 + 0.1, tx1 - 0.1, by - 0.17, by + 0.17, 0.42, 0.46)
                for lx in (tx0 + 0.25, tx1 - 0.25):
                    _box(bm_leg, lx - 0.02, lx + 0.02, by - 0.13, by + 0.13, 0.0, 0.42)
            for lx in (tx0 + 0.2, tx1 - 0.2):  # table trestles
                _box(bm_leg, lx - 0.025, lx + 0.025, ry - T_W / 2 + 0.08, ry + T_W / 2 - 0.08, 0.0, T_H - 0.04)
                _box(bm_leg, lx - 0.025, lx + 0.025, ry - 0.02, ry + 0.02, 0.0, T_H - 0.04)
            for k in range(rnd.randint(3, 6)):  # set places: plates and bowls
                px = tx0 + 0.3 + (T_L - 0.6) * (k + rnd.uniform(0.2, 0.8)) / 6
                py = ry + rnd.choice((-1, 1)) * 0.22
                r = rnd.choice((0.11, 0.12, 0.075))
                K.add_cylinder(bm_cer, px, py, T_H, T_H + (0.018 if r > 0.1 else 0.055), r, segments=24)
            for k in range(2):  # pendants: two per table
                lx = tx0 + T_L * (0.28 + 0.44 * k)
                z_s = h - 1.15
                K.add_cylinder(bm_shade, lx, ry, z_s, z_s + 0.24, 0.17, segments=28)
                res = bmesh.ops.create_circle(bm_glow, cap_ends=True, segments=24, radius=0.15)
                bmesh.ops.translate(bm_glow, verts=res["verts"], vec=(lx, ry, z_s - 0.002))
                cords.append([(lx, ry, z_s + 0.24), (lx, ry, h)])
                pl = bpy.data.lights.new("CAF_pendant", "POINT")
                pl.energy = 35.0
                pl.shadow_soft_size = 0.1
                pl.use_shadow = False  # many small pendants: no shadow maps (EEVEE shadow buffer), the area fill casts them
                pl.color = C.kelvin_rgba(WARM_K)[:3]
                po = bpy.data.objects.new("CAF_pendant", pl)
                po.location = (lx, ry, z_s - 0.08)
                coll.objects.link(po)
    K.finish_object("cafeteria_tables_benches", bm_top, [M["oak"]], coll, bevel=0.004)
    K.finish_object("cafeteria_table_legs", bm_leg, [M["frame"]], coll, bevel=0.002)
    K.finish_object("cafeteria_ceramics", bm_cer, [M["ceramic"]], coll, bevel=0.003, smooth=True)
    K.finish_object("cafeteria_pendant_shades", bm_shade, [M["terracotta"]], coll, bevel=0.004, smooth=True)
    K.finish_object("cafeteria_pendant_glow", bm_glow, [M["warm_emit"]], coll, bevel=0)
    K.tube("cafeteria_pendant_cords", cords, 0.004, M["frame"], coll, fillet=0)
