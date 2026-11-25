# Storyboard — ZIYO YOGʻDUSI commercial

30 fps · frames are absolute film frames (0–2249). No people, no voice, no subtitles.
Lens values are full-frame equivalent (36 mm sensor). "KF" = key frame.
Sound cues listed here are copied into `docs/sound-cues.md` once frames are locked; all SFX are made with ElevenLabs `text_to_sound_effects` into `assets/audio/sfx/`. Music: your licensed instrumental track (`assets/audio/music/`), edited to hit the marked accents.

---

## Transitions

The floor-slab pass is the default; six transition types are used in total. Every transition moves the camera downward (or forward-and-down) and has a matched EXIT/ENTRY definition. Camera paths on both sides of every cut come from one shared module (`blender/scripts/common/camera_handoff.py`).

| Cut | Frame (exit → entry) | Type | Motivation |
|---|---|---|---|
| 1 → 2 | 269 → 270 | **G — Screen-glass pass** | Camera dives through the monitor glass into its pixel grid and emerges through the glass of the Face ID terminal display |
| 2 → 3 | 449 → 450 | **S — Floor-slab pass** (default) | — |
| 3 → 4 | 599 → 600 | **F — CCTV feed match** | Camera pushes into a CCTV feed showing the English classroom from a high angle; the feed becomes the real 3D room |
| 4 → 5 | 809 → 810 | **S — Floor-slab pass** | — |
| 5 → 6 | 989 → 990 | **W — Window / sky pass** | Camera passes through the classroom window; the bright sky fills the frame; the cut is on matched sky; descent toward the stadium |
| 6 → 7 | 1229 → 1230 | **W — Window pass (facade)** | Camera descends along the school's glazed facade beside the field and passes through a window into the IT class |
| 7 → 8 | 1469 → 1470 | **S — Floor-slab pass** | — |
| 8 → 9 | 1709 → 1710 | **H — Haze match** | Camera descends into the plov steam; warm white haze fills the frame; it resolves into the glow of the dormitory's frosted ceiling lamp |
| 9 → 10 | 1919 → 1920 | **S → P — Slab, then film-strip pull-back** (Remotion) | The slab frame shrinks into one cell of the vertical film strip |
| 10 → 11 | 2069 → 2070 | **L — Point-of-light** | The last strip frame collapses to a point of light that blooms into the wordmark |

### S — Floor-slab pass (default)
Shared slab kit (`blender/kit/slab`, 1.2 m thick: concrete, cable trays, warm LED strips). The cut sits at the slab midpoint.

| Property | EXIT (last frame of N) = ENTRY (first frame of N+1) |
|---|---|
| Position | empty `HANDOFF` at slab midpoint; X/Y = 0 in handoff space |
| Rotation | looking straight down (−Z), roll 0°, image "up" = scene +Y |
| Focal length | 24 mm, DOF off during the pass |
| Motion | descending 0.12 m/frame (3.6 m/s), constant ±6 frames around the cut; ENTRY = EXIT pose advanced one frame |
| Light | slab interior only: warm-white LED strips 4000 K |

### G — Screen-glass pass (1 → 2)
| Property | EXIT 269 | ENTRY 270 |
|---|---|---|
| Frame content | macro of the monitor's RGB subpixel grid, emissive, filling the frame | the same subpixel grid (identical texture and scale) on the Face ID terminal display |
| Rotation | looking along the screen normal, tilted 30° downward (screen leans back) | the terminal display also leans back 30°, so the camera continues forward-and-down |
| Focal length | 50 mm, DOF off | 50 mm |
| Motion | forward-and-down 0.03 m/frame, constant ±6 frames | same |
| Light | subpixels emit cool 6500 K white | same |

### F — CCTV feed match (3 → 4)
| Property | EXIT 599 | ENTRY 600 |
|---|---|---|
| Frame content | the CCTV feed (rendered from the English-class set) fills the frame; overlay fully faded out by 595 | the 3D English classroom from the same CCTV angle |
| Camera | the feed's virtual CCTV camera: ceiling corner, 2.8 m height, looking down 35°, 18 mm | identical |
| Motion | descending + forward 0.02 m/frame | same; the "feed" look (slight barrel distortion and grade) dissolves to the clean film look over 600–615 |
| Light | English class daylight 5200 K | same |

### W — Window / sky pass (5 → 6, 6 → 7)
- **5 → 6:** EXIT 989: the camera has passed through the open classroom window; the frame is filled by bright sky (the same HDRI as scene 6, overexposed +1.5 EV at the cut), looking 45° down, 35 mm, moving forward-and-down 0.10 m/frame. ENTRY 990: the same sky and exposure; exposure eases back to 0 EV over 990–1010, revealing the stadium below.
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

