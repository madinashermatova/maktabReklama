# Production plan — ZIYO YOG’DUSI commercial

75 s · 30 fps · 2250 frames (0–2249) · EEVEE · preview 960×540 @ ~16 samples · final 1920×1080.
Rules: see `CLAUDE.md`. Shot-level detail: `docs/storyboard.md`. Progress: `docs/status.md`.

## 1. Scene table

Frame ranges are inclusive. The starting timeline is kept unchanged — no reason found to move any boundary yet. Final ranges live in `src/timeline.ts` once Remotion work starts.

| # | Name | Start | End | Frames | Seconds | Technique | Main risk | Fallback |
|---|---|---|---|---|---|---|---|---|
| 1 | Website | 0 | 269 | 270 | 9.0 | Mixed: Remotion renders the invented website UI (hero image = the real entrance photo, sky replaced) as a frame sequence → used as screen texture on a Blender monitor; code-melt liquid in Blender | Code-melt liquid looks fake or is too heavy | 2D gooey-drip melt in Remotion (SVG/blur-threshold filter) over the Blender plate |
| 2 | Turnstile with Face ID | 270 | 449 | 180 | 6.0 | Mixed: opens on the 3D replica of the real entrance (`blender/kit/entrance.blend`, photo-matched), through the gate; Blender hall + terminal + glass-wing turnstiles; scan UI (abstract dot/mesh lattice, scan line, dots lighting in sequence) made in Remotion as a screen texture | The scan graphic reads as a face, or the action is unclear without people | Flat square dot lattice with no face-like features; simplify to scan line + green state + gate opening |
| 3 | CCTV | 450 | 599 | 150 | 5.0 | Mixed: Blender security-room set + monitor wall; feeds are low-res re-renders of other scene sets; Remotion adds generic CCTV overlay (REC dot, grid, camera IDs) | Rendering extra feed angles costs time; feeds must not look like real CCTV branding | Feeds use stills from other scenes with slow Remotion pans |
| 4 | English class | 600 | 809 | 210 | 7.0 | Blender | Empty classroom feels lifeless | Motion through objects: books unfold, letters on board assemble, globe rotates, curtain cloth breathes |
| 5 | Russian class | 810 | 989 | 180 | 6.0 | Blender (shares classroom kit with 4, different dressing) | Looks like a copy of scene 4 | Different camera path, colour accent, props (Cyrillic alphabet chart, literature books) |
| 6 | Football field | 990 | 1229 | 240 | 8.0 | Blender | Grass density + outdoor lighting on iGPU; long render | GN grass only near camera, textured + displaced ground far away; HDRI sky |
| 7 | IT class | 1230 | 1469 | 240 | 8.0 | Mixed: Blender room + Remotion-made generic code/UI on screens as textures | Many screens = many textures; generic UI must not resemble real OS | One shared screen sequence, offset per monitor |
| 8 | Cafeteria — plov | 1470 | 1709 | 240 | 8.0 | Blender | Plov (rice grains, steam) hard to make appetising | Shader-based rice mound with displacement + a few GN grains on top; steam as animated volume, fallback alpha cards |
| 9 | Dormitory | 1710 | 1919 | 210 | 7.0 | Blender | Cloth blanket sim instability | Shape-key / lattice animated blanket |
| 10 | Rewind | 1920 | 2069 | 150 | 5.0 | Remotion, reusing rendered frames of scenes 1–9 | Conflicts with "camera always travels down" (see open question Q1) | Simple accelerating montage (no reversed motion) |
| 11 | Brand reveal | 2070 | 2249 | 180 | 6.0 | Mixed: Blender light/background plate + typographic wordmark `ZIYO YOG’DUSI` composited in Remotion; optional logo slot (`src/brand.ts`, empty for now) | Font without native ’ (U+2019) glyph or without commercial licence | Choose another OFL font that passes the glyph check; never fall back to a substitute glyph |

Total 2250 frames ✔. Blender-rendered frames: scenes 1–9 + 11 ≈ **2100 frames**; scene 10 is pure Remotion.

### World layout (vertical film strip)

Each scene lives in its own `.blend` around its own origin. The camera always travels downward (or forward-and-down) between scenes. The floor-slab pass is the default; six transition types are used in total:

| Cut | Type |
|---|---|
| 1 → 2 | D — Photo-to-3D dissolve (real entrance photo on the website → 3D replica, through the gate to the turnstile) |
| 2 → 3 | S — Floor slab |
| 3 → 4 | C — Lens pass into the CCTV dome lens (replaces F, user decision 2026-11-26) |
| 4 → 5 | S — Floor slab |
| 5 → 6 | W — Window / sky pass (classroom window → sky over the stadium) |
| 6 → 7 | W — Facade window pass (stadium → IT class) |
| 7 → 8 | S — Floor slab |
| 8 → 9 | H — Haze match (plov steam → dorm lamp glow) |
| 9 → 10 | S → P — Slab, then film-strip pull-back (Remotion) |
| 10 → 11 | L — Point of light |

