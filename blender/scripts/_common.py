"""Shared helpers for every scene build script (blender/scripts/sNN_*.py).

Usage inside a scene script:

    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import _common as C

    C.reset_scene()
    sc = C.setup_scene("s02_turnstile")          # fps, resolution, frame range, EEVEE, AgX, PNG output
    cam = C.make_camera("CAM", lens=35, location=(0, -6, 1.6), target=(0, 0, 1.2))
    C.key_transform(cam, sc.frame_start, location=(0, -6, 1.6))
    C.key_transform(cam, sc.frame_end, location=(0, -2, 1.6))
    C.set_easing(cam, "EASE_IN_OUT")
    C.save_scene("s02_turnstile")

Frame ranges come from blender/timeline.json (generated from src/timeline.ts — never hard-code them).
Scenes use ABSOLUTE film frames (e.g. scene 2 = 270..449), so rendered file names match the film timeline.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

# --------------------------------------------------------------------------- paths

SCRIPTS_DIR = Path(__file__).resolve().parent
BLENDER_DIR = SCRIPTS_DIR.parent
ROOT = BLENDER_DIR.parent
SCENES_DIR = BLENDER_DIR / "scenes"
KIT_DIR = BLENDER_DIR / "kit"
RENDERS_DIR = ROOT / "renders"
ASSETS_DIR = ROOT / "assets"
TIMELINE_JSON = BLENDER_DIR / "timeline.json"

# --------------------------------------------------------------------------- timeline


def load_timeline() -> dict:
    """Read blender/timeline.json (run `npm run timeline:export` after editing src/timeline.ts)."""
    with open(TIMELINE_JSON, encoding="utf-8") as f:
        return json.load(f)


def get_scene_def(scene_id: str) -> dict:
    tl = load_timeline()
    for s in tl["scenes"]:
        if s["id"] == scene_id:
            return s
    raise KeyError(f"Scene '{scene_id}' not in {TIMELINE_JSON}. Known: {[s['id'] for s in tl['scenes']]}")


# --------------------------------------------------------------------------- scene setup


def reset_scene() -> None:
    """Start from an empty file (factory settings, no default cube/light/camera)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)


def _set_enum(owner, prop: str, wanted: tuple[str, ...]) -> str:
    """Assign the first identifier in `wanted` that this Blender build accepts; never hard-code blindly.
    Uses try/except because some enums (engine, view_transform) are dynamic and bl_rna under-reports them."""
    errors = []
    for w in wanted:
        try:
            setattr(owner, prop, w)
            return w
        except TypeError as e:
            errors.append(str(e))
    raise ValueError(f"None of {wanted} valid for {prop}: {errors[-1] if errors else ''}")


def setup_scene(
    scene_id: str,
    preview: bool = False,
    transparent: bool = False,
    samples: int = 128,
    color_depth: str = "8",
) -> bpy.types.Scene:
    """Configure the current scene from the timeline: fps, 1920×1080 base, frame range, EEVEE, AgX, PNG output.

    preview=True     → 50 % (960×540) and ~16 samples (values from timeline.json)
    transparent=True → RGBA with transparent film (for compositing in Remotion)
    """
    tl = load_timeline()
    d = get_scene_def(scene_id)
    sc = bpy.context.scene
    sc.name = scene_id

    # Time
    sc.render.fps = tl["fps"]
    sc.render.fps_base = 1.0
    sc.frame_start = d["from"]
    sc.frame_end = d["end"]
    sc.frame_current = d["from"]

    apply_render_settings(sc, preview=preview, transparent=transparent, samples=samples, color_depth=color_depth)
    sc.render.filepath = str(RENDERS_DIR / scene_id / "####")
    return sc


