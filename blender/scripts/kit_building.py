"""Kit pieces for the school building exterior + shared tree generator. Imported by build_kit.py.

PIECE_school_building   the school (design language A). Origin = ground level (z = 0) at the centre of the
                        main facade line; the main facade faces −Y. 3 storeys (neutral choice — no real
                        details provided), 48 × 15 m teaching wing on a 3 m window module that matches the
                        interior kit (2.4 × 2.0 m windows, sill 0.90 m), ground floor at +0.45 m,
                        floor-to-floor 3.9 m, flat roof with parapet. Central glazed entrance core (12 m)
                        in a teal portal frame, cantilevered canopy with oak soffit, steps + ramp.
                        Interiors behind the glass are shallow room shells (ceiling lights, blinds) so the
                        windows read as real rooms. No signage, no symbol (CLAUDE.md → BRAND).
PIECE_school_grounds    forecourt paving, entrance path, lawn, kerbs, planters, benches, bollard lights, trees.

make_tree()             trunk + branches + a canopy of displaced leaf clusters with alpha leaf cards.
"""

from __future__ import annotations

import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

import _common as C
import build_kit as K

GROUND_FLOOR = 0.45
FLOOR_TO_FLOOR = 3.9
FLOORS = 3
MODULE = 3.0
WING_X = (-24.0, 24.0)
WING_DEPTH = 15.0
WALL_T = 0.35
RECESS = 0.12  # window frame set back from the outer facade face
ROOF_Z = GROUND_FLOOR + FLOORS * FLOOR_TO_FLOOR  # 12.15
PARAPET = 1.0
CORE_X = (-6.0, 6.0)
CORE_FRONT = -2.0
CORE_TOP = ROOF_Z + PARAPET + 0.9


# --------------------------------------------------------------------------- materials


def exterior_materials():
    M = {}
    # Facade render: warm white (wall colour of the design language) with large, very soft tonal variation
    m, nt, b = K.new_material("KIT_render_facade")
    base = C.hex_rgba("#ECE6DC")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n_big = K.noise(nt, tc.outputs["Object"], 0.12, 3.0, 0.5)
    col = K.ramp(nt, n_big.outputs["Fac"], [(0.35, K.shade(base, 0.93)), (0.5, base), (0.65, K.shade(base, 1.03))])
    n_mid = K.noise(nt, tc.outputs["Object"], 1.6, 6.0, 0.6)
    col = K.mix_color(nt, col, K.ramp(nt, n_mid.outputs["Fac"], [(0.4, K.shade(base, 0.97)), (0.6, K.shade(base, 1.01))]),
                      0.5, "MULTIPLY")
    nt.links.new(K.per_object_variation(nt, col, 0.03), b.inputs["Base Color"])
    K.bsdf_set(b, rough=0.88)
    K.bump(nt, b, K.noise(nt, tc.outputs["Object"], 180.0, 6.0, 0.65).outputs["Fac"], 0.18, 0.004)
    M["render"] = m
    M["render_band"] = K.mat_paint("KIT_render_band", "#DCD4C7", rough=0.85)
    M["plinth"] = K.mat_concrete("KIT_plinth_stone", "#7E7A74", rough=0.7)
    M["roof"] = K.mat_concrete("KIT_roof_gravel", "#8D8A85", rough=0.95)
    M["interior_wall"] = K.mat_simple("KIT_interior_shell", "#D9D2C6", rough=0.9, vary=0.1)
    M["interior_dark"] = K.mat_simple("KIT_interior_shadow", "#5A5650", rough=0.9)
    M["interior_light"] = K.mat_emit("KIT_interior_light_emit", 4000, 6.0)
    M["blind"] = K.mat_simple("KIT_blind_fabric", "#E8E3D8", rough=0.95, vary=0.05)
    M["soffit_light"] = K.mat_emit("KIT_soffit_light_emit", 3500, 0.6)
    M["paving_slab"] = _mat_paving()
    M["kerb"] = K.mat_concrete("KIT_kerb", "#A39E96", rough=0.8)
    M["soil"] = K.mat_simple("KIT_soil_mulch", "#4B3A2C", rough=0.95)
    M["leaf_card"] = _mat_leaf_card()
    return M


def _mat_paving():
    m, nt, b = K.new_material("KIT_paving_slabs")
    base = C.hex_rgba("#BDB6AA")
    vec = K.uv_vec(nt)
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.offset, br.offset_frequency = 0.5, 1
    for k, v in (("Scale", 1.0), ("Brick Width", 0.6), ("Row Height", 0.3), ("Mortar Size", 0.006),
                 ("Mortar Smooth", 0.3), ("Color1", base), ("Color2", K.shade(base, 0.9)), ("Mortar", K.shade(base, 0.6))):
        K._sock(br, k, v)
    nt.links.new(vec, br.inputs["Vector"])
    n = K.noise(nt, vec, 3.0, 8.0, 0.6)
    col = K.mix_color(nt, br.outputs["Color"], K.ramp(nt, n.outputs["Fac"], [(0.35, K.shade(base, 0.85)), (0.65, K.shade(base, 1.05))]),
                      0.5, "MULTIPLY")
    nt.links.new(col, b.inputs["Base Color"])
    nt.links.new(K.map_range(nt, K.noise(nt, vec, 40.0, 4.0, 0.6).outputs["Fac"], 0.7, 0.9), b.inputs["Roughness"])
    inv = nt.nodes.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    nt.links.new(br.outputs["Fac"], inv.inputs[1])
    K.bump(nt, b, inv.outputs[0], 0.3, 0.004)
    return m