Exact EXIT/ENTRY values for each type are in `docs/storyboard.md` → "Transitions". **Risk:** the W passes assume the Russian classroom and the IT class have exterior windows, and that the IT class is beside the field. There are no reference photos, so the building is designed to support this (see §4 kit plan); the fallback for any W, H or F transition is S.

## 2. Hardest effects

### Code melting into liquid (scene 1)
- **Technique:** website code lines (Remotion-rendered texture) on the monitor heat up (emission ramp), then lines detach as real geometry: text converted to curves → mesh in GN, the meshes are pulled down by a GN "gravity + noise" deformation and merged via **Mesh-to-Volume → Volume-to-Mesh** (metaball-like blobs) for the drips; glossy, slightly emissive liquid material. Drips fall off the monitor edge and lead the camera downward into the slab (scene exit). Bake as **Alembic / GN bake**, ~100 frames, low voxel resolution, smoothed with subdivision.
- **Fallback A:** Blender metaballs animated along drip curves (cheap, stable).
- **Fallback B:** 2D melt in Remotion (SVG displacement + gooey threshold filter) over a Blender plate.

### Plov (scene 8)
- **Technique:** kazan (cast-iron pot) and serving plate modelled procedurally. Rice mound = base mesh with displacement + **GN-instanced rice grains** (low-poly capsule, ~20–40k instances, only on the visible surface), carrot strips and chickpeas instanced on top, meat pieces as sculpted-by-noise meshes; subsurface-ish rice shader, oil sheen via clearcoat. Steam = **EEVEE volume** (cube with animated noise density) — no simulation.
- **Motion:** the cover lifts off and slides away, steam rises; plate assembles (grains settle onto plate via GN "drop & settle" animation, not a physics sim).
- **Fallback:** shader-only rice mound (no instances) + alpha-card steam planes.

### Cloth (scene 9, also curtains 4/5, goal net 6)
- **Technique:** blanket unfolds and settles on a bed: **light cloth sim** on a ~40×40 grid (~1.6k verts), collision with mattress/pillow only, bake ~80 frames, then subdivision ×2 + solidify. Curtains: wind via low-res cloth or a GN wave deformer. Goal net: static mesh + GN ripple when the ball hits.
- **Fallback:** shape-key animation (folded → flat) or a lattice-driven unfold.

### Other risks
- **Grass (scene 6):** GN instanced blades in a camera-frustum mask (~150k blades near camera), mown-stripe colour variation; distant field is a textured plane with normal map.
- **Reflections / glass:** EEVEE raytracing on; screen-space fallback for previews.
- **Continuity cuts:** every transition type (S, D, F, W, H) has exact EXIT/ENTRY values; camera keyframes on both sides are generated from one shared Python module (`blender/scripts/common/camera_handoff.py`). The D dissolve needs the 3D replica to overlay the photo (camera solve + overlay check, `tools/overlay_match.py`); the W pass needs the same HDRI and exposure on both sides; the H pass needs matched luminance and tint (checked by sampling the two frames).

## 3. Render budget

Benchmark (audit, simple 4-object scene, 1080p, EEVEE default samples): **14.1 s/frame** (20.1 s cold). Real scenes are heavier — assume **2–3×**.

| Pass | Frames | s/frame (estimate) | Time per full pass |
|---|---|---|---|
| Preview 960×540, ~16 samples | ~2100 | 2–5 s | **~1.2–3 h** |
| Final 1920×1080, 32–64 samples | ~2100 | 28–42 s | **~16–25 h** |
| CCTV feed re-renders (scene 3, low-res) | ~4 × 150 | ~2 s | ~20 min |

- Plan ~3 preview iterations per scene and 1 final; finals render scene by scene overnight via the Blender CLI.
- Measure real per-scene s/frame on the first preview of each scene and update this table.
- Disk: 1080p RGBA PNG ≈ 3–5 MB/frame → ~10 GB for finals, ~3 GB for previews. 132 GB free on C: is enough.
- Remotion assembly render: minutes (2D only).
- 4K later: AI upscale of the 1080p sequence, or re-render on a GPU render farm (scenes are resolution-independent).

## 4. Assets

**Reference photo:** `assets/reference/entrance_front.jpg` (the real entrance, 2026-11-26) — hero image of scene 1 (sky replaced only) and the reference for the 3D entrance replica. Every other space (corridors, classrooms, cafeteria, sports ground, dormitory) has no photo and is designed in Blender.

### Design language — CHOSEN: A "Warm modern" (fixed for the whole film)
- Warm white walls, light oak floors/doors, teal accent, amber small accents, graphite frames, white ceiling. Full spec: `docs/design-language.md`. B and C were rejected and removed from the kit.
- Real school details (building colour, number of floors, roof shape, main colours): **none provided yet** — neutral choices until given.

