# Status

States: **not started** · **in progress** · **review** · **approved**

## Pre-production

| Item | State | Notes |
|---|---|---|
| Environment audit | approved | EEVEE 14.1 s/frame, Cycles CPU 56.3 s/frame @1080p (simple scene) |
| CLAUDE.md rulebook | review | 2026-11-26: brand apostrophe → ’ U+2019 (as on the real sign); text rule extended to the one real signboard; real reference photo + entrance replica; transition 1→2 = photo-to-3D dissolve. Earlier the same day: lens rule added (24/35/50 standard; 18 wide, 85/100 close-up; nothing outside 18–100 mm) — enforced in `_common.set_lens()` |
| Production plan | review | Open questions Q1–Q4 in `docs/production-plan.md` |
| Storyboard | review | |
| Initial git commit | blocked | Git user.name / user.email still not found in any git config (re-checked after the skeleton step) |
| Project skeleton | review | Folders, `src/timeline.ts`, `<SceneSequence>`, `ZiyoCommercial` (2250 f, 30 fps), `SoundLayer` + `src/soundCues.ts` (empty), npm scripts, `blender/scripts/_common.py`, `blender/timeline.json`. Verified: composition 1920×1080 / 3840×2160 with `REMOTION_FINAL=1`; placeholders show correct names and frame ranges; image-sequence playback tested with dummy frames; `_common.py` self-test passes in Blender 5.3 |

## Scenes

