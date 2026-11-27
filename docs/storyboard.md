# Storyboard — ZIYO YOG’DUSI commercial

30 fps · frames are absolute film frames (0–2249). Timeline revised 2026-11-27: scene 2 → 8 s (270–509), scene 3 moved to 510–659 (not re-rendered: its `.blend` and frames keep their 450–599 numbering, `blendFrom` in `src/timeline.ts`; Blender frame = film frame − 60), scene 5 → 5 s, scene 6 → 7 s; total still 75 s. No people, no voice, no subtitles.
One school day, morning (scene 2) to evening (scene 9); every room has its own atmosphere and camera language (`docs/design-language.md` → Room atmospheres, binding). CCTV cameras only in scene 3 (exception: the real camera in the entrance photo / replica).
Lens values are full-frame equivalent (36 mm sensor). "KF" = key frame.
Sound cues listed here are copied into `docs/sound-cues.md` once frames are locked; all SFX are made with ElevenLabs `text_to_sound_effects` into `assets/audio/sfx/`. Music: your licensed instrumental track (`assets/audio/music/`), edited to hit the marked accents.

---

## Transitions

The floor-slab pass is the default; six transition types are used in total. Every transition moves the camera downward (or forward-and-down) and has a matched EXIT/ENTRY definition. Camera paths on both sides of every cut come from one shared module (`blender/scripts/common/camera_handoff.py`).