def apply_render_settings(
    sc: bpy.types.Scene,
    preview: bool = False,
    transparent: bool = False,
    samples: int = 128,
    color_depth: str = "8",
) -> None:
    """Resolution (base 1920×1080 + percentage), EEVEE with raytracing, AgX, PNG output. No frame range."""
    tl = load_timeline()
    r = sc.render
    # Resolution: always the base size; scale only via percentage (resolution-independent).
    r.resolution_x = tl["baseWidth"]
    r.resolution_y = tl["baseHeight"]
    r.resolution_percentage = tl["previewPercentage"] if preview else 100
    r.pixel_aspect_x = r.pixel_aspect_y = 1.0

    # Engine: EEVEE with screen-space raytracing (reflections, refraction) and fast GI / AO
    _set_enum(r, "engine", ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"))
    ee = sc.eevee
    ee.taa_render_samples = tl["previewSamples"] if preview else samples
    for prop, value in (("use_raytracing", True), ("use_fast_gi", True), ("use_shadows", True)):
        if hasattr(ee, prop):
            setattr(ee, prop, value)
    quality = (
        ("ray_tracing_method", "SCREEN"),
        ("shadow_pool_size", "512"),  # rooms have many shadow-casting downlights
        ("shadow_ray_count", 2),  # soft, accurate penumbrae
        ("shadow_step_count", 12),
        ("fast_gi_method", "GLOBAL_ILLUMINATION"),  # screen-space GI + AO: contact darkening in corners/under furniture
        ("fast_gi_distance", 1.5),
        ("fast_gi_resolution", "1"),
        ("fast_gi_quality", 0.75),
        ("clamp_surface_indirect", 8.0),  # kills sparkle/fireflies on glossy floors in sun patches
        ("gi_diffuse_bounces", 3),
    )
    for prop, value in quality:
        try:
            setattr(ee, prop, value)
        except (TypeError, AttributeError):
            pass
    rto = getattr(ee, "ray_tracing_options", None)
    if rto is not None:
        for prop, value in (("resolution_scale", "1"), ("use_denoise", True), ("denoise_spatial", True),
                            ("denoise_temporal", True), ("denoise_bilateral", True), ("screen_trace_quality", 0.5)):
            try:
                setattr(rto, prop, value)
            except (TypeError, AttributeError):
                pass

    # Colour management: AgX, neutral look
    sc.display_settings.display_device = "sRGB"
    _set_enum(sc.view_settings, "view_transform", ("AgX",))
    try:
        sc.view_settings.look = "None"
    except TypeError:
        pass
    sc.view_settings.exposure = 0.0
    sc.view_settings.gamma = 1.0

    # Output: PNG (absolute frame numbers when rendering sequences)
    r.film_transparent = transparent
    img = r.image_settings
    img.file_format = "PNG"
    img.color_mode = "RGBA" if transparent else "RGB"
    img.color_depth = color_depth
    img.compression = 15
    r.use_file_extension = True
    r.use_overwrite = True


def save_scene(scene_id: str) -> Path:
    """Save to blender/scenes/<id>.blend (no .blend1 backups)."""
    SCENES_DIR.mkdir(parents=True, exist_ok=True)
    path = SCENES_DIR / f"{scene_id}.blend"
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(path), check_existing=False)
    return path


# --------------------------------------------------------------------------- camera


def look_at(obj: bpy.types.Object, target) -> None:
    """Rotate obj so its -Z axis (camera view direction) points at target, +Y up."""
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def make_camera(
    name: str = "CAM",
    lens: float = 35.0,
    location=(0.0, -8.0, 1.6),
    target=None,
    rotation=None,
    sensor_width: float = 36.0,
    dof_target: bpy.types.Object | None = None,
    fstop: float = 2.8,
    set_active: bool = True,
) -> bpy.types.Object:
    """Create a camera. Give either `target` (look-at point) or `rotation` (Euler radians)."""
    data = bpy.data.cameras.new(name)
    data.lens = lens
    data.sensor_fit = "HORIZONTAL"
    data.sensor_width = sensor_width
    data.clip_start, data.clip_end = 0.01, 500.0
    if dof_target is not None:
        data.dof.use_dof = True
        data.dof.focus_object = dof_target
        data.dof.aperture_fstop = fstop
    cam = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = location
    if target is not None:
        look_at(cam, target)
    elif rotation is not None:
        cam.rotation_euler = rotation
    if set_active:
        bpy.context.scene.camera = cam
    return cam