def _mat_leaf_card():
    """Alpha-masked leaf on a 0..1 UV card: pointed ellipse, colour varies per card (UV-independent noise)."""
    m, nt, b = K.new_material("KIT_leaf_card")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["UV"], sep.inputs[0])

    def math_node(op, a, bb=None):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = op
        for i, v in enumerate((a, bb)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                nt.links.new(v, n.inputs[i])
        return n.outputs[0]

    u = math_node("MULTIPLY", math_node("SUBTRACT", sep.outputs["X"], 0.5), 2.0)  # −1..1 across
    v = sep.outputs["Y"]  # 0 (stem) .. 1 (tip)
    width = math_node("SINE", math_node("MULTIPLY", math_node("POWER", v, 0.8), math.pi))  # 0 at stem and tip
    inside = math_node("LESS_THAN", math_node("ABSOLUTE", u), math_node("MULTIPLY", width, 0.95))
    nt.links.new(inside, b.inputs["Alpha"])
    n = K.noise(nt, tc.outputs["Object"], 2.2, 4.0, 0.6)
    col = K.ramp(nt, n.outputs["Fac"], [(0.3, C.hex_rgba("#2B4F1E")), (0.5, C.hex_rgba("#47742A")), (0.72, C.hex_rgba("#7C9F45"))])
    nt.links.new(K.per_object_variation(nt, col, 0.12), b.inputs["Base Color"])
    K.bsdf_set(b, rough=0.55, sss=0.0)
    if "Transmission Weight" in b.inputs:
        b.inputs["Transmission Weight"].default_value = 0.0
    for prop, val in (("surface_render_method", "DITHERED"), ("use_backface_culling", False)):
        try:
            setattr(m, prop, val)
        except (AttributeError, TypeError):
            pass
    try:
        m.blend_method = "HASHED"
    except (AttributeError, TypeError):
        pass
    return m


# --------------------------------------------------------------------------- trees


def make_tree(name, loc, coll, M, rnd: random.Random, height=7.0, crown_r=3.0, clusters=34, cards_per_vert=0.8,
              leaf_size=0.22):
    """Deciduous tree: tapered trunk with 4–6 main branches, canopy of displaced leaf clusters (solid cores so
    the canopy has body and self-shadowing) dressed with alpha leaf cards so the silhouette is broken and leafy.
    Returns the list of created objects."""
    x, y, z = loc
    objs = []
    trunk_h = height - crown_r * 1.55
    crown_c = Vector((x, y, z + trunk_h + crown_r * 0.72))
    # Trunk + branches as tubes
    polys = [[(x, y, z - 0.1), (x + rnd.uniform(-0.15, 0.15), y + rnd.uniform(-0.15, 0.15), z + trunk_h * 0.6),
              (x + rnd.uniform(-0.25, 0.25), y + rnd.uniform(-0.25, 0.25), z + trunk_h)]]
    branch_tips = []
    for k in range(rnd.randint(4, 6)):
        a = k / 5 * 2 * math.pi + rnd.uniform(-0.4, 0.4)
        r = crown_r * rnd.uniform(0.45, 0.7)
        tip = crown_c + Vector((math.cos(a) * r, math.sin(a) * r, rnd.uniform(-0.2, 0.6) * crown_r))
        base = Vector(polys[0][-1]) + Vector((0, 0, rnd.uniform(-0.6, 0.2)))
        mid = base.lerp(tip, 0.5) + Vector((0, 0, 0.25))
        polys.append([tuple(base), tuple(mid), tuple(tip)])
        branch_tips.append(tip)
    trunk = K.tube(f"{name}_trunk", polys[:1], 0.17 * height / 7, M["bark"], coll, fillet=0.4)
    branches = K.tube(f"{name}_branches", polys[1:], 0.07 * height / 7, M["bark"], coll, fillet=0.5)
    for t in (trunk, branches):  # taper: thicker at the base
        t.data.bevel_resolution = 3
    objs += [trunk, branches]

    # Canopy: clusters distributed in an ellipsoid, denser toward the outside, a few at branch tips
    centres = list(branch_tips)
    while len(centres) < clusters:
        d = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 0.8))).normalized()
        rr = crown_r * (0.45 + 0.5 * rnd.random() ** 0.5)
        p = crown_c + Vector((d.x * rr, d.y * rr, d.z * rr * 0.72))
        if p.z < z + trunk_h * 0.9:
            continue
        centres.append(p)
    core = bmesh.new()
    cards = bmesh.new()
    uv = cards.loops.layers.uv.verify()
    for p in centres:
        cr = crown_r * rnd.uniform(0.2, 0.32)
        sub = bmesh.new()
        bmesh.ops.create_icosphere(sub, subdivisions=2, radius=cr)
        for vtx in sub.verts:  # lumpy cluster
            n = vtx.co.normalized()
            vtx.co *= 1.0 + 0.22 * math.sin(n.x * 7 + p.x) * math.cos(n.y * 6 + p.y) + rnd.uniform(-0.08, 0.08)
            vtx.co.z *= 0.8
        for vtx in sub.verts:
            co = vtx.co + p
            core.verts.new(vtx.co * 0.8 + p)  # core sits inside the leaf shell
            if rnd.random() > cards_per_vert:
                continue
            for _ in range(2):  # two crossed leaves per sampled vertex
                nrm = (vtx.co.normalized() + Vector((rnd.uniform(-0.7, 0.7), rnd.uniform(-0.7, 0.7), rnd.uniform(-0.3, 0.9)))).normalized()
                side = nrm.cross(Vector((0, 0, 1)))
                if side.length < 1e-3:
                    side = Vector((1, 0, 0))
                side.normalize()
                up = side.cross(nrm).normalized()
                ang = rnd.uniform(0, 2 * math.pi)
                side, up = side * math.cos(ang) + up * math.sin(ang), up * math.cos(ang) - side * math.sin(ang)
                s = leaf_size * rnd.uniform(0.7, 1.25)
                base = co + nrm * rnd.uniform(-0.1, 0.25) * cr
                quad = [base - side * s * 0.3, base + side * s * 0.3, base + side * s * 0.3 + up * s, base - side * s * 0.3 + up * s]
                f = cards.faces.new([cards.verts.new(q) for q in quad])
                for loop, uvc in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
                    loop[uv].uv = uvc
        # rebuild faces of the cluster core in `core`
        base_index = len(core.verts) - len(sub.verts)
        core.verts.ensure_lookup_table()
        sub.verts.index_update()
        for f in sub.faces:
            core.faces.new([core.verts[base_index + v.index] for v in f.verts])
        sub.free()
    ob = K.finish_object(f"{name}_canopy", core, [M["leaves"]], coll, bevel=0, smooth=True)
    ob.scale = (1, 1, 1)
    d = ob.modifiers.new("LeafLumps", "DISPLACE")
    tex = bpy.data.textures.get("KIT_leaf_lumps") or bpy.data.textures.new("KIT_leaf_lumps", "CLOUDS")
    tex.noise_scale = 0.35
    d.texture, d.strength, d.texture_coords, d.mid_level = tex, 0.35, "GLOBAL", 0.5
    me = bpy.data.meshes.new(f"{name}_leaves")
    cards.to_mesh(me)
    cards.free()
    me.materials.append(M["leaf_card"])
    leaves = bpy.data.objects.new(f"{name}_leaves", me)
    coll.objects.link(leaves)
    objs += [ob, leaves]
    return objs


