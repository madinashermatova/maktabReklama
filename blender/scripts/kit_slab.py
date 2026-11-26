"""Kit piece PIECE_slab — the shared floor slab for the S transition (docs/storyboard.md → "S — Floor-slab pass").

Imported by build_kit.py (do not run directly).

Geometry (piece origin = top of the upper room's finished floor, centred on the camera shaft):
    x, y ∈ [−3, 3]; z from −0.02 (just under the scene's own floor finish, PIECE_floor_area) to −1.20.
      top deck      −0.02 … −0.15   concrete
      cavity        −0.15 … −1.05   0.9 m void: downstand ribs, cable trays + cables, round duct,
                                     warm-white 4000 K LED strips under the top deck
      bottom deck   −1.05 … −1.20   concrete; its underside is the lower room's plenum top
                                     (lower room ceiling panel at −1.20 − 0.30 = −1.50)
    slab_HANDOFF empty at (0, 0, −0.61) = slab midpoint = the cut. Image "up" = +Y. The column above
    and below (0, 0) is kept free of geometry except the two decks the camera passes through.

Lighting: only the slab's own LED strips (light data KIT_slab_led, fixed 4000 K — NOT driven by the lighting
presets), so the cut frame is identical in every scene. Scenes add an irradiance volume inside the cavity with
_common.add_slab_probe() so world light cannot leak in.
"""

from __future__ import annotations

import math
import random

import bmesh
import bpy
from mathutils import Matrix

import _common as C
import build_kit as K

SLAB_TOP = -0.02
DECK_TOP_BOTTOM = -0.15
CAVITY_FLOOR = -1.05
SLAB_BOTTOM = -1.20
HALF = 3.0
LED_KELVIN = 4000
LED_WATTS = 6.0


def slab_materials():
    M = {}
    # Board-formed concrete: faint 1.2 × 0.15 m board marks + tie holes, light warm grey
    m, nt, b = K.new_material("KIT_slab_concrete")
    base = C.hex_rgba("#A7A39C")
    vec = K.uv_vec(nt)
    n1 = K.noise(nt, vec, 1.8, 10.0, 0.62)
    col = K.ramp(nt, n1.outputs["Fac"], [(0.32, K.shade(base, 0.82)), (0.5, base), (0.7, K.shade(base, 1.08))])
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.offset, br.offset_frequency = 0.0, 1
    for k, v in (("Scale", 1.0), ("Brick Width", 1.2), ("Row Height", 0.15), ("Mortar Size", 0.002),
                 ("Color1", (1, 1, 1, 1)), ("Color2", (0.95, 0.95, 0.95, 1)), ("Mortar", (0.78, 0.78, 0.78, 1))):
        K._sock(br, k, v)

    nt.links.new(vec, br.inputs["Vector"])
    col = K.mix_color(nt, col, br.outputs["Color"], 1.0, "MULTIPLY")
    nt.links.new(col, b.inputs["Base Color"])
    n2 = K.noise(nt, vec, 80.0, 4.0, 0.6)
    nt.links.new(K.map_range(nt, n2.outputs["Fac"], 0.72, 0.9), b.inputs["Roughness"])
    K.bump(nt, b, n2.outputs["Fac"], 0.12, 0.004)
    M["concrete"] = m
    M["galv"] = K.mat_metal("KIT_galvanised", "#A9AEB2", 0.36, brushed=True)
    M["cable_grey"] = K.mat_simple("KIT_cable_grey", "#7D8084", rough=0.45)
    M["cable_black"] = K.mat_simple("KIT_cable_black", "#1D1E20", rough=0.4)
    M["cable_white"] = K.mat_simple("KIT_cable_white", "#E6E4DE", rough=0.45)
    M["cable_amber"] = K.mat_simple("KIT_cable_amber", "#E3A33B", rough=0.45)
    M["led_emit"] = K.mat_emit("KIT_slab_led_emit", LED_KELVIN, 14.0)
    M["led_body"] = bpy.data.materials["KIT_steel_brushed"]
    M["tie"] = K.mat_simple("KIT_tie_hole", "#4C4A47", rough=0.8)
    return M