# --------------------------------------------------------------------------- keyframes & easing


def key_transform(obj, frame: int, location=None, rotation=None, scale=None) -> None:
    """Set and keyframe the given transform channels at `frame`."""
    if location is not None:
        obj.location = location
        obj.keyframe_insert("location", frame=frame)
    if rotation is not None:
        obj.rotation_euler = rotation
        obj.keyframe_insert("rotation_euler", frame=frame)
    if scale is not None:
        obj.scale = scale
        obj.keyframe_insert("scale", frame=frame)


def key_value(owner, prop: str, value, frame: int) -> None:
    """Keyframe any property, e.g. key_value(cam.data, 'lens', 50, 300)."""
    setattr(owner, prop, value)
    owner.keyframe_insert(prop, frame=frame)


def fcurves_of(id_data) -> list:
    """F-curves of an ID's action; works with Blender 5.x layered actions (channelbags)."""
    ad = getattr(id_data, "animation_data", None)
    if ad is None or ad.action is None:
        return []
    act = ad.action
    try:
        from bpy_extras import anim_utils

        cb = anim_utils.action_get_channelbag_for_slot(act, ad.action_slot)
        return list(cb.fcurves) if cb else []
    except (ImportError, AttributeError):
        return list(getattr(act, "fcurves", []))


def set_easing(id_data, mode: str = "EASE_IN_OUT", interpolation: str = "BEZIER") -> None:
    """Smooth speed ramps on all keys of an object/data block. No linear starts/stops (CLAUDE.md).

    mode: EASE_IN, EASE_OUT, EASE_IN_OUT, AUTO
    interpolation: BEZIER (default), or SINE / QUAD / CUBIC / QUART / QUINT / EXPO / CIRC / BACK
    """
    for fc in fcurves_of(id_data):
        for kp in fc.keyframe_points:
            kp.interpolation = interpolation
            kp.easing = mode
            if interpolation == "BEZIER":
                kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"


# Pure easing functions (t in 0..1) for procedural animation / Geometry-Nodes drivers / sampling paths.


def clamp01(t: float) -> float:
    return 0.0 if t < 0.0 else 1.0 if t > 1.0 else t


def smoothstep(t: float) -> float:
    t = clamp01(t)
    return t * t * (3 - 2 * t)


def smootherstep(t: float) -> float:
    t = clamp01(t)
    return t * t * t * (t * (6 * t - 15) + 10)


def ease_in_cubic(t: float) -> float:
    return clamp01(t) ** 3


def ease_out_cubic(t: float) -> float:
    return 1 - (1 - clamp01(t)) ** 3


def ease_in_out_cubic(t: float) -> float:
    t = clamp01(t)
    return 4 * t**3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def ease_in_out_sine(t: float) -> float:
    return -(math.cos(math.pi * clamp01(t)) - 1) / 2


def ease_out_back(t: float, overshoot: float = 1.10158) -> float:
    """Small physical overshoot + settle (use sparingly; no cartoon bounce)."""
    t = clamp01(t)
    c3 = overshoot + 1
    return 1 + c3 * (t - 1) ** 3 + overshoot * (t - 1) ** 2


def lerp(a, b, t: float):
    if isinstance(a, (tuple, list, Vector)):
        return type(a)(x + (y - x) * t for x, y in zip(a, b)) if not isinstance(a, Vector) else a.lerp(b, t)
    return a + (b - a) * t