# --------------------------------------------------------------------------- building helpers


def _wall(name, length, height, openings, mats, coll, matrix: Matrix, bevel=0.006):
    """Facade wall: runs along local +X from 0, OUTER face at local y = 0, body toward +Y (WALL_T)."""
    bm = K.wall_bm(length, height, WALL_T, openings)
    bmesh.ops.transform(bm, matrix=matrix, verts=bm.verts)
    return K.finish_object(name, bm, mats, coll, bevel=bevel)


def _window_openings(length, mods, z_floor):
    """(x0, x1, z0, z1) per module index in `mods` for one storey."""
    return [(i * MODULE + 0.3, i * MODULE + 2.7, z_floor + 0.9, z_floor + 2.9) for i in mods]


def _window_set(bm_frame, bm_glass, bm_sill, bm_blind, rnd, x0, x1, z0, z1):
    """Window in the local frame of a facade (outer face y = 0, +Y inward): recessed graphite frame with mullion
    and top-hung vent transom, glass, aluminium sill flashing, optional roller blind."""
    fy0, fy1, fw = RECESS, RECESS + 0.07, 0.06
    mid = (x0 + x1) / 2
    zt = z1 - 0.55
    K.add_box(bm_frame, x0, x1, fy0, fy1, z0, z0 + fw)
    K.add_box(bm_frame, x0, x1, fy0, fy1, z1 - fw, z1)
    K.add_box(bm_frame, x0, x0 + fw, fy0, fy1, z0 + fw, z1 - fw)
    K.add_box(bm_frame, x1 - fw, x1, fy0, fy1, z0 + fw, z1 - fw)
    K.add_box(bm_frame, mid - 0.03, mid + 0.03, fy0, fy1, z0 + fw, z1 - fw)
    K.add_box(bm_frame, x0 + fw, x1 - fw, fy0, fy1, zt - 0.025, zt + 0.025)
    # vent sash frames (slightly proud) in the top lights
    for a, b in ((x0 + fw, mid - 0.03), (mid + 0.03, x1 - fw)):
        K.add_box(bm_frame, a, b, fy0 - 0.012, fy0, zt + 0.025, zt + 0.065)
    gy = RECESS + 0.035
    K.add_box(bm_glass, x0 + fw, x1 - fw, gy - 0.004, gy + 0.004, z0 + fw, z1 - fw)
    K.add_box(bm_sill, x0 - 0.04, x1 + 0.04, -0.05, RECESS + 0.01, z0 - 0.035, z0)
    if bm_blind is not None and rnd.random() < 0.45:
        drop = rnd.choice((0.35, 0.6, 0.9, 1.3))
        K.add_box(bm_blind, x0 + 0.08, x1 - 0.08, RECESS + 0.14, RECESS + 0.15, z1 - 0.05 - drop, z1 - 0.05)