| Cut | Frame (exit → entry) | Type | Motivation |
|---|---|---|---|
| 1 → 2 | 269 → 270 | **D — Photo-to-3D dissolve** (user decision 2026-11-26) | The camera pushes into the real entrance photo on the website; the photo dissolves into the 3D replica seen from the solved photo camera; the camera then moves toward the guard booth and the Face ID turnstile beside it |
| 2 → 3 | 509 → 510 | **S — Floor-slab pass** (default) | After the turnstile the camera glides into the courtyard toward the glass cafeteria, tilts down and sinks into the paving, on into the slab (matched to scene 3's existing ENTRY) |
| 3 → 4 | 659 → 660 | **C — Lens pass** (user decision 2026-11-26, replaces F) | The corridor dome camera turns to face us; the camera pushes forward-and-down into its coated lens; inside the lens the frame goes dark, and scene 4 opens from that darkness onto the English class from a high corner — no camera in the classroom, no CCTV look (rule: CCTV only in scene 3) |
| 4 → 5 | 869 → 870 | **S — Floor-slab pass** | — |
| 5 → 6 | 1019 → 1020 | **W — Window / sky pass** | Camera passes through the classroom window; the bright sky fills the frame; the cut is on matched sky; descent toward the stadium |
| 6 → 7 | 1229 → 1230 | **W — Window pass (facade)** | Camera descends along the school's glazed facade beside the field and passes through a window into the IT class |
| 7 → 8 | 1469 → 1470 | **S — Floor-slab pass** | — |
| 8 → 9 | 1709 → 1710 | **H — Haze match** | Camera descends into the plov steam; warm white haze fills the frame; it resolves into the glow of the dormitory's frosted ceiling lamp |
| 9 → 10 | 1919 → 1920 | **S → P — Slab, then film-strip pull-back** (Remotion) | The slab frame shrinks into one cell of the vertical film strip |
| 10 → 11 | 2069 → 2070 | **L — Point-of-light** | The last strip frame collapses to a point of light that blooms into the wordmark |

### S — Floor-slab pass (default)
Shared slab kit piece `PIECE_slab` in `blender/kit/school_kit.blend` (1.2 m thick: concrete decks, sealed cavity with ribs, cable trays, duct, warm LED strips). The cut sits at the slab midpoint.

| Property | EXIT (last frame of N) = ENTRY (first frame of N+1) |
|---|---|
| Position | empty `HANDOFF` at slab midpoint; X/Y = 0 in handoff space |
| Rotation | looking straight down (−Z), roll 0°, image "up" = scene +Y |
| Focal length | 24 mm, DOF off during the pass |
| Motion | descending 0.12 m/frame (3.6 m/s), constant ±6 frames around the cut; ENTRY = EXIT pose advanced one frame |
| Light | slab interior only: warm-white LED strips 4000 K. Both scene files call `C.key_slab_isolation(first, last)` for the frames the camera is inside the slab (world strength 0, exposure `SLAB_EXPOSURE`, switched while the camera is inside a solid deck) — verified identical cut frame under different presets (`kit_slab_test.py`) |
| Kit | `PIECE_slab` (`blender/scripts/kit_slab.py`); anchor = `C.slab_handoff_matrix(instance)`; probes = `C.add_slab_probe(instance)` |

### D — Photo-to-3D dissolve (1 → 2) — replaces the former G screen-glass pass (user decision 2026-11-26)
Reference: `assets/reference/entrance_front.jpg` (the real entrance). Hero image: `tools/hero_sky.py` (sky replaced only).

**Camera solve of the photo** (`blender/scripts/build_entrance.py`, values stored in `entrance.blend` → scene `photo_solve`):
| Quantity | Value | How |
|---|---|---|
| Orientation | level (verticals vertical), facade parallel to the image (yaw < 1°) | vertical edges; signboard top edge slope 0.005 |
| Principal point = street vanishing point | (681, 478) px of 1280 × 720 → lens shift x −0.032, y +0.092 | least-squares of left/right roof edges, right plinth, wall cable (spread ±10 px). 478 ≈ the centre of a 4:3 frame cropped to 16:9 |
| Focal length | f ≈ 545 px ±10 % → **15.3 mm** on a 36 mm sensor (an ultra-wide phone lens) | square checker paving: f = (y − y_h) · column period / row period |
| Camera height / distance | **1.40 m**, entrance facade at **8.48 m** — ASSUMED scale | booth door ≈ 2.2 m, paving tile ≈ 0.24 m; replace with one real measurement (gate height or pillar width) when available |

| Property | EXIT 269 (scene 1, Remotion/website) | ENTRY 270 (scene 2, Blender) |
|---|---|---|
| Frame content | the hero photo fills the frame, pushed in **1.174×** around its centre | the 3D replica from `CAM_S02_START` — same framing; the photo cross-dissolves to the render over 270–285 |
| Camera | (2D push-in) | position (0, 0, 1.40), looking +Y, level; **18 mm** = 15.33 mm × 1.174, shifts × 1.174 (lens rule: never wider than 18 mm in the film; the 15.3 mm `CAM_PHOTO_MATCH` is a measurement camera only) |
| Motion | push-in eases to a constant 1.0 %/frame scale rate ±6 frames | forward (+Y) 0.03 m/frame, matching the apparent push-in, then eases on toward the guard booth |
| Light | photo with the replaced morning sky | `W_entrance_morning` sky + sun 5400 K from the right (34°), same look as the hero sky |

### C — Lens pass (3 → 4) — replaces the former F feed match (user decision 2026-11-26)
| Property | EXIT 659 (scene 3; `.blend` frame 599) | ENTRY 660 (scene 4) |
|---|---|---|
| Frame content | inside the dome camera's lens: camera 12 mm behind the coated front element, looking down the barrel — near-black, faint green/purple coating ring | the same near-black frame (matched luminance, faint neutral glint); over 660–675 the darkness opens like an iris onto the sunlit English classroom from a high corner — a purely cinematic reveal: no camera object in the room, no CCTV look |
| Camera | 35 mm, looking along the lens axis (forward and 2.3° down), anchor `EXIT_ANCHOR_C` in `s03_cctv.blend` | 35 mm, high corner of the classroom, same forward-and-down direction |
| Motion | forward-and-down 0.01 m/frame, constant ±6 frames (`C.HANDOFF_TYPES["C"]`) | same, then the crane down into the room |
| Light | none inside the lens (EEVEE: only reflections) | dark → English-class daylight 5200 K |
| Note | CCTV cameras appear only in scene 3 (user, 2026-11-26) — scene 4 shows none | |

### W — Window / sky pass (5 → 6, 6 → 7)
- **5 → 6:** EXIT 1019: the camera has passed through the open classroom window; the frame is filled by bright sky (the same HDRI as scene 6, overexposed +1.5 EV at the cut), looking 45° down, 35 mm, moving forward-and-down 0.10 m/frame. ENTRY 1020: the same sky and exposure; exposure eases back to 0 EV over 1020–1040, revealing the stadium below.
- **6 → 7:** EXIT 1229: the frame is filled by one window pane of the school's glazed facade (reflecting sky and field), 35 mm, looking horizontally, moving forward-and-down 0.05 m/frame. ENTRY 1230: the same pane from the inside (sky reflection matched), the camera continues through it into the IT class.
- **Design:** the Blender-designed building gives the Russian classroom and the IT class exterior windows, with the IT class facing the field (see the kit plan). Fallback: S.

### H — Haze match (8 → 9)
| Property | EXIT 1709 | ENTRY 1710 |
|---|---|---|
| Frame content | steam volume fills the frame: uniform warm white haze (target luminance 0.85, 3200 K tint) | the dormitory's frosted ceiling-lamp diffuser glow filling the frame, same luminance and tint |
| Camera | looking straight down, 35 mm, descending 0.06 m/frame | same |
| Fallback | S | |

### P and L (Remotion)
Defined in scenes 10 and 11.

---

## Scene 1 — Digital website universe (0–269, 9.0 s)

Concept (user decision 2026-11-26, replaces the former desk / code-melt board): a large premium floating display in a dark hazy void scrolls through a strip of invented websites and stops on the ZIYO YOG’DUSI website; a cursor clicks its hero button and the camera dives into the screen until the real entrance photo fills the frame. Built by `blender/scripts/scene_01_website.py` → `blender/scenes/s01_website.blend`. Beats: `S01_BEATS` in `src/timeline.ts`.

**ENTRY:** film start. Black → fade up 0–12.
**EXIT:** D at frame 269 — the website hero (the real entrance photo, sky replaced) fills the frame, pushed in 1.174× around its centre (Remotion lays the exact photo pixels over the render 252–258 → 269).

Website strip (`blender/kit/textures/website_strip.png`, made by `npm run website:render` + `tools/build_website_strip.py`): 6 invented generic sites (travel, store, news, fitness, bank-like dashboard, portfolio — invented names, readable words, no real brands) and the school site last. The school page shows only the wordmark **ZIYO YOG’DUSI** (U+2019, no quotes, no symbol; empty logo slot while `logoFile` is `null`), Uzbek navigation (Bosh sahifa, Biz haqimizda, Qabul, Aloqa) and facts only (Samarqand viloyati, 1–11-sinflar, xususiy maktab). Hero image = the approved real photo `assets/hero/entrance_hero_1920.png`.

| KF | Frame | In frame | Camera / lens | Light | Motion |
|---|---|---|---|---|---|
| 1a | 0–14 | Floating display (thin bevelled aluminium rim, black border, glass cover), tilted diagonally (top edge rising to the right), in a dark void with subtle haze; first page (travel site) on screen | 35 mm, oblique (36° around the display), f/4 on the screen centre; slow drift in | Teal and amber rim lights behind the display, a top light shaft in the haze, cool screen spill | Fade up 0–12 |
| 1b | 14–102 | The strip starts to scroll slowly, then accelerates | camera keeps drifting in, orbit 36° → 22° | same | Scroll F-curve: flat start, peak 0.30 pages/frame at 102 |
| 1c | 102–190 | Pages fly past (3 passes of the 6 sites; strong shutter blur), decelerate and land **exactly** on the school site at 190 | same | same | Smooth landing, zero speed at 190 |
| 1d | 194–215 | Cursor (generic arrow, no hand) fades in, glides on an eased arc to "Maktab bilan tanishing", hover at 210, press + soft ripple at 215 | camera settles to rest at the click (218) | same | Eased path; press scale 0.955 |
| 1e | 218–269 | Website UI fades away (221–236) leaving only the photo; the camera dives square-on into the screen (aligned, roll matched, at 246); the photo fills the frame and keeps pushing at the D rate | 35 mm; distance from `s01PhotoScale(frame)` (shared curve, `blender/timeline.json`) | the photo's morning light; haze thins out 226–246 | Hermite ease into the constant D push rate (last 6 frames) |

**Sound cues:** see `docs/sound-cues.md` → Scene 1 (scroll whoosh 14 → peak 102 → 190, scroll stop 190, hover 210, click 215, dive whoosh 218 → 270).

---

## Scene 2 — Turnstile with Face ID (270–509, 8.0 s)

Real layout (user, 2026-11-27): the school has **one** Face ID turnstile, at the entrance, in the passage between the laser-cut gate and the guard booth (qorovul xonasi) on the right of the entrance photo — facility confirmed. The building straight ahead after the turnstile is the school **cafeteria with a glass facade** (user, 2026-11-27). Built by `blender/scripts/scene_02_turnstile.py` → `blender/scenes/s02_turnstile.blend`, on the approved replica (`blender/kit/entrance.blend`, appended; the gate stays closed) with two deliberate replacements: the courtyard building's door, barred windows and wall AC units → the cafeteria glass wall + interior (`blender/scripts/kit_cafeteria.py`, **shared with scene 8**), and the low-poly potted palms → modelled potted palms (`blender/scripts/kit_plants.py`). Beats: `S02_BEATS` in `src/timeline.ts`. Face ID display: Remotion composition `S02-FaceID-Screen` (`src/s02/FaceIdScreen.tsx`) → `npm run faceid:render` → `renders/_faceid/` (image-sequence texture).

**ENTRY:** D at 270 — the photo (pushed in 1.174×) dissolves into the 3D replica. The photo layer (`ENTRANCE_PROJ` in `entrance.blend` → `renders/s02_turnstile_proj/`, alpha) lies over the scene-2 render in Remotion (`<S02EntryPhoto>`) and is fully transparent at 300. Camera path, 18 mm lens and lens shift 270–300 are identical to `CAM_S02_START`. Seen through the gate, the photo shows the old courtyard facade (door, barred windows), the old palms and an open passage; the 3D shows the glass cafeteria, the modelled palms and the turnstile — these fade in with the 3D during the dissolve (the photo itself is unchanged).
**EXIT:** S at 509 — the camera sinks through the courtyard paving in front of the cafeteria into the kit slab under it (24 mm, straight down, 0.12 m/frame, frames 503–509). The slab is turned to the camera's final heading, so the camera arrives in exactly the pose of scene 3's existing ENTRY (same kit slab, same anchor) — **scene 3 is not re-rendered**.
**Atmosphere** (`docs/design-language.md` → Room atmospheres): early morning, the approved replica light and look · brushed steel, clear glass; through the cafeteria glass a warm interior (cream walls, terracotta floor, oak tables, warm pendants) · camera language: **precise moves with exact stops**, then a slow calm glide · mood: security, then welcome. **Verticals stay vertical:** the camera pitch is locked level until the final tilt into the paving (2f); vertical framing uses lens shift only.

**Face ID UI rule:** the terminal display shows only an abstract **dot/mesh grid** — a rounded-SQUARE lattice of 20 × 20 points (only the 4 corner points trimmed) joined by thin triangulated lines, gently undulating like a surface. There is **no face, head, silhouette or body shape**: no oval outline, no eyes, nose, mouth or shoulders. No text (colour, three indicator dots and one generic check glyph only). Red while locked/scanning, green when granted.

| KF | Frame | In frame | Camera / lens | Light | Motion |
|---|---|---|---|---|---|
| 2a | 270–300 | The photo dissolves into the 3D replica: signboard “ZIYO YOG’DUSI” XUSUSIY MAKTABI, grooved pillars, laser-cut gate, guard booth, canopy frame; through the gate the glass cafeteria glows warm | 18 mm + photo lens shift, forward 0.03 → 0.07 m/frame | Approved replica morning light | Hand-off path of `CAM_S02_START` |
| 2b | 300–358 | The camera glides toward the guard booth; the turnstile in the passage between gate and booth: one brushed-steel cabinet against the gate's end post, one glass wing, the Face ID terminal on a post at its entry end | level; 18 → 35 mm (330) → 85 mm, lens shift eases to 0 by 330; pans onto the display; exact eased stop at 358, 1.35 m from the terminal; DOF on (the cafeteria's warm lights become bokeh behind) | Morning light under the entrance soffit | Smooth deceleration |
| 2c | 362–391 | Scan: a horizontal scan line sweeps the lattice top → bottom; dots red, lighting as it passes; turnstile LEDs red | 85 mm, f/4, locked | Display; red spill on the bezel | Sweep ease-in-out |
| 2d | 391 | All dots turn green; a check glyph draws in; the cabinet's LED line and entry bar turn green | 85 mm | Green display + spill | — |
| 2e | 395–420 | The glass wing swings open (395–415, flat against the cabinet); the camera moves into the 0.64 m lane beside the booth and passes the wing line at 420 | 85 → 24 mm, back onto the lane axis; DOF off | Daylight | Wing: eased start, ≈1 % overshoot, settle |
| 2f | 420–470 | **Courtyard reveal:** a slow, calm glide past the booth into the courtyard; the modelled potted palms pass in the left foreground; ahead the cafeteria's glass wall — slim graphite frames, a glass double door on the old doorway axis, behind it long oak tables, benches, blue-and-white plates and warm pendant lamps | level, 24 mm; ≈ 2 m/s, a gentle 12° turn toward the glass | Morning courtyard; warm 2700 K pendants inside | Eased glide (no stops) |
| 2g | 460–509 | The camera tilts down to the paving in front of the glass and sinks into it — a smooth, accelerating dive (no sudden drop) — on into the slab under it | 24 mm, pitch level → straight down (460–503); S hold 503–509 | Colour settings switch to scene 3's while the camera is inside the solid deck (505) | Hermite ease into the constant S speed |

