# Status

States: **not started** · **in progress** · **review** · **approved**

## Pre-production

| Item | State | Notes |
|---|---|---|
| Environment audit | approved | EEVEE 14.1 s/frame, Cycles CPU 56.3 s/frame @1080p (simple scene) |
| CLAUDE.md rulebook | review | |
| Production plan | review | Open questions Q1–Q4 in `docs/production-plan.md` |
| Storyboard | review | |
| Initial git commit | blocked | Git user.name / user.email still not found in any git config (re-checked after the skeleton step) |
| Project skeleton | review | Folders, `src/timeline.ts`, `<SceneSequence>`, `ZiyoCommercial` (2250 f, 30 fps), `SoundLayer` + `src/soundCues.ts` (empty), npm scripts, `blender/scripts/_common.py`, `blender/timeline.json`. Verified: composition 1920×1080 / 3840×2160 with `REMOTION_FINAL=1`; placeholders show correct names and frame ranges; image-sequence playback tested with dummy frames; `_common.py` self-test passes in Blender 5.3 |

## Scenes

| # | Scene | Frames | State | Notes |
|---|---|---|---|---|
| — | Design language | approved | **A — Warm modern**, fixed (`docs/design-language.md`) |
| — | Shared kit `blender/kit/school_kit.blend` (`build_kit.py`) v2 | review | style A only; real lights under every fixture; school desk/chair/monitor/LED accent; exterior backdrop + HDRI; irradiance-volume bake; renders `renders/_kit/v2/`. Slab piece not yet built |
| — | School building exterior (kit) | — | not started | scene 1 hero image + scene 6 background |
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