| # | Scene | Frames | State | Notes |
|---|---|---|---|---|
| — | Design language | approved | **A — Warm modern** = shared shell (window frames, doors, ceiling system). **Room atmospheres** (2026-11-26): every room its own palette, light, furniture, props and camera language, one school day morning → evening; CCTV only in scene 3 (exception: real entrance camera). Table in `docs/design-language.md` |
| — | Shared kit `blender/kit/school_kit.blend` (`build_kit.py`) v2 | **approved** (2026-11-26, step 3) | style A only; real lights under every fixture; school desk/chair/monitor/LED accent; exterior backdrop + HDRI; irradiance-volume bake; renders `renders/_kit/v2/`. v2 review notes recorded in `docs/design-language.md` and applied to the kit: lacquered floor gloss, `tech_dark` exposure 0.4 → 0.7 + brighter neutral fill, backdrop trees with leaf clusters + leaf cards, backdrop buildings with recessed framed windows and three plaster tones. `outdoor_day` now uses a procedural physical sky (no HDRI trees in the sky) synced to the sun lamp |
| — | Floor slab `PIECE_slab` (`kit_slab.py`) | review | 6 × 6 m, 1.2 m thick: concrete decks, sealed 0.9 m cavity with ribs, 2 cable trays + cables, round duct, 4000 K LED strips (own light, not preset-driven); `slab_HANDOFF` at −0.61. Test `kit_slab_test.py`: cut frame renders **identically (0/255 diff)** under `day_interior` and `tech_dark` when scenes use `C.key_slab_isolation()` (EEVEE leaks world light into the cavity otherwise: +24 %). Renders `renders/_kit/slab/` |
| — | School building exterior `PIECE_school_building` + `PIECE_school_grounds` (`kit_building.py`) | **superseded** (2026-11-26) | Not used in the film. Stadium background (scene 6) = the real left building, extended in the same style (user decision 2026-11-26). Code kept; its tree generator is reused for scene 6 |
| — | Website hero image — real entrance photo, sky replaced (`tools/hero_sky.py`) v2 | **approved** (2026-11-26) | **Approved file: `assets/hero/entrance_hero_1920.png`** (committed; byte-identical to the master `renders/_hero/entrance_hero_1920.png`, md5 7b163457…). It is the scene 1 website hero image and the photo projected onto the replica for the 1→2 hand-off (`build_entrance.py` reads it from `assets/hero/`). Source `assets/reference/entrance_front.jpg`; Lanczos upscale 1280 → 1920 px (no AI, no invented detail — fine detail stays soft at 1920). Colour-unmixing matte; procedural clear morning sky with a few soft clouds; slight spill/cool grade. **Signboard bit-identical to the upscaled original (max diff 0)**; buildings, gate, booth unchanged except the grade. Re-running `tools/hero_sky.py` needs a new decision; its output goes to `renders/_hero/` and must be copied to `assets/hero/` |
| — | 3D entrance replica `blender/kit/entrance.blend` (`build_entrance.py`) v2 | **approved** (2026-11-26) | Photo-matched: every element back-projected from measured photo pixels through the solved camera (f ≈ 545 px = 15.3 mm, principal point (681, 478), level, height 1.40 m ASSUMED → facade 8.48 m). v2: weathered plaster, frosted/etched booth glass, left boundary wall as photographed (rounded-top openings, downpipe, shutter doorway), canopy pole and facade cables, view through the gate, the photographed golden tree (branching skeleton + leaf cards), low morning sun, sign glow (compositor glare), scene-2 opening move and the photo-projection hand-off layer (`ENTRANCE_PROJ`; composited by `tools/composite_handoff.py` now, by Remotion in the assembly). Renders `renders/_entrance/entrance_match_960_v2.png`, `handoff_strip_960.png`, `handoff_alpha_strip.png`. Sign text from `common/brand.py` in Montserrat Bold. Invented (not visible in the photo, neutral): building depths/roofs behind the visible faces, courtyard layout beyond the gate (incl. carved wooden pointed-arch double door, potted palms), AC units only where the photo cannot see, gate-pattern exact motif, booth interior |
| 1 | Website — "Digital website universe" | 0–269 | **approved** (2026-11-26, draft preview 960×540) | Decisions (2026-11-26): real photo hero, dive into the photo (D), new void concept (storyboard rewritten). **Websites** (Remotion, `src/website/`): 6 invented sites (Horizon Trails travel, Oakline store, The Daily Meridian news, Pulse fitness, Ledgerly bank-like dashboard, portfolio) + the school site (wordmark only, Uzbek nav, facts only, real hero photo); `npm run website:render` → `renders/_website/` → `tools/build_website_strip.py` → `blender/kit/textures/website_strip.png` (1920×7560). School page sequence 190–269 (hover, click + ripple, UI fade); frame 269 = the approved photo pixel-identical. **Blender** `blender/scripts/scene_01_website.py` → `blender/scenes/s01_website.blend`: floating tilted display (bevelled aluminium, black border, Fresnel glass), void + noise haze, teal/amber rims, top shaft, screen spill; strip = real moving plane (3 passes of the 6 sites, shader-masked by the screen); Bezier scroll 14 → peak 0.30 pages/frame at 102 → exact stop 190. **Motion blur is in the strip shader** (16 jittered taps over the 180° shutter travel, keyed per frame from the scroll F-curve): EEVEE motion blur double-exposed the masked plane and leaked it outside the screen, so it is off. Camera 35 mm, f/4; dive distance from `s01PhotoScale` (`diveStartScale` raised 0.46 → 0.60 so the click is readable). View transform **Standard** in this scene so the screen reproduces page pixels exactly (D hand-off). Preview `renders/01_website_preview/` → `public/renders/s01_website/`. Sound cues: `docs/sound-cues.md`. Inspection: CLI renders + MCP `look` (frames 8, 120, 190, 215, 246, 269 — no problems; the look tool tiles at ~4:3, so 246/269 show more height than the 16:9 camera) |
| 2 | Turnstile with Face ID | 270–449 | not started | starts on the 3D entrance replica (D dissolve), through the gate to the turnstile; abstract dot-lattice scan UI only. Timing note: the entrance approach now shares 6 s with the Face ID scan — may need frames from another scene (your decision when scene 2 is boarded) |
| 3 | CCTV security | 450–599 | **review** (draft preview 2026-11-26) | Decisions (2026-11-26): corridor + security monitor concept (storyboard rewritten); indoor CCTV in corridors and classrooms is real, but **CCTV is shown only in scene 3** (rule 2026-11-26); **3 → 4 = C lens pass** (scene 4 opens from the lens darkness with no camera in the room) (replaces F; `_common.HANDOFF_TYPES["C"]`, storyboard + scene 4 ENTRY updated). `blender/scripts/scene_03_cctv.py` → `blender/scenes/s03_cctv.blend`: 18 m kit corridor (walls, doors, skirting, floor, ceiling panels with real downlights/LED slots, far-end window, `day_interior`), slab above the entry (`C.key_handoff` ENTRY S, isolation 450–453), probes baked. 3 cameras: pendant turret dome (ceiling hatch + rod) and 2 bullets (white housing on twin rails, sun shield, yoke, IR LED ring), multi-coated lenses (thin-film green/purple), blue status LEDs. **Room atmosphere** (2026-11-26): cool neutral 5800 K, slightly dim, cool light-grey walls, pale grey-washed floor (copies of the kit materials in this file only; shell unchanged). Animation: eased rail slides 484/488/492, servo pans LEFT 35° → pause → RIGHT 70° (quick start, overshoot + settle), then Locked/Damped Track on lagged targets (3/5/7 frames) following a glowing light point (no people); blue LEDs pulse brighter on lock-on. Security monitor shows the 3 live feeds (pre-rendered from the cameras: `renders/_cctv_feeds/`, 480×270, no text). EXIT C: 12 mm inside the dome front element (`EXIT_ANCHOR_C`). Lens 24 → 35 mm. Inspected with MCP `look` (fixed: crane overshoot through the floor, stale `matrix_world` for slab/anchors, monitor facing the wall, glance pitch sign). Preview `renders/03_cctv_preview/` → `public/renders/s03_cctv/` (150 frames). Open: scene 2 (not built) must end on the same slab placement; HUD brackets later in Remotion |
| 4 | English class | 600–809 | not started | |
| 5 | Russian class | 810–989 | not started | |
| 6 | Football field | 990–1229 | not started | |
| 7 | IT class | 1230–1469 | not started | |
| 8 | Cafeteria — plov | 1470–1709 | not started | |
| 9 | Dormitory | 1710–1919 | not started | |
| 10 | Rewind | 1920–2069 | not started | depends on Q1 |
| 11 | Brand reveal | 2070–2249 | not started | wordmark only; logo slot empty |
| — | Remotion assembly + timeline | 0–2249 | not started | |
| — | Sound (SFX + music edit) | 0–2249 | not started | needs music file |