Per-frame clearance check in the build script: the camera never comes closer than **0.28 m** to any geometry (passing the booth's back corner, 440).

**Sound cues:** `docs/sound-cues.md` → Scene 2.

---

## Scene 3 — CCTV security (510–659, 5.0 s)

Concept (user decisions 2026-11-26, replace the former security-room board): a school corridor from the kit; three real surveillance cameras slide out, pan, then lock onto a soft glowing light point (no people); the wall security monitor shows their live feeds; the camera ends inside the dome camera's lens (C). Indoor CCTV in corridors and classrooms is real (user). Built by `blender/scripts/scene_03_cctv.py` → `blender/scenes/s03_cctv.blend`; feeds `renders/_cctv_feeds/`.

Frames below are FILM frames; in `s03_cctv.blend` (and the script/notes inside it) every number is 60 lower (film 510 = `.blend` 450).

**ENTRY:** S at 510 (slab above the corridor ceiling, 24 mm, looking straight down, 0.12 m/frame).
**EXIT:** C at 659 (inside the dome camera's lens).
**Atmosphere** (`docs/design-language.md` → Room atmospheres): morning · cool neutral (≈ 5600–6000 K), slightly dim, small blue status LEDs · cool light-grey walls, pale grey-washed floor · camera language: **vertical swoop + slow axial push** · mood: calm watchfulness. The only scene with CCTV cameras.

| KF | Frame | In frame | Camera / lens | Light | Motion |
|---|---|---|---|---|---|
| 3a | 510–530 | Slab → the camera drops through the ceiling into a warm-modern corridor (oak floor, white walls, oak doors, tile ceiling with downlights + LED slots, window at the far end) | 24 mm straight down, swoops into a forward glide; lens 24 → 35 mm by 544 | cool neutral, slightly dim (room light set in the scene file); slab isolation 510–513 | Descent bends into forward motion (no overshoot), tilt up to look down the corridor |
| 3b | 544–570 | Cameras appear: bullet L slides out of its wall housing on twin rails (544), the dome lowers from a ceiling hatch on a pendant rod (548), bullet R slides out (552). Security monitor (wall, right) shows their live feeds from 544 | 35 mm, slow forward dolly | same | Eased rail slides (smootherstep), staggered |
| 3c | 570–613 | Servo pans: LEFT 35° (570/572/574), pause 0.5 s, RIGHT 70° (595/597/599) | 35 mm; glance toward the monitor 576–628 | same | Quick start, smooth stop, tiny overshoot + settle |
| 3d | 610–648 | A soft glowing light point appears at the far end and travels down the corridor past the camera; cameras lock on (blue LEDs pulse brighter at 627/629/631) and track it | 35 mm | the point lights walls and floor as it passes | Locked Track (pan) + Damped Track (tilt) on lagged targets (3/5/7 frames) |
| 3e | 628–659 | The dome turns to face the camera; push forward-and-down into its multi-coated lens | 35 mm, DOF on the lens | lens coating reflections | Hermite ease into the constant C speed (0.01 m/frame) |

Cameras: dome = pendant turret (white ball in a shroud, black face plate, coated lens, LED); bullets = white housing tube, sun shield, bezel, coated lens with IR LED ring, yoke on a pan joint, carriage on twin steel rails out of a white wall housing. HUD (thin focus brackets) is optional and will be added in Remotion — nothing baked into the 3D render.

**Sound cues:** `docs/sound-cues.md` → Scene 3.

---

## Scene 4 — English class (660–869, 7.0 s)

**ENTRY:** C at 660 (the dark lens-pass frame opens like an iris onto the room 660–675; no camera in the classroom, no CCTV look).
**EXIT:** S at 809.
**Atmosphere** (`docs/design-language.md` → Room atmospheres): bright sunny morning · strong warm sun (≈ 5200 K), airy · warm white + teal · world map, open bookshelves, whiteboard + teacher's desk · camera language: **slow high crane** descending + airy lateral truck · mood: open, creative.

| KF | Frame | In frame | Camera / lens | Light | Motion |
|---|---|---|---|---|---|
| 4a | 660 | High corner view of a bright, airy classroom: warm white walls, teal accents, a world map, open bookshelves, whiteboard and teacher's desk at the front, desks in rows | 35 mm (C entry: darkness opens), slow high crane descending from the ceiling corner toward eye level | Bright sunny morning, warm sun 5200 K through the windows, airy bounce | Slow crane down and forward |
| 4b | 700 | Whiteboard: letters assemble out of small 3D tiles into English words (generic: "Hello", "Learn", "Future") | 35 mm, slow truck along the desks | Daylight + board spot | Tiles fly in on arcs and land with a small settle |
| 4c | 760 | On a desk, a closed textbook opens on its own, pages turn (page bend) | 85 mm, shallow DOF | Daylight | Pages turn with weight and settle |
| 4d | 810 | Globe on the shelf rotates; curtain moves softly in a breeze | 50 mm | Daylight, the curtain casts a moving shadow | Globe eases to a stop |
| 4e | 845–869 | Camera tilts down through the desk aisle to the floor → slab | → 24 mm, S | — | Ease into S |

**Sound cues**
- 660 — CCTV signal tone resolves into room ambience
- 700–730 — light wooden "tick" per tile landing (≈8 ticks; exact frames from the animation)
- 760 — book open thump; 772, 784 — page turns
- 810 — soft globe spin creak
- 850–869 — downward whoosh

---

## Scene 5 — Russian class (870–1019, 5.0 s)

Same classroom kit, different dressing and colour accent (deep blue + warm wood), different camera grammar (lateral moves instead of push-ins).

**ENTRY:** S at 810.
**EXIT:** W at 1019 (out through the window into the sky).
**Atmosphere** (`docs/design-language.md` → Room atmospheres): late morning · soft side light (≈ 5000 K) + warm desk lamp (≈ 2900 K) · deep burgundy accents, dark wood · classic literature shelves (unbranded spines, no real titles) · camera language: **low push-in** at desk height, long lenses, shallow DOF · mood: classic, literary.

| KF | Frame | In frame | Camera / lens | Light | Motion |
|---|---|---|---|---|---|
| 5a | 870 | Top-down onto a reading corner and dark-wood desks; burgundy accents | 24 mm → 50 mm | Soft late-morning side light 5000 K, warm desk lamp | Tilt to horizontal while dropping to desk height |
| 5b | 899 | Cyrillic alphabet chart; letters rotate into place one by one (3D tiles) | 50 mm, low push-in at desk height | Side light | Tiles rotate 180° into place with easing |
| 5c | 937 | Bookshelf of literature volumes (unbranded spines, no real titles); one book slides out and opens on a lectern | 85 mm, low slow push-in | Warm desk lamp 2900 K accent | Slide with friction, open, settle |
| 5d | 970 | Desk with notebook by the window; a fountain pen rolls and stops against a ruler | 100 mm macro-ish, shallow DOF | Lamp + strong window light | Rolling with deceleration, contact |
| 5e | 987–1019 | Rack focus to the window; the window swings open; the camera moves forward-and-down through it until the bright sky fills the frame | 35 mm, exposure ramps +1.5 EV | Daylight blooms | Ease into W speed |

**Sound cues**
- 899–928 — soft tile flips (≈6, frames from the animation)
- 937 — book slide (friction), 949 — book thump on the lectern
- 970 — pen roll, 980 — pen tap against the ruler
- 991 — window latch + hinge swing
- 999–1019 — outdoor air rush, birds rising

---

## Scene 6 — Football field (1020–1229, 7.0 s)

**ENTRY:** W at 1020 (from the sky, exposure settling).
**EXIT:** W at 1229 (through a facade window into the IT class).
**Atmosphere** (`docs/design-language.md` → Room atmospheres): midday · bright high sun (≈ 5600 K), short shadows, clear sky · saturated green turf · camera language: **aerial descent + low fast tracking** · mood: energy.

| KF | Frame | In frame | Camera / lens | Light | Motion |
|---|---|---|---|---|---|
| 6a | 1020 | Bright sky settles; below, a green artificial-turf pitch with white markings and goals, the school beside it: the real left building from the entrance photo (cream/beige, 3 storeys, brown roof edge), extended in the same style, slightly out of focus, with trees | 35 mm, looking 45° down, high (aerial descent) | Bright midday sun, short crisp shadows, clear sky | Descent eases out |
| 6b | 1064 | Low over the grass; mown stripes; a ball (unbranded panels) rests on the centre spot | 24 mm, low fast tracking shot | Sun backlight, grass translucency | Camera glides at grass height |
| 6c | 1108 | The ball starts rolling (pushed by a gust — no player), accelerates toward goal | 35 mm, tracking alongside | Same | Rolling physics, bounces off a small bump |
| 6d | 1160 | The ball hits the net; the net ripples and catches the ball | 50 mm, behind the goal | Same | Net ripple (GN / light cloth), ball drops and settles |
| 6e | 1186–1229 | Camera turns toward that building's facade and descends along it toward a ground-floor window until one pane fills the frame | 35 mm, forward-and-down | Sky reflection in the glass | Ease into W speed |

**Sound cues**
- 1020 — wind/air ambience swell; light birds
- 1108 — ball thump (gust start)
- 1125, 1141 — soft ball bounces on the turf
- 1160 — net swish; 1171 — ball drop on the ground
- 1160 — music accent (big hit)
- 1213–1229 — soft glass "whoom" as the camera reaches the pane

---

## Scene 7 — IT class (1230–1469, 8.0 s)

**ENTRY:** W at 1230 (through the window pane from outside).
**EXIT:** S at 1469.
**Atmosphere** (`docs/design-language.md` → Room atmospheres): early afternoon, blinds down · dark, blue/violet LED accents, glossy surfaces, screens as key light · camera language: **orbit** · mood: tech, mystery.

| KF | Frame | In frame | Camera / lens | Light | Motion |
|---|---|---|---|---|---|
| 7a | 1230 | Through the glass: rows of desks with monitors (all off); the sky reflection fades as the camera passes the pane | 35 mm, forward-and-down to desk height | Dark room (blinds down, thin daylight slits); blue/violet LED accents, glossy dark surfaces | Ease out of W speed |
| 7b | 1270 | Monitors switch on in a wave down the rows; generic invented IDE/UI on the screens | 35 mm, slow orbit around the end of a row | Screens become the key light | Wave of power-on, 2-frame stagger |
| 7c | 1330 | Close: keyboard keys depress by themselves in a typing rhythm; code appears on the screen | 85 mm, shallow DOF | Screen glow | Key travel with bottom-out and release |
| 7d | 1390 | A small educational robot kit (generic) on a desk assembles: parts slide and click together, LEDs light up | 50 mm, orbit 30° | Screen + robot LEDs | Assemble with settles |
| 7e | 1440–1469 | Tilt down → slab | → 24 mm, S | — | Ease into S |

**Sound cues**
- 1230 — glass pass whoosh tail, interior hush
- 1270–1300 — power-on chirps cascade (one per monitor row, frames from the animation)
- 1330–1380 — mechanical keyboard typing (sync to key presses)
- 1390–1420 — plastic clicks as robot parts lock (≈5)
- 1420 — robot "ready" chirp
- 1445–1469 — downward whoosh

---

## Scene 8 — Cafeteria, plov (1470–1709, 8.0 s)

**ENTRY:** S at 1470.
**EXIT:** H at 1709 (into the steam).
**Same building as scene 2:** the cafeteria's glass wall and interior come from `blender/scripts/kit_cafeteria.py` (`glass_wall()`, `interior()`, `materials()`), which scene 2 already shows from the courtyard (user, 2026-11-27: the cafeteria has a glass facade). Scene 8 builds the room from the same module, so the glass wall, frames, floor, tables, ceramics and pendant lamps match.
**Atmosphere** (`docs/design-language.md` → Room atmospheres): afternoon · warm golden light through a glass wall (≈ 3800–4200 K) · cream + terracotta, Uzbek blue-and-white ceramic accents (unbranded) · camera language: **top-down** bird's-eye glides, vertical descent into the steam · mood: home, hospitality.

| KF | Frame | In frame | Camera / lens | Light | Motion |
|---|---|---|---|---|---|
| 8a | 1470 | Top-down onto a clean, bright cafeteria: long tables, set places | 24 mm | Warm golden afternoon light through the glass wall; cream + terracotta, blue-and-white ceramics | Top-down glide along the tables |
| 8b | 1520 | Large kazan on the serving counter, lid on | 50 mm, top-down glide over the counter onto the kazan | Golden key on the kazan | Lid lifts and slides aside; steam billows (volume) |
| 8c | 1575 | Close on the plov: glossy rice, carrot strips, chickpeas, meat | 100 mm, shallow DOF, f/2 | Warm backlight through the steam | Steam drifts; slow rack focus |
| 8d | 1620 | A plate on the table receives the plov: rice grains cascade and settle into a mound, garnish lands | 50 mm, slight top angle | Warm | GN drop-and-settle; small bounce of grains |
| 8e | 1670–1709 | Camera rises over the kazan and descends straight down into the steam column until warm haze fills the frame | 35 mm, top-down | Steam lit warm 3200 K | Ease into H |

**Sound cues**
- 1470 — soft cafeteria room tone (no voices)
- 1520 — heavy metal lid lift; 1535 — lid set down clank
- 1520 — steam hiss swell
- 1620–1640 — rice pour / grain cascade
- 1642 — plate settle tap
- 1680–1709 — steam hiss rising into a soft airy whoosh

---

## Scene 9 — Dormitory (1710–1919, 7.0 s)

**ENTRY:** H at 1710 (warm haze resolves into the frosted ceiling-lamp glow).
**EXIT:** S at 1919 → handed to Remotion as the first frame of scene 10.
**Atmosphere** (`docs/design-language.md` → Room atmospheres): evening · warm lamps (≈ 2700–2900 K), deep blue window light · muted sage + beige, soft textiles · camera language: **slow lateral slide**, gentle drift · mood: cozy, safe.

| KF | Frame | In frame | Camera / lens | Light | Motion |
|---|---|---|---|---|---|
| 9a | 1710 | Lamp glow pulls into focus; the camera descends past the lamp; the tidy dorm room below: beds, desks, wardrobes | 35 mm, top-down → tilt to horizontal | Evening, warm 2800 K lamps, deep blue window light | Ease out of H |
| 9b | 1750 | A folded blanket on a bed unfolds and settles across the mattress | 35 mm | Warm lamps | Cloth sim: lift, unfold, drape, settle |
| 9c | 1810 | Pillow drops lightly into place; bedside lamp clicks on | 50 mm, shallow DOF | Lamp key turns on | Pillow compression is physical (shape key), no cartoon squash |
| 9d | 1860 | Window: curtains close gently; night sky outside | 35 mm, slow lateral slide to the window | Moonlight cool rim + warm interior | Curtain cloth |
| 9e | 1895–1919 | Tilt down → slab | → 24 mm, S | — | Ease into S |

**Sound cues**
- 1710 — warm low pad swell (music)
- 1750 — blanket fabric whoosh; 1780 — soft settle
- 1810 — pillow soft thump; 1822 — lamp switch click
- 1860 — curtain rings slide
- 1900–1919 — deep downward whoosh (bigger, builds into the rewind)

---

## Scene 10 — Rewind (1920–2069, 5.0 s) — Remotion

Pending decision Q1 in `docs/production-plan.md`. Proposal below.

**ENTRY:** 1920 = slab frame identical to the scene 9 exit (Remotion shows the rendered S frame).
**EXIT:** 2069 = scene 1's first frame (website glow), shrinking to a point of light at the centre of scene 11's wordmark (transition L).

| KF | Frame | In frame | Motion |
|---|---|---|---|
| 10a | 1920 | Slab frame (from the scene 9 exit) | Transition P: the frame shrinks into one cell of a vertical film strip |
| 10b | 1950 | The full strip: scenes 1–9 as stacked frames with thin separators, each playing its footage in reverse | The strip scrolls **upward** past a fixed camera (the camera never goes up), accelerating |
| 10c | 2010 | Strip at peak speed; motion-blurred frames | Speed-ramp peak |
| 10d | 2050 | The strip decelerates and stops on scene 1's frame (monitor glow) | Ease out |
| 10e | 2069 | Scene 1's frame shrinks to a point of light | Transition L |

**Sound cues**
- 1920 — tape/vinyl rewind "zip" start, pitch rising to 2010
- 2010 — music build peak
- 2050 — brake/stop thud
- 2060–2069 — reverse-reverb swell into the reveal

---

## Scene 11 — Brand reveal (2070–2249, 6.0 s)

**ENTRY:** L at 2070 — point of light at the frame centre (matches 10e).
**EXIT:** 2249 — final frame, wordmark held; fade to black 2235–2249.

Built as a Blender light/background plate + the wordmark composited in Remotion. **No symbol or emblem.** An optional logo slot (`src/brand.ts` → `logoFile`, currently `null`) sits above the wordmark; when it is empty, the wordmark is centred and the layout is complete without it.

| KF | Frame | In frame | Camera / lens | Light | Motion |
|---|---|---|---|---|---|
| 11a | 2070 | Point of light on a deep dark background | 50 mm, locked | Single warm light | The light blooms into a soft horizontal glow |
| 11b | 2100 | The wordmark **ZIYO YOG’DUSI** (U+2019, font verified) resolves out of the glow, letters stepping in left → right | Locked, very slow push-in (scale 1.00 → 1.03) | Warm key + soft rim | Per-letter opacity/tracking ease-in, no bounce |
| 11c | 2150 | Full wordmark; a light sweep passes across the letters | Locked | Light sweep | Sweep ease-in-out |
| 11d | 2200 | Hold | Locked | — | Still |
| 11e | 2235–2249 | Fade to black | — | — | — |

If a logo is added later: it fades/scales in above the wordmark at 2100–2130 and the wordmark follows at 2130; all frame numbers stay inside this scene.

**Sound cues**
- 2070 — soft shimmer
- 2100–2140 — subtle airy "letter" ticks (one per letter group)
- 2150 — brand chime (final musical accent)
- 2249 — music end (tail cut/fade to fit)