def bake_path(obj, frames: range, fn) -> None:
    """Keyframe obj every frame from fn(frame) -> dict(location=..., rotation=...). For exact hand-off matching."""
    for f in frames:
        key_transform(obj, f, **fn(f))
    for fc in fcurves_of(obj):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"  # every frame is keyed, so linear between samples is exact


# --------------------------------------------------------------------------- colour


def srgb_to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_rgba(h: str, alpha: float = 1.0) -> tuple:
    """'#EDE8E0' → linear RGBA for shader inputs."""
    h = h.lstrip("#")
    return tuple(srgb_to_linear(int(h[i : i + 2], 16) / 255) for i in (0, 2, 4)) + (alpha,)


def kelvin_rgba(kelvin: float) -> tuple:
    """Approximate black-body colour (Tanner Helland fit) as linear RGBA, for emission materials."""
    t = kelvin / 100.0
    r = 255 if t <= 66 else 329.698727446 * ((t - 60) ** -0.1332047592)
    g = 99.4708025861 * math.log(t) - 161.1195681661 if t <= 66 else 288.1221695283 * ((t - 60) ** -0.0755148492)
    b = 255 if t >= 66 else 0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307
    return tuple(srgb_to_linear(max(0.0, min(255.0, v)) / 255) for v in (r, g, b)) + (1.0,)


# --------------------------------------------------------------------------- camera rig

#: Consistent lens set (CLAUDE.md / step 4). Other focal lengths only where the storyboard
#: explicitly asks for them (macro close-ups, the CCTV feed camera) — pass allow_special=True.
LENSES = (24.0, 35.0, 50.0)


def make_camera_rig(
    name: str = "RIG",
    lens: float = 35.0,
    location=(0.0, 0.0, 1.6),
    rotation=(math.radians(90), 0.0, 0.0),
    focus_location=(0.0, 3.0, 1.2),
    fstop: float = 4.0,
    set_active: bool = True,
):
    """Empty RIG (animate this: location/rotation or a path) → child camera → DOF on a FOCUS empty.

    The camera sits at the rig origin with zero local rotation, so the rig's rotation IS the view
    (rig −Z = view direction, rig +Y = image up). Rotation (90°,0,0) looks horizontally along +Y.
    Returns (rig, cam, focus).
    """
    coll = bpy.context.scene.collection
    rig = bpy.data.objects.new(name, None)
    rig.empty_display_type = "ARROWS"
    rig.empty_display_size = 0.3
    rig.location = location
    rig.rotation_euler = rotation
    coll.objects.link(rig)

    focus = bpy.data.objects.new(f"{name}_FOCUS", None)
    focus.empty_display_type = "SPHERE"
    focus.empty_display_size = 0.1
    focus.location = focus_location
    coll.objects.link(focus)

    cam = make_camera(f"{name}_CAM", lens=lens, location=(0, 0, 0), rotation=(0, 0, 0), dof_target=focus, fstop=fstop,
                      set_active=set_active)
    cam.parent = rig
    return rig, cam, focus


def set_lens(cam, lens: float, frame: int | None = None, allow_special: bool = False) -> None:
    """Set (and optionally keyframe) the focal length, enforcing the lens set unless allow_special."""
    if lens not in LENSES and not allow_special:
        raise ValueError(f"Lens {lens} mm is not in the lens set {LENSES}; pass allow_special=True if the storyboard asks for it")
    cam.data.lens = lens
    if frame is not None:
        cam.data.keyframe_insert("lens", frame=frame)


def follow_path(rig, points, start: int, end: int, name: str = "RIG_PATH") -> bpy.types.Object:
    """Move the rig along a smooth curve through `points` (world coords) from frame start to end, eased.

    Use for travelling shots; downward hand-off segments use key_handoff() instead (constant speed).
    """
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.use_path = True
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(points) - 1)
    for bp, p in zip(sp.bezier_points, points):
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    rig.location = (0, 0, 0)
    con = rig.constraints.new("FOLLOW_PATH")
    con.target = ob
    con.use_fixed_location = True
    con.offset_factor = 0.0
    con.keyframe_insert("offset_factor", frame=start)
    con.offset_factor = 1.0
    con.keyframe_insert("offset_factor", frame=end)
    set_easing(rig, "EASE_IN_OUT")
    return ob