### Kit status (`blender/kit/school_kit.blend`, built by `blender/scripts/build_kit.py`)
- Built: walls (plain / window / door), floor, ceiling with real downlights + LED slots, skirting, corner post, student desk, school chair, monitor, LED accent channel, exterior backdrop (schoolyard, trees, low buildings), materials, 4 lighting presets, camera rig + hand-off helper.
- Built 2026-11-26: floor slab `PIECE_slab` (`kit_slab.py`), school building exterior `PIECE_school_building` + `PIECE_school_grounds` (`kit_building.py`, hero still via `kit_exterior_hero.py`).
- Still to build: remaining furniture listed below.

### Procedural (built by scripts in `blender/scripts/`, shared parts in `blender/kit/`)
- **School building exterior:** ~~kit building~~ superseded (2026-11-26): the website hero is the real entrance photo (scene 1).
- **Stadium background (scene 6) — user decision 2026-11-26:** the school seen beside the field is the **real left building from the entrance reference** (`assets/reference/entrance_front.jpg`: cream/beige plaster, 3 storeys, brown roof edge), **extended in the same style** (same window rhythm, plaster, roof edge; extension = neutral invented detail, listed in `docs/status.md`), slightly out of focus. Trees from the tree generator of the superseded kit building (`kit_building.py`). The kit building `PIECE_school_building` is not used in the film. The 6 → 7 facade window pass goes through a ground-floor window of this building.
- Architecture kit: walls, floor, ceiling grid, window frames, doors, slab, light fixtures, corridor module.
- Furniture: desks, chairs, whiteboard, shelves, bunk/single beds, cafeteria tables, security desk.
- Tech: monitors, PCs, keyboards, CCTV cameras, glass-wing turnstiles + Face ID terminal (abstract dot-lattice UI).
- Kazan, plates, rice/carrot/chickpea instances, steam volume.
- Football goals, net, field markings, ball (unbranded panels), GN grass.
- Code-melt liquid, cloth (blankets, curtains).
- All screen UIs (website, IT code, CCTV overlay) — generic, invented, made in Remotion.

### From Poly Haven via the MCP (`search_assets` / `import_asset`)
**Note:** the Poly Haven library is currently **off** in the Blender MCP add-on — enable it in the add-on preferences before asset work starts. Meanwhile the kit uses three CC0 Poly Haven HDRIs bundled with Blender (`assets/hdri/`, see `docs/assets-credits.md`).
- HDRIs: daytime sky for the football field; soft interior/studio HDRIs for reflections.
- PBR textures: wood floor, laminate, concrete, painted plaster, fabric, leather, cast iron, grass/soil, metal.
- Optional models: potted plants, books, small decor — only if they fit the design language and carry no brand marks.

### You must provide
1. **Licensed instrumental music** → `assets/audio/music/` (≥75 s, licence document alongside).
2. **Confirmation of facilities:** that the school really has every facility in the scene table (turnstile with Face ID, CCTV, football field, IT class, cafeteria, dormitory).
3. Website UI language (see Q2).
4. Optional: real details of the building (colour, floors, roof shape, main colours) — used if given.

Welcome: more photos of the school (other sides of the entrance, courtyard, turnstile area) — they replace invented detail.

**Not blocking:** an official logo does not exist yet. The brand is the wordmark `ZIYO YOG’DUSI`; if a logo is made later, drop it into `assets/brand/` and set `logoFile` in `src/brand.ts` (see CLAUDE.md → BRAND).

### Fonts (wordmark)
- Candidate typefaces must be commercially licensed (e.g. SIL OFL) and contain **U+2019 (and U+201C/U+201D for the signboard) natively** — verified with a fontTools `cmap` check before use; results recorded in `docs/status.md`. Fonts and licence files go in `assets/fonts/`.
- In use: **Montserrat Bold** (SIL OFL 1.1, `assets/fonts/Montserrat-Bold.ttf` + `OFL-Montserrat.txt`) for the 3D signboard replica — closest open geometric sans to the real sign lettering. The scene 1/11 wordmark font is still to be chosen (Montserrat passes the glyph check and is a candidate).

## 5. Open questions (need your decision)

- **Q1 — Rewind vs. "camera always goes down":** proposal — in scene 10 the camera does not move up. Instead the camera pulls back to reveal the whole vertical film strip (all previous scenes as frames), and the *strip* scrolls upward past a fixed camera at increasing speed, ending on scene 1's frame, which collapses into the brand reveal. Is that acceptable?
- **Q2 — Language of the website UI text** (Uzbek Latin / Uzbek Cyrillic / Russian / English)?
- **Q3 — Scene 3 CCTV:** may the feeds show other rooms of the school (empty), and may an overlay show a running time code (generic, no date)?
- **Q4 — Brand reveal:** brand name only, or also a slogan/website/phone? (Only text you supply will be used.)