def _interior_shell(coll, M, x0, x1, y_front, depth, rnd):
    """Shallow room shells behind the windows of one facade side (front = −Y): floor, ceiling with lit panels,
    back wall, partitions every 9 m (classroom width = 3 modules)."""
    bm_w, bm_l = bmesh.new(), bmesh.new()
    for f in range(FLOORS):
        zf = GROUND_FLOOR + f * FLOOR_TO_FLOOR
        yb = y_front + depth
        K.add_box(bm_w, x0, x1, y_front, yb, zf - 0.02, zf)  # floor
        K.add_box(bm_w, x0, x1, y_front, yb, zf + 3.2, zf + 3.22)  # ceiling
        K.add_box(bm_w, x0, x1, yb, yb + 0.02, zf, zf + 3.2)  # back (corridor) wall
        x = x0
        while x <= x1 + 1e-6:
            K.add_box(bm_w, x - 0.05, x + 0.05, y_front, yb, zf, zf + 3.2)
            x += 9.0
        for xm in [x0 + 1.5 + MODULE * i for i in range(int((x1 - x0) / MODULE))]:
            if rnd.random() < 0.88:  # a few rooms with lights off
                for yy in (y_front + 1.6, y_front + 4.2):
                    K.add_box(bm_l, xm - 1.1, xm + 1.1, yy - 0.06, yy + 0.06, zf + 3.195, zf + 3.2)
    K.finish_object(f"interior_shell_{y_front:+.0f}", bm_w, [M["interior_wall"]], coll, bevel=0)
    K.finish_object(f"interior_lights_{y_front:+.0f}", bm_l, [M["interior_light"]], coll, bevel=0)


# --------------------------------------------------------------------------- the building