# --------------------------------------------------------------------------- scene hand-offs (docs/storyboard.md → Transitions)

#: Values from docs/storyboard.md. speed = metres per frame at the cut, held constant ±hold frames.
#: direction: "DOWN" = world −Z with the camera looking straight down; "VIEW" = along the anchor's view (−Z axis).
HANDOFF_TYPES = {
    "S": dict(lens=24.0, speed=0.12, direction="DOWN"),  # floor-slab pass (default)
    "G": dict(lens=50.0, speed=0.03, direction="VIEW"),  # screen-glass pass
    "F": dict(lens=18.0, speed=0.02, direction="VIEW"),  # CCTV feed match (special lens)
    "W56": dict(lens=35.0, speed=0.10, direction="VIEW"),  # window / sky pass 5→6
    "W67": dict(lens=35.0, speed=0.05, direction="VIEW"),  # facade window pass 6→7
    "H": dict(lens=35.0, speed=0.06, direction="DOWN"),  # haze match 8→9
}

#: (exit scene, entry scene) → hand-off type. Scenes 10 and 11 are Remotion-side (P, L).
TRANSITIONS = {
    ("s01_website", "s02_turnstile"): "G",
    ("s02_turnstile", "s03_cctv"): "S",
    ("s03_cctv", "s04_english"): "F",
    ("s04_english", "s05_russian"): "S",
    ("s05_russian", "s06_football"): "W56",
    ("s06_football", "s07_it"): "W67",
    ("s07_it", "s08_cafeteria"): "S",
    ("s08_cafeteria", "s09_dormitory"): "H",
    ("s09_dormitory", "s10_rewind"): "S",
}


def handoff_for(scene_id: str, which: str) -> str:
    for (exit_id, entry_id), kind in TRANSITIONS.items():
        if (which == "EXIT" and exit_id == scene_id) or (which == "ENTRY" and entry_id == scene_id):
            return kind
    raise KeyError(f"No {which} hand-off defined for {scene_id}")


def key_handoff(rig, cam, scene_id: str, which: str, anchor, hold: int = 6) -> range:
    """Key the ENTRY or EXIT pose of a scene from the storyboard hand-off table.

    `anchor` is an empty placed in this scene's file at the cut point (e.g. slab midpoint), oriented like
    the camera at the cut (for "DOWN" types only its Z rotation is used). Both files place their anchor
    at the identical spot relative to the shared geometry, so the cut is invisible.

    EXIT: frames end-hold … end, the camera reaches the anchor exactly on the last frame.
    ENTRY: frames from … from+hold, the camera starts one frame past the anchor (EXIT pose advanced one frame).
    Motion is constant speed (linear keys) inside the window; ease into/out of it with your other keys.
    """
    spec = HANDOFF_TYPES[handoff_for(scene_id, which)]
    d = get_scene_def(scene_id)
    mw = anchor.matrix_world
    origin = mw.translation.copy()
    if spec["direction"] == "DOWN":
        rot = (0.0, 0.0, anchor.matrix_world.to_euler().z)
        direction = Vector((0, 0, -1))
    else:
        rot = tuple(mw.to_euler())
        direction = (mw.to_3x3() @ Vector((0, 0, -1))).normalized()
    step = direction * spec["speed"]

    if which == "EXIT":
        frames = range(d["end"] - hold, d["end"] + 1)
        offset = lambda f: f - d["end"]  # noqa: E731
    else:
        frames = range(d["from"], d["from"] + hold + 1)
        offset = lambda f: f - d["from"] + 1  # noqa: E731

    for f in frames:
        key_transform(rig, f, location=origin + step * offset(f), rotation=rot)
        set_lens(cam, spec["lens"], frame=f, allow_special=True)
    for fc in fcurves_of(rig) + fcurves_of(cam.data):
        for kp in fc.keyframe_points:
            if frames.start <= kp.co.x <= frames.stop - 1:
                kp.interpolation = "LINEAR"
    return frames