## Scene 1 — Website (0–269, 9.0 s)

**ENTRY:** film start. Black → fade up from frame 0–12.
**EXIT:** G at frame 269 (into the monitor's subpixel grid).

The website header shows the wordmark **ZIYO YOGʻDUSI** (U+02BB, same verified font as scene 11), with no symbol or icon. An optional logo slot left of the wordmark stays empty while `logoFile` is `null`.

| KF | Frame | In frame | Camera / lens | Light | Motion |
|---|---|---|---|---|---|
| 1a | 0 | Dark, calm study desk; a slim unbranded monitor, the screen glowing with the invented school website hero page | Front, eye level, 50 mm, slow dolly in; shallow DOF (f/2.8) on the screen | Moody: the screen is the key light (cool 6500 K), faint warm practical lamp behind | Fade up; the website hero shows a rendered image of the school building exterior (from the Blender kit) with a slow parallax |
| 1b | 75 | Screen fills ~70 % of the frame; cursor (no hand) glides over menu items, opens an "Admissions"-type page — generic labels, no numbers or claims | 50 → 65 mm push-in | Same | Smooth UI scroll, buttons respond |
| 1c | 140 | The page flips into its source-code view: lines of code scroll | 85 mm, close on the screen | Screen shifts cyan → warm amber | Code lines start to glow hot |
| 1d | 190 | Code lines detach from the glass and melt into thick glossy amber liquid, flowing down the screen and over the bezel | 50 mm, slight tilt down | Liquid slightly emissive, lights the desk | Liquid drips with weight (accelerating fall, stretching, bead-off) |
| 1e | 235–269 | As the liquid drains, the screen behind it glows clean white; the camera pushes forward-and-down into the glass until the RGB subpixel grid fills the frame | 50 mm, DOF off by 255 | The screen is the only light | Ease into G speed |

**Sound cues**
- 0 — music start (soft intro)
- 75 — soft UI click
- 104 — second UI click + page swipe whoosh
- 140 — digital "code reveal" shimmer
- 190 — low sizzle/hum as the code heats; liquid stretch
- 215, 228, 241 — three thick liquid drip "plops" (sync to drip contacts)
- 250–269 — rising electric "glass dive" whoosh

---

## Scene 2 — Turnstile with Face ID (270–449, 6.0 s)

**ENTRY:** G at 270 (out of the Face ID terminal display glass).
**EXIT:** S at 449.

**Face ID UI rule:** the terminal display shows only an abstract **dot/mesh grid** — a rounded-square lattice of points (about 20 × 20) joined by thin triangulated lines, gently undulating like a surface. There is **no face, head, silhouette or body shape**: no oval outline, no eyes, nose, mouth or shoulders. No text on the scan UI (colour and generic glyphs only).

| KF | Frame | In frame | Camera / lens | Light | Motion |
|---|---|---|---|---|---|
| 2a | 270 | Emerging from the terminal display: the subpixel grid widens into the scan UI — the abstract dot lattice in dim blue | 50 mm, moving forward-and-down through the glass, then easing back to a steady position in front of the terminal | Display glow, cool 6500 K | Ease out of G speed |
| 2b | 300 | The full Face ID terminal on its stand beside a row of modern glass-wing turnstiles in a bright entrance hall | 35 mm, camera descends and arcs 20° around the terminal | Morning daylight through tall windows (5600 K), soft shadows | Slow arc |
| 2c | 325–355 | Scan: a horizontal scan line sweeps the lattice top → bottom; dots light up in sequence (blue → white) as the line passes; mesh lines brighten | 85 mm, close on the display, shallow DOF | Display + daylight | Sweep with ease-in-out; dots light in a wave |
| 2d | 360 | All dots settle to green; a generic check glyph fades in at the centre of the lattice | 85 mm | Display turns green; green spill on the terminal bezel | Green pulse |
| 2e | 370–420 | Glass wings open smoothly (rotate into place); the path ahead is clear | 35 mm, camera dollies through the opened gate | Daylight | Wings: accelerate, decelerate, tiny settle overshoot |
| 2f | 425–449 | Past the gate, camera tilts down to the polished floor; floor seam → slab | → 24 mm, top-down, S | Daylight fades into slab LEDs | Ease into S |

**Sound cues**
- 270 — glass-dive whoosh tail
- 325 — soft scanning hum (sweep 325–355)
- 340–355 — tiny digital ticks as the dots light (subtle, in groups)
- 360 — two-tone confirmation beep (existing draft SFX, to be regenerated into `assets/audio/sfx/`)
- 370 — soft motor whir of the glass wings opening
- 405 — gentle mechanical "settle" click
- 430–449 — downward whoosh

---

## Scene 3 — CCTV (450–599, 5.0 s)

**ENTRY:** S at 450 (security room ceiling).
**EXIT:** F at 599 (into the English-class feed).

| KF | Frame | In frame | Camera / lens | Light | Motion |
|---|---|---|---|---|---|
| 3a | 450 | Top-down onto a calm, dim security room: desk with keyboard, wall of monitors | 24 mm | Low ambient, monitors as key (cool 7000 K) | Tilt to horizontal while descending |
| 3b | 480 | Monitor wall: 3×3 feeds of empty school spaces (corridor, entrance, field, classrooms) with a generic CCTV overlay (REC dot, camera IDs "CAM 01"…, running time code without date) | 40 mm, slow push-in | Monitor glow | Feeds show subtle motion (light shift, door closing, curtain moving) |
| 3c | 515 | A ceiling CCTV dome camera (real 3D) in the room rotates toward the lens | 85 mm, close | Rim light on the dome | Dome pans with mechanical ease, small stop |
| 3d | 545 | Push toward the centre feed: the English classroom seen from a high corner | 40 → 70 mm push | Monitor glow | Feed grows to fill the frame |
| 3e | 575–599 | The feed fills the frame; overlay fades out by 595; ready for F | Matches the feed camera (18 mm equivalent) | English-class daylight | Ease into F motion |

**Sound cues**
- 450 — low electronic room tone fade in
- 480 — soft monitor-wall power "tick" cascade (9 quick ticks, 480–492)
- 515 — servo whir of the dome camera, stop click at 533
- 545 — digital zoom "blip"
- 590–599 — soft "signal lock" tone into the room

---

## Scene 4 — English class (600–809, 7.0 s)

**ENTRY:** F at 600 (from the CCTV angle; the feed look dissolves 600–615).
**EXIT:** S at 809.

| KF | Frame | In frame | Camera / lens | Light | Motion |
|---|---|---|---|---|---|
| 4a | 600 | High corner view of a bright modern classroom, desks in rows | 18 mm, descending from the ceiling corner toward eye level | Warm daylight 5200 K through windows, soft AO | Crane down and forward, lens eases 18 → 35 mm by 640 |
| 4b | 640 | Whiteboard: letters assemble out of small 3D tiles into English words (generic: "Hello", "Learn", "Future") | 35 mm, slow truck along the desks | Daylight + board spot | Tiles fly in on arcs and land with a small settle |
| 4c | 700 | On a desk, a closed textbook opens on its own, pages turn (page bend) | 85 mm, shallow DOF | Daylight | Pages turn with weight and settle |
| 4d | 750 | Globe on the shelf rotates; curtain moves softly in a breeze | 50 mm | Daylight, the curtain casts a moving shadow | Globe eases to a stop |
| 4e | 785–809 | Camera tilts down through the desk aisle to the floor → slab | → 24 mm, S | — | Ease into S |

**Sound cues**
- 600 — CCTV signal tone resolves into room ambience
- 640–670 — light wooden "tick" per tile landing (≈8 ticks; exact frames from the animation)
- 700 — book open thump; 712, 724 — page turns
- 750 — soft globe spin creak
- 790–809 — downward whoosh

---

## Scene 5 — Russian class (810–989, 6.0 s)

Same classroom kit, different dressing and colour accent (deep blue + warm wood), different camera grammar (lateral moves instead of push-ins).

**ENTRY:** S at 810.
**EXIT:** W at 989 (out through the window into the sky).

| KF | Frame | In frame | Camera / lens | Light | Motion |
|---|---|---|---|---|---|
| 5a | 810 | Top-down onto a reading corner and desks | 24 mm | Late-morning daylight 5000 K | Tilt to horizontal |
| 5b | 845 | Cyrillic alphabet chart; letters rotate into place one by one (3D tiles) | 50 mm, lateral slide right | Daylight | Tiles rotate 180° into place with easing |
| 5c | 890 | Bookshelf of literature volumes (unbranded spines, no real titles); one book slides out and opens on a lectern | 65 mm | Warm reading lamp 3000 K accent | Slide with friction, open, settle |
| 5d | 930 | Desk with notebook by the window; a fountain pen rolls and stops against a ruler | 100 mm macro-ish, shallow DOF | Lamp + strong window light | Rolling with deceleration, contact |
| 5e | 950–989 | Rack focus to the window; the window swings open; the camera moves forward-and-down through it until the bright sky fills the frame | 35 mm, exposure ramps +1.5 EV | Daylight blooms | Ease into W speed |

**Sound cues**
- 845–880 — soft tile flips (≈6, frames from the animation)
- 890 — book slide (friction), 905 — book thump on the lectern
- 930 — pen roll, 942 — pen tap against the ruler
- 955 — window latch + hinge swing
- 965–989 — outdoor air rush, birds rising

---

## Scene 6 — Football field (990–1229, 8.0 s)

**ENTRY:** W at 990 (from the sky, exposure settling).
**EXIT:** W at 1229 (through a facade window into the IT class).

| KF | Frame | In frame | Camera / lens | Light | Motion |
|---|---|---|---|---|---|
| 6a | 990 | Bright sky settles; below, a green artificial-turf pitch with white markings and goals, the school building exterior (same kit model as the scene 1 hero image) along one side | 35 mm, looking 45° down, high | Clear afternoon sun (HDRI), long soft shadows | Descent eases out |
| 6b | 1040 | Low over the grass; mown stripes; a ball (unbranded panels) rests on the centre spot | 28 mm, low tracking shot | Sun backlight, grass translucency | Camera glides at grass height |
| 6c | 1090 | The ball starts rolling (pushed by a gust — no player), accelerates toward goal | 35 mm, tracking alongside | Same | Rolling physics, bounces off a small bump |
| 6d | 1150 | The ball hits the net; the net ripples and catches the ball | 50 mm, behind the goal | Same | Net ripple (GN / light cloth), ball drops and settles |
| 6e | 1180–1229 | Camera turns toward the school's glazed facade and descends along it toward a ground-floor window until one pane fills the frame | 35 mm, forward-and-down | Sky reflection in the glass | Ease into W speed |

**Sound cues**
- 990 — wind/air ambience swell; light birds
- 1090 — ball thump (gust start)
- 1110, 1128 — soft ball bounces on the turf
- 1150 — net swish; 1162 — ball drop on the ground
- 1150 — music accent (big hit)
- 1210–1229 — soft glass "whoom" as the camera reaches the pane

---

## Scene 7 — IT class (1230–1469, 8.0 s)

**ENTRY:** W at 1230 (through the window pane from outside).
**EXIT:** S at 1469.

| KF | Frame | In frame | Camera / lens | Light | Motion |
|---|---|---|---|---|---|
| 7a | 1230 | Through the glass: rows of desks with monitors (all off); the sky reflection fades as the camera passes the pane | 35 mm, forward-and-down to desk height | Daylight from the windows, dim interior 6500 K | Ease out of W speed |
| 7b | 1270 | Monitors switch on in a wave down the rows; generic invented IDE/UI on the screens | 35 mm, slow dolly along a row | Screens become the key light | Wave of power-on, 2-frame stagger |
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

| KF | Frame | In frame | Camera / lens | Light | Motion |
|---|---|---|---|---|---|
| 8a | 1470 | Top-down onto a clean, bright cafeteria: long tables, set places | 24 mm | Warm 4000 K pendant lights + daylight | Tilt to horizontal |
| 8b | 1520 | Large kazan on the serving counter, lid on | 50 mm, slow push-in | Warm key on the kazan | Lid lifts and slides aside; steam billows (volume) |
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

| KF | Frame | In frame | Camera / lens | Light | Motion |
|---|---|---|---|---|---|
| 9a | 1710 | Lamp glow pulls into focus; the camera descends past the lamp; the tidy dorm room below: beds, desks, wardrobes | 35 mm, top-down → tilt to horizontal | Evening, warm 2800 K lamps, deep blue window light | Ease out of H |
| 9b | 1750 | A folded blanket on a bed unfolds and settles across the mattress | 35 mm | Warm lamps | Cloth sim: lift, unfold, drape, settle |
| 9c | 1810 | Pillow drops lightly into place; bedside lamp clicks on | 50 mm, shallow DOF | Lamp key turns on | Pillow compression is physical (shape key), no cartoon squash |
| 9d | 1860 | Window: curtains close gently; night sky outside | 35 mm, slow push to the window | Moonlight cool rim + warm interior | Curtain cloth |
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
| 11b | 2100 | The wordmark **ZIYO YOGʻDUSI** (U+02BB, font verified) resolves out of the glow, letters stepping in left → right | Locked, very slow push-in (scale 1.00 → 1.03) | Warm key + soft rim | Per-letter opacity/tracking ease-in, no bounce |
| 11c | 2150 | Full wordmark; a light sweep passes across the letters | Locked | Light sweep | Sweep ease-in-out |
| 11d | 2200 | Hold | Locked | — | Still |
| 11e | 2235–2249 | Fade to black | — | — | — |

If a logo is added later: it fades/scales in above the wordmark at 2100–2130 and the wordmark follows at 2130; all frame numbers stay inside this scene.

**Sound cues**
- 2070 — soft shimmer
- 2100–2140 — subtle airy "letter" ticks (one per letter group)
- 2150 — brand chime (final musical accent)
- 2249 — music end (tail cut/fade to fit)