## Assets from you

| Asset | State |
|---|---|
| Official logo (`assets/brand/`) | does not exist yet — not blocking (wordmark only) |
| Fonts | **Montserrat Bold** (SIL OFL 1.1, licence `assets/fonts/OFL-Montserrat.txt`) used for the signboard replica. Glyph check (fontTools cmap, 2026-11-26): A B D G I K M O S T U X Y Z, ’ U+2019, “ U+201C, ” U+201D — **all present natively, none missing**. Wordmark font for scenes 1/11: **Montserrat Bold** (website header). Scene-1 websites also use Montserrat (variable), Inter, Playfair Display, Space Grotesk — all SIL OFL 1.1, licences in `assets/fonts/<family>/`. `tools/check_website_glyphs.py` (2026-11-26): 102 characters (printable ASCII + · – — ’ “ ” −) checked in all 5 fonts — **none missing** (● U+25CF was replaced by drawn dots) |
| Reference photos | `assets/reference/entrance_front.jpg` (real entrance, 2026-11-26). More photos welcome (other sides, courtyard, turnstile area) |
| Design-language choice | done — A (Warm modern) |
| Real building details | from the entrance photo — recorded in CLAUDE.md → DESIGN LANGUAGE. A real dimension (gate height or pillar width) would fix the camera-solve scale |
| Licensed instrumental music (`assets/audio/music/`) | missing |
| Facility confirmation | missing |

## Placeholders in use

None yet. Every placeholder will be listed here (magenta "PLACEHOLDER" label in frame).

## Tools

- `tools/py.sh` runs Blender's bundled Python with project-local Pillow / SciPy / fontTools from `tools/pydeps/` (git-ignored). Setup once: `"<Blender>/5.3/python/bin/python.exe" -m pip install --target tools/pydeps pillow scipy fonttools`.
- `npm run website:render` (scene-1 pages + school sequence), `tools/build_website_strip.py` (strip texture), `tools/check_website_glyphs.py` (font coverage).
- `tools/hero_sky.py` (hero sky replacement), `tools/gate_pattern.py` (laser-cut pattern masks → `assets/textures/`), `tools/overlay_match.py` (camera-match overlay).