# --------------------------------------------------------------------------- lighting presets (built by build_kit.py)

LIGHTING_PRESETS = ("day_interior", "warm_interior", "tech_dark", "outdoor_day")


def _find_layer_collection(layer_coll, name):
    if layer_coll.collection.name == name:
        return layer_coll
    for child in layer_coll.children:
        found = _find_layer_collection(child, name)
        if found:
            return found
    return None


def apply_lighting_preset(name: str, scene: bpy.types.Scene | None = None) -> dict:
    """Enable collection LIGHT_<name>, disable the other presets, and apply its world, exposure and the
    shared kit fixtures (downlights, LED strips) stored as JSON in the collection's "preset" property."""
    if name not in LIGHTING_PRESETS:
        raise KeyError(f"Unknown preset {name}; known {LIGHTING_PRESETS}")
    sc = scene or bpy.context.scene
    target = None
    for p in LIGHTING_PRESETS:
        lc = _find_layer_collection(bpy.context.view_layer.layer_collection, f"LIGHT_{p}")
        if lc is None:
            raise KeyError(f"Collection LIGHT_{p} not found — link/append it from blender/kit/school_kit.blend")
        lc.exclude = p != name
        if p == name:
            target = lc.collection
    cfg = json.loads(target["preset"])
    sc.world = bpy.data.worlds[cfg["world"]]
    sc.view_settings.exposure = cfg.get("exposure", 0.0)
    for key in ("downlight", "ledstrip", "accent", "screen"):
        light = bpy.data.lights.get(f"KIT_{key}")
        spec = cfg.get(key, dict(watts=0.0, kelvin=4000, emit=0.0))
        if light is not None:
            light.energy = spec["watts"]
            # Unlit fixtures must not consume EEVEE shadow pages; accents and screens are soft fills.
            light.use_shadow = spec["watts"] > 0 and key in ("downlight", "ledstrip")
            light.use_temperature = "kelvin" in spec
            if "kelvin" in spec:
                light.temperature = spec["kelvin"]
            else:
                light.color = spec["rgb"]
        mat = bpy.data.materials.get(f"KIT_{key}_emit")
        if mat is not None:
            em = next(n for n in mat.node_tree.nodes if n.type == "EMISSION")
            em.inputs["Color"].default_value = kelvin_rgba(spec["kelvin"]) if "kelvin" in spec else tuple(spec["rgb"]) + (1.0,)
            em.inputs["Strength"].default_value = spec["emit"]
    return cfg


# --------------------------------------------------------------------------- self-test

if __name__ == "__main__":
    # blender -b --factory-startup --python blender/scripts/_common.py
    reset_scene()
    sc = setup_scene("s02_turnstile")
    cam = make_camera(lens=35, location=(0, -6, 1.6), target=(0, 0, 1.2))
    key_transform(cam, sc.frame_start, location=(0, -6, 1.6))
    key_transform(cam, sc.frame_end, location=(0, -2, 1.6))
    set_easing(cam)
    print(
        "COMMON_OK",
        sc.name,
        sc.frame_start,
        sc.frame_end,
        sc.render.fps,
        f"{sc.render.resolution_x}x{sc.render.resolution_y}@{sc.render.resolution_percentage}%",
        sc.render.engine,
        sc.view_settings.view_transform,
        sc.render.image_settings.color_mode,
        len(fcurves_of(cam)),
        "fcurves",
        round(ease_in_out_cubic(0.25), 4),
    )