def build_school_building(M, parent):
    c = K.piece_collection(parent, "school_building")
    rnd = random.Random(23)
    X0, X1 = WING_X
    L = X1 - X0
    H = ROOF_Z + PARAPET
    n_mod = int(L / MODULE)
    core_mods = {i for i in range(n_mod) if CORE_X[0] - 1e-6 <= X0 + i * MODULE and X0 + (i + 1) * MODULE <= CORE_X[1] + 1e-6}
    front_mods = [i for i in range(n_mod) if i not in core_mods]

    bm_frame, bm_glass, bm_sill, bm_blind = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()

    def facade(name, origin, rot_z_deg, length, mods_per_floor):
        mat = Matrix.Translation(origin) @ Matrix.Rotation(math.radians(rot_z_deg), 4, "Z")
        openings = []
        for f in range(FLOORS):
            openings += _window_openings(length, mods_per_floor, GROUND_FLOOR + f * FLOOR_TO_FLOOR)
        _wall(name, length, H, openings, [M["render"]], c, mat)
        fr, gl, si, bl = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
        for (x0, x1, z0, z1) in openings:
            _window_set(fr, gl, si, bl, rnd, x0, x1, z0, z1)
        for src, dst in ((fr, bm_frame), (gl, bm_glass), (si, bm_sill), (bl, bm_blind)):
            bmesh.ops.transform(src, matrix=mat, verts=src.verts)
            me = bpy.data.meshes.new("tmp")
            src.to_mesh(me)
            dst.from_mesh(me)
            bpy.data.meshes.remove(me)
            src.free()
        # string courses (thin, slightly proud bands) at each upper floor line + plinth band
        bm = bmesh.new()
        for f in range(1, FLOORS):
            z = GROUND_FLOOR + f * FLOOR_TO_FLOOR - 0.14
            K.add_box(bm, 0, length, -0.025, 0.0, z, z + 0.1)
        K.add_box(bm, 0, length, -0.03, 0.0, ROOF_Z + PARAPET - 0.08, ROOF_Z + PARAPET + 0.0)
        bmesh.ops.transform(bm, matrix=mat, verts=bm.verts)
        K.finish_object(f"{name}_bands", bm, [M["render_band"]], c, bevel=0.004)
        bm = bmesh.new()
        K.add_box(bm, -0.04, length + 0.04, -0.04, 0.0, 0.0, GROUND_FLOOR)
        bmesh.ops.transform(bm, matrix=mat, verts=bm.verts)
        K.finish_object(f"{name}_plinth", bm, [M["plinth"]], c, bevel=0.006)

    # Front (faces −Y): outer face y = 0, runs +X
    facade("facade_front", Vector((X0, 0, 0)), 0, L, front_mods)
    # Back (faces +Y): runs −X from (X1, D)
    facade("facade_back", Vector((X1, WING_DEPTH, 0)), 180, L, list(range(n_mod)))
    # Ends: east end faces +X (runs +Y from (X1, 0)), west end faces −X (runs −Y from (X0, D))
    end_mods = [1, 2, 3]
    facade("facade_east", Vector((X1, 0, 0)), 90, WING_DEPTH, end_mods)
    facade("facade_west", Vector((X0, WING_DEPTH, 0)), -90, WING_DEPTH, end_mods)

    K.finish_object("window_frames", bm_frame, [M["frame"]], c, bevel=0.003)
    g = K.finish_object("window_glass", bm_glass, [M["glass"]], c, bevel=0)
    g.visible_shadow = False
    K.finish_object("window_sills_ext", bm_sill, [M["frame"]], c, bevel=0.002)
    K.finish_object("window_blinds", bm_blind, [M["blind"]], c, bevel=0)

    # Roof slab, parapet coping, a few set-back rooftop units (not visible from the ground)
    bm = bmesh.new()
    K.add_box(bm, X0 + WALL_T, X1 - WALL_T, WALL_T, WING_DEPTH - WALL_T, ROOF_Z - 0.3, ROOF_Z + 0.15)
    K.finish_object("roof", bm, [M["roof"]], c, bevel=0)
    bm = bmesh.new()
    t = 0.04
    K.add_box(bm, X0 - t, X1 + t, -t, WALL_T + t, H, H + 0.05)
    K.add_box(bm, X0 - t, X1 + t, WING_DEPTH - WALL_T - t, WING_DEPTH + t, H, H + 0.05)
    K.add_box(bm, X0 - t, X0 + WALL_T + t, WALL_T + t, WING_DEPTH - WALL_T - t, H, H + 0.05)
    K.add_box(bm, X1 - WALL_T - t, X1 + t, WALL_T + t, WING_DEPTH - WALL_T - t, H, H + 0.05)
    K.finish_object("parapet_coping", bm, [M["frame"]], c, bevel=0.003)
    bm = bmesh.new()
    for x in (-16.0, 13.0):
        K.add_box(bm, x, x + 3.0, 6.0, 9.0, ROOF_Z + 0.15, ROOF_Z + 1.4)
    K.finish_object("roof_units", bm, [M["steel_brushed"]], c, bevel=0.02)

    # Room shells behind the windows
    _interior_shell(c, M, X0 + WALL_T, X1 - WALL_T, WALL_T, 6.0, rnd)
    bm = bmesh.new()  # dark corridor zone in the middle + back rooms read as darker depth
    K.add_box(bm, X0 + WALL_T, X1 - WALL_T, 6.05, WING_DEPTH - WALL_T - 6.0, GROUND_FLOOR, ROOF_Z - 0.3)
    K.finish_object("interior_core", bm, [M["interior_dark"]], c, bevel=0)

    build_entrance_core(c, M, rnd)
    return c


