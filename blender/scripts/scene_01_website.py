"""Scene 1 — "Digital website universe" (film frames 0–269) → blender/scenes/s01_website.blend

    "C:\\Program Files\\Blender Foundation\\Blender 5.3\\blender.exe" -b --python blender/scripts/scene_01_website.py

Inputs (build them first):
  blender/kit/textures/website_strip.png   7 pages stacked top → bottom (npm run website:render + tools/build_website_strip.py)
  renders/_website/school_seq/####.png     school page, film frames S01_BEATS.scrollStop … 269 (npm run website:render):
                                           hover, click + ripple, UI fade → the bare approved hero photo
  blender/timeline.json                    S01 beats + s01PhotoScale per frame (from src/timeline.ts)

Shot: a large floating display in a dark hazy void, tilted diagonally (top edge rising to the right). The website
strip is a real plane moving behind the glass (shader-masked by the screen rectangle, so EEVEE motion blur sees real
motion). Scroll: slow start → very fast (strong blur) → smooth landing exactly on the school website at scrollStop.
Cursor, click and ripple are in the school sequence texture. The camera settles at the click, then dives square-on
into the screen; its distance follows s01PhotoScale(frame) exactly, so the photo on the screen has the same size the
Remotion exact-photo overlay (src/components/S01ExitPhoto.tsx, 252–269) and scene 2's first frame expect (D hand-off).

Colour management: Standard (not AgX) in this scene only — the screen is an emitter at strength 1, so its pixels
reproduce the Remotion page/photo exactly (needed for the invisible D hand-off). The void is dark, so nothing clips.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Euler, Matrix, Quaternion, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as C  # noqa: E402

SCENE_ID = "s01_website"
TL = C.load_timeline()
B = TL["s01"]["beats"]
PHOTO_SCALE = TL["s01"]["photoScale"]  # index = film frame (scene 1 starts at 0)
S1 = C.get_scene_def(SCENE_ID)
F_START, F_END = S1["from"], S1["end"]

STRIP_PNG = C.KIT_DIR / "textures" / "website_strip.png"
SEQ_DIR = C.RENDERS_DIR / "_website" / "school_seq"
STRIP_PAGES = 7  # pages in the atlas (school last)
GENERIC = 6
BLUR_TAPS = 16
CYCLES = 3  # the 6 generic pages pass 3× before the school page → long, fast scroll (strong blur)
N_PAGES = GENERIC * CYCLES + 1  # school page index = N_PAGES − 1

# Display (metres). Screen 16:9.
W, H = 2.4, 1.35
BEZEL = 0.045  # black border under the glass
RIM = 0.012  # metal rim beyond the border
DEPTH = 0.04
ROLL_DEG = -9.0  # rotation about the display normal: right side up → top edge rises to the right

LENS = 35.0
SENSOR = 36.0

for p in (STRIP_PNG, SEQ_DIR / f"{B['scrollStop']:04d}.png", SEQ_DIR / f"{F_END:04d}.png"):
    if not Path(p).exists():
        raise FileNotFoundError(f"{p} missing — run `npm run website:render` and tools/build_website_strip.py")

# --------------------------------------------------------------------------- scene
C.reset_scene()
sc = C.setup_scene(SCENE_ID, samples=64)
sc.render.filepath = str(C.RENDERS_DIR / SCENE_ID / "####")
C._set_enum(sc.view_settings, "view_transform", ("Standard",))
sc.view_settings.look = "None"

ee = sc.eevee
for prop, value in (
    ("volumetric_start", 0.1), ("volumetric_end", 30.0), ("volumetric_tile_size", "8"), ("volumetric_samples", 48),
    ("volumetric_sample_distribution", 0.85), ("use_volumetric_shadows", True), ("volumetric_light_clamp", 0.0),
    ("motion_blur_steps", 2), ("motion_blur_max", 160), ("motion_blur_depth_scale", 100.0),
):
    try:
        setattr(ee, prop, value)
    except (AttributeError, TypeError):
        pass
sc.render.use_motion_blur = False  # strip blur is in its shader (see build_strip_material)
sc.render.motion_blur_shutter = 0.5
try:
    sc.render.motion_blur_position = "CENTER"
except (AttributeError, TypeError):
    pass

# World: near-black blue void
world = bpy.data.worlds.new("W_void")
sc.world = world
world.use_nodes = True
wn = world.node_tree.nodes
bg = next(n for n in wn if n.type == "BACKGROUND")
bg.inputs["Color"].default_value = C.hex_rgba("#05080C")
bg.inputs["Strength"].default_value = 0.35


# --------------------------------------------------------------------------- helpers
def new_mesh_obj(name, bm, mats, parent=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob)
    if parent is not None:
        ob.parent = parent
    return ob


def principled(name, color, metallic=0.0, rough=0.5, coat=0.0, aniso=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    p.inputs["Base Color"].default_value = color
    p.inputs["Metallic"].default_value = metallic
    p.inputs["Roughness"].default_value = rough
    if "Coat Weight" in p.inputs:
        p.inputs["Coat Weight"].default_value = coat
    if aniso and "Anisotropic" in p.inputs:
        p.inputs["Anisotropic"].default_value = aniso
    return m


def box(bm, cx, cy, cz, sx, sy, sz):
    r = bmesh.ops.create_cube(bm, size=1.0)
    for v in r["verts"]:
        v.co = Vector((cx + v.co.x * sx, cy + v.co.y * sy, cz + v.co.z * sz))


def rect_plane(bm, x0, x1, z0, z1, y=0.0):
    vs = [bm.verts.new((x0, y, z0)), bm.verts.new((x1, y, z0)), bm.verts.new((x1, y, z1)), bm.verts.new((x0, y, z1))]
    f = bm.faces.new(vs)
    f.normal_update()
    if f.normal.y > 0:  # face the camera (−Y)
        f.normal_flip()
    return f


# --------------------------------------------------------------------------- display
display = bpy.data.objects.new("DISPLAY", None)  # screen centre; local −Y = towards the viewer
display.empty_display_type = "ARROWS"
sc.collection.objects.link(display)
display.rotation_euler = (0.0, math.radians(ROLL_DEG), 0.0)

M_alu = principled("S01_aluminium", C.hex_rgba("#9EA3A8"), metallic=1.0, rough=0.22, aniso=0.4)
M_back = principled("S01_anodised_back", C.hex_rgba("#1C1F23"), metallic=1.0, rough=0.38)
M_border = principled("S01_black_border", C.hex_rgba("#050607"), rough=0.6)

OW, OH = W + 2 * (BEZEL + RIM), H + 2 * (BEZEL + RIM)
bm = bmesh.new()
box(bm, 0.0, DEPTH / 2, 0.0, OW, DEPTH, OH)  # front face at y = 0
housing = new_mesh_obj("DISPLAY_housing", bm, [M_alu], display)
bev = housing.modifiers.new("bevel", "BEVEL")
bev.width, bev.segments, bev.limit_method = 0.009, 5, "ANGLE"
housing.modifiers.new("wn", "WEIGHTED_NORMAL")
# darker anodised back panel (seen in the oblique opening shot only from the rim)
bm = bmesh.new()
box(bm, 0.0, DEPTH + 0.004, 0.0, OW * 0.86, 0.008, OH * 0.82)
new_mesh_obj("DISPLAY_back", bm, [M_back], display)

# black border ring under the glass (screen hole in the middle)
bm = bmesh.new()
bw, bh = W / 2 + BEZEL, H / 2 + BEZEL
for (x0, x1, z0, z1) in ((-bw, bw, H / 2, bh), (-bw, bw, -bh, -H / 2), (-bw, -W / 2, -H / 2, H / 2), (W / 2, bw, -H / 2, H / 2)):
    rect_plane(bm, x0, x1, z0, z1, y=-0.0015)
new_mesh_obj("DISPLAY_border", bm, [M_border], display)
# matte black panel behind the screen area (what an "off" pixel looks like; never visible while the strip covers it)
bm = bmesh.new()
rect_plane(bm, -W / 2, W / 2, -H / 2, H / 2, y=-0.0005)
new_mesh_obj("DISPLAY_panel", bm, [M_border], display)

# glass cover: transparent + Fresnel-weighted gloss (reflects the soft boxes), slight rim reflections
M_glass = bpy.data.materials.new("S01_cover_glass")
M_glass.use_nodes = True
nt = M_glass.node_tree
nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial")
tr = nt.nodes.new("ShaderNodeBsdfTransparent")
gl = nt.nodes.new("ShaderNodeBsdfGlossy")
gl.inputs["Roughness"].default_value = 0.025
fr = nt.nodes.new("ShaderNodeFresnel")
fr.inputs["IOR"].default_value = 1.52
add = nt.nodes.new("ShaderNodeAddShader")
mul = nt.nodes.new("ShaderNodeMath")
mul.operation = "MULTIPLY"
mul.inputs[1].default_value = 1.0
nt.links.new(fr.outputs[0], mul.inputs[0])
# glossy tinted by the Fresnel factor (energy: transparent passes ~all light, gloss adds reflections on top)
rgb = nt.nodes.new("ShaderNodeCombineColor")
for k in range(3):
    nt.links.new(mul.outputs[0], rgb.inputs[k])
nt.links.new(rgb.outputs[0], gl.inputs["Color"])
nt.links.new(tr.outputs[0], add.inputs[0])
nt.links.new(gl.outputs[0], add.inputs[1])
nt.links.new(add.outputs[0], out.inputs["Surface"])
for prop, value in (("surface_render_method", "BLENDED"), ("use_transparency_overlap", False)):
    try:
        setattr(M_glass, prop, value)
    except (AttributeError, TypeError):
        pass
bm = bmesh.new()
rect_plane(bm, -bw, bw, -bh, bh, y=-0.004)
glass = new_mesh_obj("DISPLAY_glass", bm, [M_glass], display)
glass.visible_shadow = False

# --------------------------------------------------------------------------- website strip (real moving plane)
img_strip = bpy.data.images.load(str(STRIP_PNG), check_existing=True)
img_strip.colorspace_settings.name = "sRGB"
img_seq = bpy.data.images.load(str(SEQ_DIR / f"{B['scrollStop']:04d}.png"), check_existing=True)
img_seq.source = "SEQUENCE"
img_seq.colorspace_settings.name = "sRGB"
seq_len = F_END - B["scrollStop"] + 1


def build_strip_material():
    m = bpy.data.materials.new("S01_website_strip")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    N = nt.nodes
    L = nt.links

    def math_node(op, a=None, b=None):
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

    # strip-local coordinates (object = the strip itself): x ∈ [−W/2, W/2], z ∈ [−N·H, 0]
    tc_self = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(tc_self.outputs["Object"], sep.inputs[0])
    u = math_node("ADD", math_node("DIVIDE", sep.outputs["X"], W), 0.5)
    q = math_node("DIVIDE", sep.outputs["Z"], -H)  # page coordinate, 0 at the strip top

    # Shutter blur along the scroll: BLUR_TAPS taps spread over the distance (in pages) the strip travels during
    # the shutter (value node "blur_pages", keyed every frame from the scroll F-curve).
    blur = N.new("ShaderNodeValue")
    blur.name = blur.label = "blur_pages"
    # per-AA-sample jitter (white noise of the sub-pixel window position) → the taps converge to a smooth smear
    tc_win = N.new("ShaderNodeTexCoord")
    wmul = N.new("ShaderNodeVectorMath")
    wmul.operation = "SCALE"
    wmul.inputs["Scale"].default_value = 4096.0
    L.new(tc_win.outputs["Window"], wmul.inputs[0])
    wn = N.new("ShaderNodeTexWhiteNoise")
    wn.noise_dimensions = "3D"
    L.new(wmul.outputs[0], wn.inputs["Vector"])
    jit = math_node("DIVIDE", math_node("SUBTRACT", wn.outputs["Value"], 0.5), BLUR_TAPS)
    acc = None
    for i in range(BLUR_TAPS):
        off = math_node("MULTIPLY", blur.outputs[0], math_node("ADD", jit, (i + 0.5) / BLUR_TAPS - 0.5))
        qi = math_node("ADD", q, off)
        page = math_node("FLOOR", qi)
        local = math_node("SUBTRACT", qi, page)  # 0 top → 1 bottom of a page
        last = math_node("GREATER_THAN", page, N_PAGES - 1.5)
        src = math_node("ADD", math_node("MULTIPLY", math_node("FLOORED_MODULO", page, GENERIC), math_node("SUBTRACT", 1.0, last)),
                        math_node("MULTIPLY", last, STRIP_PAGES - 1))
        v_atlas = math_node("SUBTRACT", 1.0, math_node("DIVIDE", math_node("ADD", src, local), STRIP_PAGES))
        uv_a = N.new("ShaderNodeCombineXYZ")
        L.new(u, uv_a.inputs[0])
        L.new(v_atlas, uv_a.inputs[1])
        t_atlas = N.new("ShaderNodeTexImage")
        t_atlas.image = img_strip
        t_atlas.interpolation = "Linear"
        t_atlas.extension = "EXTEND"
        L.new(uv_a.outputs[0], t_atlas.inputs["Vector"])
        if acc is None:
            acc = t_atlas.outputs["Color"]
        else:
            mx = N.new("ShaderNodeMix")
            mx.data_type = "RGBA"
            mx.inputs["Factor"].default_value = 1.0 / (i + 1)  # running mean
            L.new(acc, mx.inputs["A"])
            L.new(t_atlas.outputs["Color"], mx.inputs["B"])
            acc = mx.outputs["Result"]

    # school page: the Remotion sequence (hover, click, ripple, UI fade) from scrollStop on (strip at rest)
    page0 = math_node("FLOOR", q)
    local0 = math_node("SUBTRACT", q, page0)
    is_last = math_node("GREATER_THAN", page0, N_PAGES - 1.5)
    seq_on = N.new("ShaderNodeValue")
    seq_on.name = seq_on.label = "school_seq_on"
    use_seq = math_node("MULTIPLY", is_last, seq_on.outputs[0])
    uv_s = N.new("ShaderNodeCombineXYZ")
    L.new(u, uv_s.inputs[0])
    L.new(math_node("SUBTRACT", 1.0, local0), uv_s.inputs[1])
    t_seq = N.new("ShaderNodeTexImage")
    t_seq.image = img_seq
    t_seq.interpolation = "Linear"
    t_seq.extension = "EXTEND"
    iu = t_seq.image_user
    iu.frame_duration = seq_len
    iu.frame_start = B["scrollStop"]
    iu.frame_offset = B["scrollStop"] - 1  # file number = film frame
    iu.use_auto_refresh = True
    iu.use_cyclic = False
    L.new(uv_s.outputs[0], t_seq.inputs["Vector"])

    col = N.new("ShaderNodeMix")
    col.data_type = "RGBA"
    L.new(use_seq, col.inputs["Factor"])
    L.new(acc, col.inputs["A"])
    L.new(t_seq.outputs["Color"], col.inputs["B"])

    # screen mask in DISPLAY space (fixed rectangle; the plane slides behind it)
    tc_disp = N.new("ShaderNodeTexCoord")
    tc_disp.object = display
    sep_d = N.new("ShaderNodeSeparateXYZ")
    L.new(tc_disp.outputs["Object"], sep_d.inputs[0])
    in_x = math_node("LESS_THAN", math_node("ABSOLUTE", sep_d.outputs["X"]), W / 2)
    in_z = math_node("LESS_THAN", math_node("ABSOLUTE", sep_d.outputs["Z"]), H / 2)
    mask = math_node("MULTIPLY", in_x, in_z)

    em = N.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 1.0  # Standard view transform → exact page pixels
    L.new(col.outputs["Result"], em.inputs["Color"])
    trn = N.new("ShaderNodeBsdfTransparent")
    mix = N.new("ShaderNodeMixShader")
    L.new(mask, mix.inputs["Fac"])
    L.new(trn.outputs[0], mix.inputs[1])
    L.new(em.outputs[0], mix.inputs[2])
    o = N.new("ShaderNodeOutputMaterial")
    L.new(mix.outputs[0], o.inputs["Surface"])
    try:
        m.surface_render_method = "DITHERED"  # binary mask → exact with hashed transparency
    except (AttributeError, TypeError):
        pass
    return m


M_strip = build_strip_material()
bm = bmesh.new()
rect_plane(bm, -W / 2, W / 2, -N_PAGES * H, 0.0, y=0.0)
strip = new_mesh_obj("WEBSITE_strip", bm, [M_strip], display)
strip.location = (0.0, -0.001, 0.0)
strip.visible_shadow = False
for attr in ("visible_volume_scatter",):
    if hasattr(strip, attr):
        setattr(strip, attr, False)


def strip_z(page_at_centre: float) -> float:
    """Strip-local origin (its top edge) height that puts page `page_at_centre` centred on the screen."""
    return H / 2 + page_at_centre * H


# Scroll F-curve (3 Bezier keys, hand-set handles): slow start → peak speed mid-way → smooth landing, zero speed at stop.
P_END = N_PAGES - 1
F0, F2 = B["scrollStart"], B["scrollStop"]
F1 = round((F0 + F2) / 2)
V_PEAK = 0.30  # pages per frame at the peak (≈ 0.4 m/frame on a 1.35 m screen → strong blur)
C.key_transform(strip, F0, location=(0.0, -0.001, strip_z(0)))
C.key_transform(strip, F1, location=(0.0, -0.001, strip_z(P_END / 2)))
C.key_transform(strip, F2, location=(0.0, -0.001, strip_z(P_END)))
fc_z = next(fc for fc in C.fcurves_of(strip) if fc.data_path == "location" and fc.array_index == 2)
k0, k1, k2 = fc_z.keyframe_points
for k in (k0, k1, k2):
    k.interpolation = "BEZIER"
    k.handle_left_type = k.handle_right_type = "FREE"
n1 = (F1 - F0) / 3.0
n2 = (F2 - F1) / 3.0
slope = V_PEAK * H  # metres per frame
k0.handle_right = (F0 + n1 * 1.0, k0.co.y)  # flat → slow start
k0.handle_left = (F0 - 1, k0.co.y)
k1.handle_left = (F1 - n1, k1.co.y - slope * n1)
k1.handle_right = (F1 + n2, k1.co.y + slope * n2)
k2.handle_left = (F2 - n2, k2.co.y)  # flat → soft landing, zero speed at the stop
k2.handle_right = (F2 + 1, k2.co.y)
for fc in C.fcurves_of(strip):
    if not (fc.data_path == "location" and fc.array_index == 2):  # (RNA wrappers: never compare with `is`)
        for k in fc.keyframe_points:
            k.interpolation = "CONSTANT"
fc_z.update()

SHUTTER = 0.5  # 180° shutter
nodes = M_strip.node_tree.nodes
blur_out = nodes["blur_pages"].outputs[0]
for f in range(F_START, F_END + 1):
    dz = fc_z.evaluate(f + SHUTTER / 2) - fc_z.evaluate(f - SHUTTER / 2)
    blur_out.default_value = abs(dz) / H
    blur_out.keyframe_insert("default_value", frame=f)
seq_out = nodes["school_seq_on"].outputs[0]
seq_out.default_value = 0.0
seq_out.keyframe_insert("default_value", frame=F_START)
seq_out.default_value = 1.0
seq_out.keyframe_insert("default_value", frame=B["scrollStop"])
for fc in C.fcurves_of(M_strip.node_tree):
    for k in fc.keyframe_points:
        k.interpolation = "CONSTANT" if "school_seq_on" in fc.data_path else "LINEAR"

# --------------------------------------------------------------------------- lights (rim, screen spill, soft boxes)
def area(name, loc, rot, size, watts, color, shape="RECTANGLE", size_y=None, volume=1.0, spec=1.0):
    ld = bpy.data.lights.new(name, "AREA")
    ld.shape = shape
    ld.size = size
    if size_y is not None:
        ld.size_y = size_y
    ld.energy = watts
    ld.color = color[:3]
    ld.volume_factor = volume
    ld.specular_factor = spec
    ob = bpy.data.objects.new(name, ld)
    sc.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = rot
    return ob


def spot(name, loc, target, watts, color, angle=30, blend=0.6, volume=1.0, radius=0.2):
    ld = bpy.data.lights.new(name, "SPOT")
    ld.energy = watts
    ld.color = color[:3]
    ld.spot_size = math.radians(angle)
    ld.spot_blend = blend
    ld.shadow_soft_size = radius
    ld.volume_factor = volume
    ob = bpy.data.objects.new(name, ld)
    sc.collection.objects.link(ob)
    ob.location = loc
    C.look_at(ob, target)
    return ob


teal = C.hex_rgba("#2F6E73")
amber = C.hex_rgba("#E3A33B")
# Rim lights behind the display (outline the bevelled frame, glow in the haze)
area("RIM_teal", (-1.9, 1.3, 0.9), Euler((math.radians(-70), 0, math.radians(-125))), 1.2, 260, (0.30, 0.75, 0.80, 1), volume=1.2)
area("RIM_amber", (2.0, 1.1, -0.9), Euler((math.radians(-105), 0, math.radians(120))), 1.0, 220, (1.0, 0.68, 0.32, 1), volume=1.2)
spot("TOP_shaft", (0.6, 2.4, 5.0), (0.0, 0.6, 0.0), 900, C.kelvin_rgba(5200), angle=26, blend=0.8, volume=1.6)
# Screen spill: the screen lights the haze in front of it and the rim (cool white)
scr_light = area("SCREEN_spill", (0, -0.02, 0), Euler((math.radians(90), 0, 0)), W, 0.0, C.kelvin_rgba(6500), size_y=H,
                 volume=0.8, spec=0.0)
scr_light.parent = display
scr_light.data.energy = 45.0
# Soft boxes for glass reflections (no camera visibility needed: area-light specular shows on the glass)
area("SOFTBOX_long", (-2.6, -3.2, 2.4), Euler((math.radians(60), 0, math.radians(-38))), 3.2, 140, C.kelvin_rgba(6000), size_y=0.25,
     volume=0.0)
area("SOFTBOX_low", (2.8, -2.6, -1.8), Euler((math.radians(118), 0, math.radians(42))), 2.0, 60, C.kelvin_rgba(4500), size_y=0.18,
     volume=0.0)

# --------------------------------------------------------------------------- haze (subtle, low-frequency)
M_haze = bpy.data.materials.new("S01_haze")
M_haze.use_nodes = True
nt = M_haze.node_tree
nt.nodes.clear()
vol = nt.nodes.new("ShaderNodeVolumePrincipled")
vol.inputs["Color"].default_value = (0.75, 0.82, 0.9, 1)
vol.inputs["Anisotropy"].default_value = 0.35
noise = nt.nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 0.18
noise.inputs["Detail"].default_value = 2.0
ramp = nt.nodes.new("ShaderNodeMapRange")
ramp.inputs["From Min"].default_value = 0.3
ramp.inputs["From Max"].default_value = 0.7
ramp.inputs["To Min"].default_value = 0.4
ramp.inputs["To Max"].default_value = 1.0
dens = nt.nodes.new("ShaderNodeMath")
dens.operation = "MULTIPLY"
dens.name = "haze_density"
dens.inputs[1].default_value = 0.035
nt.links.new(noise.outputs["Fac"], ramp.inputs["Value"])
nt.links.new(ramp.outputs["Result"], dens.inputs[0])
nt.links.new(dens.outputs[0], vol.inputs["Density"])
vo = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(vol.outputs[0], vo.inputs["Volume"])
bm = bmesh.new()
box(bm, 0, 2.0, 0, 26, 24, 16)
haze = new_mesh_obj("HAZE_volume", bm, [M_haze])
haze.visible_shadow = False
# the haze thins out as the camera dives in (the screen must read clean for the exact-photo hand-off)
dens_in = dens.inputs[1]
dens_in.keyframe_insert("default_value", frame=B["diveStart"] + 8)
dens_in.default_value = 0.0
dens_in.keyframe_insert("default_value", frame=B["alignedAt"])
C.set_easing(M_haze.node_tree, "EASE_IN_OUT")

# --------------------------------------------------------------------------- camera
focus = bpy.data.objects.new("CAM_FOCUS", None)
focus.parent = display
sc.collection.objects.link(focus)
cam = C.make_camera("CAM_S01", lens=LENS, location=(0, -5, 0), rotation=(math.radians(90), 0, 0), dof_target=focus, fstop=4.0)
C.set_lens(cam, LENS)

R_D = display.rotation_euler.to_matrix()
Q_ALIGNED = (R_D @ Euler((math.radians(90), 0, 0)).to_matrix()).to_quaternion()  # square-on, roll = display roll

THETA_A, THETA_0 = 36.0, 22.0  # orbit angle around the display's up axis (deg): start → at the click
PHI_A, PHI_0 = 10.0, 4.0  # elevation above the display's centre plane (deg)
K_A = 1.32  # start distance / distance at the click


def photo_distance(scale: float, theta_deg: float) -> float:
    """Camera distance so the screen spans `scale` × frame width (cos θ: foreshortened width when oblique)."""
    return W * LENS * math.cos(math.radians(theta_deg)) / (SENSOR * scale)


def level_look(pos: Vector) -> Quaternion:
    """Look at the display centre with a world-level horizon (the display then reads tilted diagonally)."""
    return (Vector((0, 0, 0)) - pos).to_track_quat("-Z", "Y")


def local_pos(theta, phi, d):
    t, p = math.radians(theta), math.radians(phi)
    return Vector((-d * math.sin(t) * math.cos(p), -d * math.cos(t) * math.cos(p), d * math.sin(p)))


prev_euler = [None]


def cam_pose(f: int):
    d_click = photo_distance(PHOTO_SCALE[B["diveStart"]], THETA_0)
    if f <= B["diveStart"]:
        u = (f - F_START) / (B["diveStart"] - F_START)
        e = 1 - (1 - u) ** 2  # already drifting at the fade-in, settles to rest at the click
        theta, phi = C.lerp(THETA_A, THETA_0, e), C.lerp(PHI_A, PHI_0, e)
        d = C.lerp(K_A, 1.0, e) * d_click
        pos = R_D @ local_pos(theta, phi, d)
        q = level_look(pos)
    else:
        w = C.smootherstep((f - B["diveStart"]) / (B["alignedAt"] - B["diveStart"]))
        theta, phi = THETA_0 * (1 - w), PHI_0 * (1 - w)
        d = photo_distance(PHOTO_SCALE[f], theta)
        pos = R_D @ local_pos(theta, phi, d)
        q = level_look(pos).slerp(Q_ALIGNED, w)
    eul = q.to_euler("XYZ", prev_euler[0]) if prev_euler[0] is not None else q.to_euler("XYZ")
    prev_euler[0] = eul
    return dict(location=tuple(pos), rotation=tuple(eul))


C.bake_path(cam, range(F_START, F_END + 1), cam_pose)

# fade up from black (0 → fadeInEnd), eased
C.key_value(sc.view_settings, "exposure", -10.0, F_START)
C.key_value(sc.view_settings, "exposure", 0.0, B["fadeInEnd"])
C.set_easing(sc, "EASE_OUT")

sc["s01_notes"] = (
    "Website strip = real plane under the glass (shader mask = screen rect). Camera distance from s01PhotoScale "
    "(blender/timeline.json). View transform Standard so the screen reproduces page pixels exactly."
)
sc.frame_set(F_START)
path = C.save_scene(SCENE_ID)
print("saved", path)
