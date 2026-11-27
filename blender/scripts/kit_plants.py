"""Realistic potted palms (areca-like clumps), modelled procedurally — shared by scenes that need potted plants.

    import kit_plants as KP
    mats = KP.palm_materials()
    KP.potted_palm("palm_0", (x, y, soil_z), coll, mats, random.Random(1), height=1.8, spread=1.1)

Each plant: 3–5 canes rising from the soil; every cane carries 2–4 pinnate fronds. A frond is a tapered petiole/rachis
that rises steeply and arches over under its own weight; along it sit two ranks of narrow lanceolate leaflets, held
in a shallow V, folded along the midrib, drooping more toward the frond tip. Leaflet length follows a natural profile
(short at the base and tip, longest at ~40 %), every leaflet has its own twist/droop/colour, a few tips are dry.
Per-vertex attributes for the material: `leafvar` (0..1, per leaflet colour variation) and `leafpos` (0 base → 1 tip).
No alpha cards: real geometry, so close-ups hold up.
"""

from __future__ import annotations

import math

import bmesh
import bpy
from mathutils import Matrix, Vector

import _common as C


def palm_materials():
    """Leaf (green variation + dry tips, slight translucency for backlight) and stem/soil materials."""
    m = bpy.data.materials.get("PLANT_palm_leaf") or bpy.data.materials.new("PLANT_palm_leaf")
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    var = nt.nodes.new("ShaderNodeAttribute")
    var.attribute_name = "leafvar"
    pos = nt.nodes.new("ShaderNodeAttribute")
    pos.attribute_name = "leafpos"
    rmp = nt.nodes.new("ShaderNodeValToRGB")
    els = rmp.color_ramp.elements
    els[0].position, els[0].color = 0.0, C.hex_rgba("#294A1E")
    els[1].position, els[1].color = 1.0, C.hex_rgba("#6E8F3C")
    e = els.new(0.55)
    e.color = C.hex_rgba("#3F6A2A")
    nt.links.new(var.outputs["Fac"], rmp.inputs["Fac"])
    # dry tips: only leaflets with leafvar > 0.86, only the last ~12 % of the leaflet
    dry_sel = nt.nodes.new("ShaderNodeMath")
    dry_sel.operation = "GREATER_THAN"
    dry_sel.inputs[1].default_value = 0.86
    nt.links.new(var.outputs["Fac"], dry_sel.inputs[0])
    tip = nt.nodes.new("ShaderNodeMapRange")
    tip.inputs["From Min"].default_value = 0.84
    tip.inputs["From Max"].default_value = 0.97
    nt.links.new(pos.outputs["Fac"], tip.inputs["Value"])
    dry = nt.nodes.new("ShaderNodeMath")
    dry.operation = "MULTIPLY"
    nt.links.new(dry_sel.outputs[0], dry.inputs[0])
    nt.links.new(tip.outputs["Result"], dry.inputs[1])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    nt.links.new(dry.outputs[0], mix.inputs["Factor"])
    nt.links.new(rmp.outputs["Color"], mix.inputs["A"])
    mix.inputs["B"].default_value = C.hex_rgba("#9A8752")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.42
    trans = nt.nodes.new("ShaderNodeBsdfTranslucent")
    nt.links.new(mix.outputs["Result"], trans.inputs["Color"])
    ms = nt.nodes.new("ShaderNodeMixShader")
    ms.inputs["Fac"].default_value = 0.22
    nt.links.new(bsdf.outputs[0], ms.inputs[1])
    nt.links.new(trans.outputs[0], ms.inputs[2])
    nt.links.new(ms.outputs[0], out.inputs["Surface"])
    m.use_backface_culling = False

    stem = bpy.data.materials.get("PLANT_palm_stem") or bpy.data.materials.new("PLANT_palm_stem")
    snt = stem.node_tree
    sb = next(n for n in snt.nodes if n.type == "BSDF_PRINCIPLED")
    sb.inputs["Base Color"].default_value = C.hex_rgba("#5E6E34")
    sb.inputs["Roughness"].default_value = 0.5
    soil = bpy.data.materials.get("PLANT_soil") or bpy.data.materials.new("PLANT_soil")
    sob = next(n for n in soil.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    sob.inputs["Base Color"].default_value = C.hex_rgba("#2B2119")
    sob.inputs["Roughness"].default_value = 0.95
    return {"leaf": m, "stem": stem, "soil": soil}


def _sweep(bm, pts, r0, r1, sides=7):
    """Tapered tube along a polyline (stem / cane)."""
    rings = []
    n = len(pts)
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
        a = t.orthogonal().normalized()
        b = t.cross(a)
        r = r0 + (r1 - r0) * i / (n - 1)
        rings.append([bm.verts.new(p + (a * math.cos(k * 2 * math.pi / sides) + b * math.sin(k * 2 * math.pi / sides)) * r)
                      for k in range(sides)])
    for ra, rb in zip(rings, rings[1:]):
        for k in range(sides):
            bm.faces.new((ra[k], ra[(k + 1) % sides], rb[(k + 1) % sides], rb[k]))


def _frond(bm_leaf, lay_var, lay_pos, bm_stem, base, azim, elev, length, rnd, leaflet_len, droop_bias):
    """One pinnate frond. Rachis integrated in steps: it starts at `elev` and bends down with arc length."""
    steps = 26
    ds = length / steps
    bend = math.radians(rnd.uniform(95, 130)) / length  # total downward bend over the frond
    pts, tans = [base.copy()], []
    p = base.copy()
    for i in range(steps):
        e = elev - bend * (i + 0.5) * ds
        t = Vector((math.cos(azim) * math.cos(e), math.sin(azim) * math.cos(e), math.sin(e)))
        tans.append(t)
        p = p + t * ds
        pts.append(p.copy())
    tans.append(tans[-1])
    _sweep(bm_stem, pts, 0.011, 0.0025)

    s_start = rnd.uniform(0.22, 0.3)  # bare petiole
    n_side = rnd.randint(28, 36)
    seg = 7
    for side in (-1, 1):
        for j in range(n_side):
            u = (j + (0.5 if side > 0 else 0.0)) / n_side  # the two ranks are offset (alternate)
            s = s_start + (0.985 - s_start) * u
            fi = s * steps
            i0 = min(int(fi), steps - 1)
            q = pts[i0].lerp(pts[i0 + 1], fi - i0)
            tg = tans[i0]
            sd = tg.cross(Vector((0, 0, 1)))
            if sd.length < 1e-4:
                sd = Vector((1, 0, 0))
            sd = sd.normalized() * side
            nrm = sd.cross(tg).normalized() * side  # frond "up"
            prof = math.sin(math.pi * min(1.0, 0.08 + u * 0.95)) ** 0.75
            ln = leaflet_len * (0.3 + 0.7 * prof) * rnd.uniform(0.86, 1.1)
            wd = ln * rnd.uniform(0.07, 0.09)
            fwd = math.radians(rnd.uniform(38, 52))  # leaflets point forward along the rachis
            vlift = rnd.uniform(0.18, 0.32)  # shallow V
            d0 = (sd * math.cos(fwd) + tg * math.sin(fwd) + nrm * vlift).normalized()
            droop = (droop_bias + 0.9 * u) * rnd.uniform(0.75, 1.2)  # radians of curl down over the leaflet
            twist = rnd.uniform(-0.25, 0.25)
            fold = rnd.uniform(0.18, 0.32)
            var = rnd.random()
            rows = []
            c = q.copy()
            dvec = d0.copy()
            for k in range(seg + 1):
                v = k / seg
                if k:
                    # curl downward gradually (gravity), rotate about the horizontal axis normal to the leaflet
                    ax = dvec.cross(Vector((0, 0, -1)))
                    if ax.length > 1e-5:
                        dvec = (Matrix.Rotation(droop / seg * (0.4 + 1.2 * v), 3, ax.normalized()) @ dvec).normalized()
                    c = c + dvec * (ln / seg)
                w = wd * (math.sin(math.pi * min(1.0, 0.12 + v)) ** 0.6) * (1 - v) ** 0.35  # lanceolate, pointed tip
                lat = dvec.cross(nrm)
                if lat.length < 1e-5:
                    lat = sd.copy()
                lat = (Matrix.Rotation(twist * v, 3, dvec) @ lat.normalized())
                up = lat.cross(dvec).normalized()
                if up.z < 0:
                    up = -up
                row = []
                for h in (-1, 0, 1):  # edge, midrib, edge
                    pt = c + lat * (h * w / 2) + up * (fold * w * (1 - abs(h)) * 0.6)
                    vt = bm_leaf.verts.new(pt)
                    vt[lay_var] = var
                    vt[lay_pos] = v
                    row.append(vt)
                rows.append(row)
            for ra, rb in zip(rows, rows[1:]):
                for h in range(2):
                    bm_leaf.faces.new((ra[h], ra[h + 1], rb[h + 1], rb[h]))


def potted_palm(name, soil_center, coll, mats, rnd, height=1.8, spread=1.15, canes=None, soil_radius=0.29,
                avoid_dir=None):
    """Build one potted palm clump on `soil_center` (the soil surface in the pot). Returns the leaf object.
    `avoid_dir`: optional (x, y) direction to keep fronds short on (e.g. toward a camera path)."""
    soil_center = Vector(soil_center)
    bm_leaf, bm_stem = bmesh.new(), bmesh.new()
    lay_var = bm_leaf.verts.layers.float.new("leafvar")
    lay_pos = bm_leaf.verts.layers.float.new("leafpos")
    n_canes = canes or rnd.randint(3, 5)
    for ci in range(n_canes):
        ca = rnd.uniform(0, 2 * math.pi)
        off = Vector((math.cos(ca), math.sin(ca), 0)) * rnd.uniform(0.02, 0.1)
        ch = rnd.uniform(0.08, 0.38) * height / 1.8
        lean = Vector((off.x, off.y, 0)) * 0.6
        c0 = soil_center + off
        c1 = c0 + Vector((0, 0, ch)) + lean * ch
        _sweep(bm_stem, [c0, c0.lerp(c1, 0.5), c1], 0.022, 0.016, sides=9)
        for _ in range(rnd.randint(2, 4)):
            az = rnd.uniform(0, 2 * math.pi)
            el = math.radians(rnd.uniform(52, 80))
            ln = spread * rnd.uniform(0.8, 1.12) * (1.0 + 0.25 * (math.sin(el) - 0.85))
            if avoid_dir is not None:
                ad = math.atan2(avoid_dir[1], avoid_dir[0])
                da = abs((az - ad + math.pi) % (2 * math.pi) - math.pi)
                if da < math.radians(55):
                    ln *= 0.62 + 0.38 * da / math.radians(55)
            _frond(bm_leaf, lay_var, lay_pos, bm_stem, c1, az, el, ln, rnd, leaflet_len=rnd.uniform(0.27, 0.34),
                   droop_bias=rnd.uniform(0.15, 0.45))
    me = bpy.data.meshes.new(f"{name}_leaves")
    bm_leaf.to_mesh(me)
    bm_leaf.free()
    me.materials.append(mats["leaf"])
    for poly in me.polygons:
        poly.use_smooth = True
    leaves = bpy.data.objects.new(f"{name}_leaves", me)
    coll.objects.link(leaves)
    bmesh.ops.recalc_face_normals(bm_stem, faces=bm_stem.faces)
    ms = bpy.data.meshes.new(f"{name}_stems")
    bm_stem.to_mesh(ms)
    bm_stem.free()
    ms.materials.append(mats["stem"])
    for poly in ms.polygons:
        poly.use_smooth = True
    st = bpy.data.objects.new(f"{name}_stems", ms)
    coll.objects.link(st)
    bm = bmesh.new()  # soil surface with a slightly domed top
    res = bmesh.ops.create_circle(bm, cap_ends=True, segments=32, radius=soil_radius)
    bmesh.ops.translate(bm, verts=res["verts"], vec=soil_center)
    ms2 = bpy.data.meshes.new(f"{name}_soil")
    bm.to_mesh(ms2)
    bm.free()
    ms2.materials.append(mats["soil"])
    so = bpy.data.objects.new(f"{name}_soil", ms2)
    coll.objects.link(so)
    return leaves