def build_entrance_core(c, M, rnd):
    cx0, cx1 = CORE_X
    fy = CORE_FRONT
    pw = 0.5  # teal portal frame width
    # Teal portal: two posts + head band + side cheeks back to the wing facade
    bm = bmesh.new()
    K.add_box(bm, cx0, cx0 + pw, fy, 0.0, 0.0, CORE_TOP)
    K.add_box(bm, cx1 - pw, cx1, fy, 0.0, 0.0, CORE_TOP)
    K.add_box(bm, cx0 + pw, cx1 - pw, fy, 0.0, CORE_TOP - 1.1, CORE_TOP)
    K.finish_object("core_portal", bm, [M["wall_accent"]], c, bevel=0.01)
    bm = bmesh.new()
    K.add_box(bm, cx0 - 0.03, cx1 + 0.03, fy - 0.03, 0.03, CORE_TOP, CORE_TOP + 0.05)
    K.finish_object("core_coping", bm, [M["frame"]], c, bevel=0.003)
    bm = bmesh.new()  # roof of the core
    K.add_box(bm, cx0 + pw, cx1 - pw, fy + 0.05, 0.3, CORE_TOP - 1.2, CORE_TOP - 1.1)
    K.finish_object("core_roof", bm, [M["roof"]], c, bevel=0)

    # Curtain wall set 0.25 m back inside the portal
    gy = fy + 0.25
    gx0, gx1 = cx0 + pw, cx1 - pw
    gz0, gz1 = GROUND_FLOOR, CORE_TOP - 1.1
    bays = 8
    bw = (gx1 - gx0) / bays
    bm_f, bm_g = bmesh.new(), bmesh.new()
    for i in range(bays + 1):
        x = gx0 + i * bw
        K.add_box(bm_f, x - 0.03, x + 0.03, gy - 0.12, gy, gz0, gz1)  # deep mullions
    levels = [gz0, gz1] + [GROUND_FLOOR + f * FLOOR_TO_FLOOR for f in range(1, FLOORS + 1)]
    levels += [GROUND_FLOOR + f * FLOOR_TO_FLOOR + 2.9 for f in range(FLOORS)]
    for z in sorted(set(levels)):
        K.add_box(bm_f, gx0, gx1, gy - 0.07, gy, z - 0.03, z + 0.03)
    # entrance doors: middle two bays, ground floor, with tall steel pull handles
    dz1 = GROUND_FLOOR + 2.9
    door_x0, door_x1 = gx0 + 3 * bw, gx0 + 5 * bw
    K.add_box(bm_f, (door_x0 + door_x1) / 2 - 0.02, (door_x0 + door_x1) / 2 + 0.02, gy - 0.07, gy, gz0, dz1)
    K.add_box(bm_g, gx0, gx1, gy - 0.004, gy + 0.004, gz0, gz1)
    K.finish_object("core_mullions", bm_f, [M["frame"]], c, bevel=0.003)
    g = K.finish_object("core_glass", bm_g, [M["glass"]], c, bevel=0)
    g.visible_shadow = False
    bm = bmesh.new()
    for xh in ((door_x0 + door_x1) / 2 - 0.12, (door_x0 + door_x1) / 2 + 0.12):
        K.add_cylinder(bm, xh, gy - 0.08, GROUND_FLOOR + 0.8, GROUND_FLOOR + 2.0, 0.016, segments=16)
        for zz in (GROUND_FLOOR + 0.85, GROUND_FLOOR + 1.95):
            K.add_box(bm, xh - 0.01, xh + 0.01, gy - 0.08, gy - 0.004, zz - 0.01, zz + 0.01)
    K.finish_object("core_door_handles", bm, [M["steel_brushed"]], c, bevel=0.002)

    # Behind the glass: lobby/stair hall — floor slabs with oak edges, warm white back wall, lit ceilings,
    # an oak stair flight between levels
    bm_s, bm_e, bm_l = bmesh.new(), bmesh.new(), bmesh.new()
    for f in range(FLOORS + 1):
        z = GROUND_FLOOR + f * FLOOR_TO_FLOOR
        y0 = gy + 0.3 if f else gy + 0.05
        K.add_box(bm_s, gx0, gx1, y0, 0.0, z - 0.35, z)
        if f:
            K.add_box(bm_e, gx0, gx1, y0 - 0.01, y0, z - 0.35, z)
        if f < FLOORS:
            for xl in (gx0 + 1.4, (gx0 + gx1) / 2, gx1 - 1.4):
                zc = z + FLOOR_TO_FLOOR - 0.35  # underside of the slab above
                K.add_cylinder(bm_l, xl, gy + 0.9, zc - 0.012, zc, 0.18, segments=24)
    K.finish_object("core_slabs", bm_s, [M["wall_paint"]], c, bevel=0)
    K.finish_object("core_slab_edges", bm_e, [M["wood_light"]], c, bevel=0)
    K.finish_object("core_lights", bm_l, [M["interior_light"]], c, bevel=0)
    bm = bmesh.new()
    K.add_box(bm, gx0, gx1, -0.02, 0.0, GROUND_FLOOR, gz1)  # back wall (the wing facade behind)
    K.finish_object("core_back_wall", bm, [M["wall_paint"]], c, bevel=0)
    bm = bmesh.new()  # stair flight: rises along +X on the right half, against the back wall
    steps = 22
    for s in range(steps):
        x = gx0 + 5.6 + s * 0.17 - 4.0
        z = GROUND_FLOOR + FLOOR_TO_FLOOR * (s + 1) / steps
        K.add_box(bm, x, x + 0.3, -1.25, -0.05, z - 0.04, z)
    K.finish_object("core_stair", bm, [M["wood_light"]], c, bevel=0.004)
    bm = bmesh.new()
    K.add_box(bm, gx0 + 1.6, gx0 + 1.6 + steps * 0.17 + 0.3, -1.3, -1.25, GROUND_FLOOR + 0.9,
              GROUND_FLOOR + 0.9 + FLOOR_TO_FLOOR)
    K.finish_object("core_stair_glass", bm, [M["glass"]], c, bevel=0)

    # Cantilevered canopy over the entrance: graphite fascia, oak soffit with recessed downlights
    ky0, ky1, kz = fy - 5.5, fy, GROUND_FLOOR + 3.4
    kx0, kx1 = cx0 - 1.0, cx1 + 1.0
    bm = bmesh.new()
    K.add_box(bm, kx0, kx1, ky0, ky1, kz + 0.05, kz + 0.38)
    K.finish_object("canopy_body", bm, [M["frame"]], c, bevel=0.006)
    bm = bmesh.new()
    K.add_box(bm, kx0 + 0.06, kx1 - 0.06, ky0 + 0.06, ky1, kz, kz + 0.05)
    K.finish_object("canopy_soffit", bm, [M["wood_light"]], c, bevel=0.002)
    bm = bmesh.new()
    for xi in range(5):
        for yi in range(2):
            K.add_cylinder(bm, kx0 + 1.6 + xi * (kx1 - kx0 - 3.2) / 4, ky0 + 1.4 + yi * 2.6, kz - 0.004, kz, 0.08, segments=20)
    K.finish_object("canopy_downlights", bm, [M["soffit_light"]], c, bevel=0)

    # Entrance platform, three steps, ramp with handrails on the east side
    bm = bmesh.new()
    K.add_box(bm, kx0, kx1, ky0, fy + 0.3, 0.0, GROUND_FLOOR)
    for s in range(3):
        h = GROUND_FLOOR * (2 - s) / 3
        K.add_box(bm, kx0 + 1.5, kx1 - 1.5, ky0 - 0.35 * (s + 1), ky0 - 0.35 * s, 0.0, h)
    rx0, rx1 = kx1, kx1 + 7.0  # ramp 1:15
    rw0, rw1 = ky0, ky0 + 1.6
    K.finish_object("entrance_platform", bm, [M["plinth"]], c, bevel=0.01)
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in ((rx0, rw0, 0), (rx1, rw0, 0), (rx1, rw1, 0), (rx0, rw1, 0),
                                    (rx0, rw0, GROUND_FLOOR), (rx1, rw0, 0.001), (rx1, rw1, 0.001), (rx0, rw1, GROUND_FLOOR))]
    for idx in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (3, 0, 4, 7)):
        bm.faces.new([vs[i] for i in idx])
    K.finish_object("entrance_ramp", bm, [M["plinth"]], c, bevel=0.004)
    rails = []
    for yy in (rw0 + 0.05, rw1 - 0.05):
        rails.append([(rx1 + 0.3, yy, 0.9), (rx1, yy, 0.9), (rx0, yy, GROUND_FLOOR + 0.9), (rx0 - 0.3, yy, GROUND_FLOOR + 0.9)])
        for k in range(5):
            x = rx0 + (rx1 - rx0) * k / 4
            zb = GROUND_FLOOR * (1 - k / 4)
            rails.append([(x, yy, zb), (x, yy, zb + 0.9)])
    K.tube("ramp_handrails", rails, 0.022, M["steel_brushed"], c, fillet=0.05)