def build_slab(parent):
    M = slab_materials()
    c = K.piece_collection(parent, "slab")
    rnd = random.Random(11)
    H = HALF

    # Shell: decks + closed side walls (0.15 m) → a sealed cavity
    bm = bmesh.new()
    K.add_box(bm, -H, H, -H, H, DECK_TOP_BOTTOM, SLAB_TOP)
    K.add_box(bm, -H, H, -H, H, SLAB_BOTTOM, CAVITY_FLOOR)
    for x0, x1, y0, y1 in ((-H, -H + 0.15, -H, H), (H - 0.15, H, -H, H), (-H + 0.15, H - 0.15, -H, -H + 0.15),
                           (-H + 0.15, H - 0.15, H - 0.15, H)):
        K.add_box(bm, x0, x1, y0, y1, CAVITY_FLOOR, DECK_TOP_BOTTOM)
    # Downstand ribs (beams) along Y at x = ±1.5, 0.30 deep under the top deck
    for x in (-1.5, 1.5):
        K.add_box(bm, x - 0.15, x + 0.15, -H + 0.15, H - 0.15, DECK_TOP_BOTTOM - 0.30, DECK_TOP_BOTTOM)
    K.finish_object("slab_shell", bm, [M["concrete"]], c, bevel=0.01, segments=2)

    # Formwork tie holes on the cavity floor (small dark discs, 0.6 m grid)
    bm = bmesh.new()
    for i in range(-4, 5):
        for j in range(-4, 5):
            K.add_cylinder(bm, i * 0.6 + 0.3, j * 0.6 + 0.3, CAVITY_FLOOR, CAVITY_FLOOR + 0.0015, 0.012, segments=12)
    K.finish_object("slab_tie_holes", bm, [M["tie"]], c, bevel=0)

    # Cable trays on low supports, running along Y. Tray A beside the shaft (x −0.42…−0.10), tray B at x +0.30…+0.52.
    def tray(name, x0, x1, z0, bundles):
        bm = bmesh.new()
        L = H - 0.2
        K.add_box(bm, x0, x1, -L, L, z0, z0 + 0.004)  # base
        for xs in (x0, x1 - 0.004):  # side rails 60 mm
            K.add_box(bm, xs, xs + 0.004, -L, L, z0, z0 + 0.06)
        for yy in [k * 0.5 for k in range(-5, 6)]:  # supports + cross rungs
            K.add_box(bm, x0 - 0.02, x1 + 0.02, yy - 0.02, yy + 0.02, CAVITY_FLOOR, CAVITY_FLOOR + 0.008)
            for xs in (x0 - 0.012, x1 + 0.004):
                K.add_box(bm, xs, xs + 0.008, yy - 0.015, yy + 0.015, CAVITY_FLOOR, z0 + 0.03)
        K.finish_object(f"slab_tray_{name}", bm, [M["galv"]], c, bevel=0.0015)
        # cables: slightly wavy tubes lying in the tray
        for mat_key, count, r in bundles:
            polys = []
            for _ in range(count):
                cx = rnd.uniform(x0 + r + 0.008, x1 - r - 0.008)
                cz = z0 + 0.004 + r + rnd.uniform(0, 0.02)
                pts = []
                for k in range(13):
                    y = -L + 2 * L * k / 12
                    pts.append((cx + 0.006 * math.sin(k * 1.3 + cx * 40), y, cz))
                polys.append(pts)
            K.tube(f"slab_cables_{name}_{mat_key}", polys, r, M[mat_key], c, fillet=0.0)

    tray("A", -0.42, -0.10, CAVITY_FLOOR + 0.10,
         [("cable_grey", 7, 0.009), ("cable_black", 5, 0.011), ("cable_white", 3, 0.006)])
    tray("B", 0.30, 0.52, CAVITY_FLOOR + 0.10, [("cable_black", 4, 0.013), ("cable_amber", 2, 0.008)])

    # Round galvanised duct along X near the top, off the shaft (y = +1.1), with hangers
    bm = bmesh.new()
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=40, radius1=0.16, radius2=0.16, depth=2 * H - 0.3)
    bmesh.ops.rotate(bm, verts=res["verts"], cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "Y"))
    bmesh.ops.translate(bm, verts=res["verts"], vec=(0, 1.1, -0.62))
    for f in bm.faces:
        f.smooth = len(f.verts) == 4
    for x in (-2.2, -0.6, 0.9, 2.2):  # duct bands + hanger rods
        b2 = bmesh.ops.create_cone(bm, cap_ends=True, segments=40, radius1=0.166, radius2=0.166, depth=0.03)
        bmesh.ops.rotate(bm, verts=b2["verts"], cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "Y"))
        bmesh.ops.translate(bm, verts=b2["verts"], vec=(x, 1.1, -0.62))
        K.add_box(bm, x - 0.006, x + 0.006, 1.094, 1.106, -0.46, DECK_TOP_BOTTOM)
    K.finish_object("slab_duct", bm, [M["galv"]], c, bevel=0)

    # Warm-white LED strips under the top deck along Y (x = ±0.75) and on the rib faces → the only light here
    bm = bmesh.new()
    for x in (-0.75, 0.75):
        K.add_box(bm, x - 0.012, x + 0.012, -H + 0.3, H - 0.3, DECK_TOP_BOTTOM - 0.012, DECK_TOP_BOTTOM, mat_index=0)
        K.add_box(bm, x - 0.009, x + 0.009, -H + 0.31, H - 0.31, DECK_TOP_BOTTOM - 0.014, DECK_TOP_BOTTOM - 0.012,
                  mat_index=1)
    K.finish_object("slab_led_channels", bm, [M["led_body"], M["led_emit"]], c, bevel=0.001)
    led = bpy.data.lights.new("KIT_slab_led", "AREA")
    led.shape, led.size, led.size_y = "RECTANGLE", 0.018, 2 * H - 0.62
    led.energy, led.use_temperature, led.temperature = LED_WATTS * (2 * H - 0.62), True, LED_KELVIN
    led.use_shadow = True
    for i, x in enumerate((-0.75, 0.75)):
        ob = bpy.data.objects.new(f"slab_led_{i}", led)
        ob.location = (x, 0, DECK_TOP_BOTTOM - 0.016)
        c.objects.link(ob)

    hand = bpy.data.objects.new("slab_HANDOFF", None)
    hand.empty_display_type = "SINGLE_ARROW"
    hand.empty_display_size = 0.3
    hand.location = (0, 0, (SLAB_TOP + SLAB_BOTTOM) / 2)  # −0.61 = slab midpoint
    hand.rotation_euler = (0, 0, 0)
    c.objects.link(hand)
    c["handoff_local"] = list(hand.location)
    c["cavity"] = [-H + 0.15, H - 0.15, -H + 0.15, H - 0.15, CAVITY_FLOOR, DECK_TOP_BOTTOM]
    return c
