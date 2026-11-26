# Status

States: **not started** · **in progress** · **review** · **approved**

## Pre-production

| Item | State | Notes |
|---|---|---|
| Environment audit | approved | EEVEE 14.1 s/frame, Cycles CPU 56.3 s/frame @1080p (simple scene) |
| CLAUDE.md rulebook | review | 2026-11-26: lens rule added (24/35/50 standard; 18 wide, 85/100 close-up; nothing outside 18–100 mm) — enforced in `_common.set_lens()` |
| Production plan | review | Open questions Q1–Q4 in `docs/production-plan.md` |
| Storyboard | review | |
| Initial git commit | blocked | Git user.name / user.email still not found in any git config (re-checked after the skeleton step) |
| Project skeleton | review | Folders, `src/timeline.ts`, `<SceneSequence>`, `ZiyoCommercial` (2250 f, 30 fps), `SoundLayer` + `src/soundCues.ts` (empty), npm scripts, `blender/scripts/_common.py`, `blender/timeline.json`. Verified: composition 1920×1080 / 3840×2160 with `REMOTION_FINAL=1`; placeholders show correct names and frame ranges; image-sequence playback tested with dummy frames; `_common.py` self-test passes in Blender 5.3 |

## Scenes

| # | Scene | Frames | State | Notes |
|---|---|---|---|---|
| — | Design language | approved | **A — Warm modern**, fixed (`docs/design-language.md`) |
| — | Shared kit `blender/kit/school_kit.blend` (`build_kit.py`) v2 | **approved** (2026-11-26, step 3) | style A only; real lights under every fixture; school desk/chair/monitor/LED accent; exterior backdrop + HDRI; irradiance-volume bake; renders `renders/_kit/v2/`. v2 review notes recorded in `docs/design-language.md` and applied to the kit: lacquered floor gloss, `tech_dark` exposure 0.4 → 0.7 + brighter neutral fill, backdrop trees with leaf clusters + leaf cards, backdrop buildings with recessed framed windows and three plaster tones. `outdoor_day` now uses a procedural physical sky (no HDRI trees in the sky) synced to the sun lamp |
| — | Floor slab `PIECE_slab` (`kit_slab.py`) | review | 6 × 6 m, 1.2 m thick: concrete decks, sealed 0.9 m cavity with ribs, 2 cable trays + cables, round duct, 4000 K LED strips (own light, not preset-driven); `slab_HANDOFF` at −0.61. Test `kit_slab_test.py`: cut frame renders **identically (0/255 diff)** under `day_interior` and `tech_dark` when scenes use `C.key_slab_isolation()` (EEVEE leaks world light into the cavity otherwise: +24 %). Renders `renders/_kit/slab/` |
| — | School building exterior `PIECE_school_building` + `PIECE_school_grounds` (`kit_building.py`) | **review — awaiting your approval** | `renders/_kit/exterior/school_exterior_v1.png` (960×540, 64 samples, 28.7 s). Neutral choices (3 storeys, flat roof, warm white render, teal entrance portal) — not real details of the school. Scene 1 hero image + scene 6 background |
| 1 | Website | 0–269 | not started | |
| 2 | Turnstile with Face ID | 270–449 | not started | abstract dot-lattice scan UI only |
| 3 | CCTV | 450–599 | not started | depends on Q3 |
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
| Wordmark font with native ʻ U+02BB + commercial licence (`assets/fonts/`) | not chosen — glyph check pending |
| Reference photos | not needed — all spaces designed in Blender |
| Design-language choice | done — A (Warm modern) |
| Real building details (colour, floors, roof, main colours) | none provided yet (optional) |
| Licensed instrumental music (`assets/audio/music/`) | missing |
| Facility confirmation | missing |

## Placeholders in use

None yet. Every placeholder will be listed here (magenta "PLACEHOLDER" label in frame).