# --------------------------------------------------------------------------- grounds


def build_school_grounds(M, parent):
    c = K.piece_collection(parent, "school_grounds")
    rnd = random.Random(41)
    # Ground: big paved forecourt, lawn beyond the forecourt edges
    bm = bmesh.new()
    K.add_box(bm, -140, 140, -140, 160, -0.30, -0.06)
    K.finish_object("grounds_lawn_base", bm, [M["grass_artificial"]], c, bevel=0)
    bm = bmesh.new()
    K.add_box(bm, -32, 32, -36, -0.04, -0.30, 0.0)  # forecourt
    K.add_box(bm, -32, 32, -0.04, 18.0, -0.30, 0.0)  # paving around the building
    K.add_box(bm, -6, 6, -70, -36, -0.30, 0.0)  # entrance path toward the street
    K.finish_object("grounds_paving", bm, [M["paving_slab"]], c, bevel=0)
    bm = bmesh.new()  # darker granite bands across the forecourt every 6 m + tree pits with graphite grates
    for k in range(1, 6):
        y = -k * 6.0
        K.add_box(bm, -32, 32, y - 0.15, y + 0.15, -0.30, 0.002)
    K.add_box(bm, -0.6, 0.6, -70, -7.6, -0.30, 0.002)  # axis band up the entrance path
    K.finish_object("grounds_paving_bands", bm, [M["plinth"]], c, bevel=0)
    bm = bmesh.new()
    for tx in (-21.0, 21.0):
        K.add_box(bm, tx - 0.8, tx + 0.8, -30.8, -29.2, -0.30, 0.004)
    K.finish_object("grounds_tree_grates", bm, [M["frame"]], c, bevel=0)
    bm = bmesh.new()  # kerbs around the forecourt lawns and planting beds
    beds = [(-28, -12, -22, -8), (12, 28, -22, -8)]  # lawn islands in the forecourt
    for x0, x1, y0, y1 in beds:
        K.add_box(bm, x0 - 0.15, x1 + 0.15, y0 - 0.15, y0, 0.0, 0.12)
        K.add_box(bm, x0 - 0.15, x1 + 0.15, y1, y1 + 0.15, 0.0, 0.12)
        K.add_box(bm, x0 - 0.15, x0, y0, y1, 0.0, 0.12)
        K.add_box(bm, x1, x1 + 0.15, y0, y1, 0.0, 0.12)
    K.finish_object("grounds_kerbs", bm, [M["kerb"]], c, bevel=0.01)
    bm = bmesh.new()
    for x0, x1, y0, y1 in beds:
        K.add_box(bm, x0, x1, y0, y1, -0.1, 0.08)
    K.finish_object("grounds_lawn_islands", bm, [M["grass_artificial"]], c, bevel=0)

    # Planting strip along the facade (between the windows and the paving), low clipped shrubs
    bm = bmesh.new()
    for x0, x1 in ((-23.5, -8.5), (8.5, 23.5)):
        K.add_box(bm, x0, x1, -1.6, -0.05, 0.0, 0.4)
    K.finish_object("planter_walls", bm, [M["kerb"]], c, bevel=0.01)
    bm = bmesh.new()
    for x0, x1 in ((-23.5, -8.5), (8.5, 23.5)):
        K.add_box(bm, x0 + 0.12, x1 - 0.12, -1.48, -0.17, 0.0, 0.36)
    K.finish_object("planter_soil", bm, [M["soil"]], c, bevel=0)
    shrubs = bmesh.new()
    for x0, x1 in ((-23.2, -8.8), (8.8, 23.2)):
        x = x0
        while x < x1:
            r = rnd.uniform(0.35, 0.5)
            sub = bmesh.new()
            bmesh.ops.create_icosphere(sub, subdivisions=2, radius=r)
            for v in sub.verts:
                v.co.z *= 0.75
                v.co *= 1 + rnd.uniform(-0.1, 0.1)
            bmesh.ops.translate(sub, verts=sub.verts, vec=(x + r, -0.82 + rnd.uniform(-0.1, 0.1), 0.36 + r * 0.55))
            me = bpy.data.meshes.new("tmp")
            sub.to_mesh(me)
            shrubs.from_mesh(me)
            bpy.data.meshes.remove(me)
            sub.free()
            x += r * 1.5
    sh = K.finish_object("planter_shrubs", shrubs, [M["leaves"]], c, bevel=0, smooth=True)
    d = sh.modifiers.new("Lumps", "DISPLACE")
    tex = bpy.data.textures.get("KIT_leaf_lumps") or bpy.data.textures.new("KIT_leaf_lumps", "CLOUDS")
    d.texture, d.strength, d.texture_coords = tex, 0.12, "GLOBAL"

    # Benches (oak slats on concrete blocks) facing the forecourt lawns, bollard lights along the path
    bm_b, bm_w = bmesh.new(), bmesh.new()
    for bx, by in ((-20, -7.2), (-14, -7.2), (14, -7.2), (20, -7.2)):
        for dx in (-0.8, 0.8):
            K.add_box(bm_b, bx + dx - 0.12, bx + dx + 0.12, by - 0.22, by + 0.22, 0.0, 0.42)
        for k in range(5):
            yy = by - 0.22 + k * 0.095
            K.add_box(bm_w, bx - 1.0, bx + 1.0, yy, yy + 0.075, 0.42, 0.46)
    K.finish_object("bench_blocks", bm_b, [M["kerb"]], c, bevel=0.01)
    K.finish_object("bench_slats", bm_w, [M["wood_light"]], c, bevel=0.004)
    bm, bm_e = bmesh.new(), bmesh.new()
    for y in (-40, -48, -56, -64):
        for x in (-6.6, 6.6):
            K.add_cylinder(bm, x, y, 0.0, 0.9, 0.07, segments=20)
            K.add_cylinder(bm_e, x, y, 0.72, 0.8, 0.072, segments=20)
    for x in (-9.0, -3.0, 3.0, 9.0):
        K.add_cylinder(bm, x, -12.0, 0.0, 0.9, 0.07, segments=20)
        K.add_cylinder(bm_e, x, -12.0, 0.72, 0.8, 0.072, segments=20)
    K.finish_object("bollards", bm, [M["frame"]], c, bevel=0.004)
    K.finish_object("bollard_lenses", bm_e, [M["soffit_light"]], c, bevel=0)

    # Trees: forecourt pairs, rows beside the building, a taller background row behind it
    spots = [(-24, -19, 7.5), (-16, -15, 6.5), (16, -15, 6.8), (24, -19, 7.8), (-21, -30, 8.6), (21, -30, 8.9),
             (-30, -4, 8.5), (30, -4, 8.2), (-36, 8, 9.0), (36, 9, 9.5),
             (-9, -40, 7.0), (9, -44, 7.2)]
    for k in range(9):
        spots.append((-40 + k * 10 + rnd.uniform(-2, 2), 25 + rnd.uniform(-2, 4), rnd.uniform(14.0, 17.0)))
    for i, (x, y, h) in enumerate(spots):
        make_tree(f"tree_{i:02d}", (x, y, 0.0), c, M, rnd, height=h, crown_r=h * 0.36,
                  clusters=int(40 + h * 2.5), leaf_size=0.26 + h * 0.014)
    build_distant_trees(c, M, rnd)
    return c


def build_distant_trees(c, M, rnd):
    """Tree belt 60–120 m out (behind and beside the school) so the horizon is never an empty line.
    Lighter trees: fewer leaf cards — they are small and soft in frame."""
    k = 0
    for i in range(46):
        a = math.radians(-60 + i * (300 / 45) + rnd.uniform(-2, 2))  # arc from front-right, behind, to front-left
        r = rnd.uniform(62, 115)
        x, y = math.cos(a) * r, math.sin(a) * r + 8.0
        if y < -45 or abs(x) < 30 and y < 0:  # keep the street approach open
            continue
        h = rnd.uniform(11, 18)
        make_tree(f"far_tree_{k:02d}", (x, y, 0.0), c, M, rnd, height=h, crown_r=h * 0.4, clusters=int(22 + h),
                  cards_per_vert=0.25, leaf_size=0.5)
        k += 1
