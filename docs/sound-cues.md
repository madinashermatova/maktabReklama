# Sound cue sheet

Every sound-synced event with its exact **absolute film frame** (30 fps). Frames come from `src/timeline.ts`; if a beat moves there, update this sheet and `src/soundCues.ts`.
SFX: only ElevenLabs `text_to_sound_effects` → `assets/audio/sfx/`. Music: only files you put in `assets/audio/music/`. **No voice, ever.**

State: cues are defined; no SFX file generated yet (`src/soundCues.ts` is still empty).

## Scene 1 — Digital website universe (0–269)

| Id | Frame(s) | Event (picture) | Sound |
|---|---|---|---|
| s01_music_in | 0 | fade up from black (0–12) | music start (soft intro) — needs your music file |
| s01_scroll_whoosh | 14 → 102 → 190 | strip starts moving at 14, **peak speed at 102**, lands at 190 | one long airy "digital scroll" whoosh: starts barely audible at 14, rises to its loudest/brightest at 102, falls away into 190 |
| s01_scroll_stop | 190 | strip stops exactly on the school website | soft, precise "settle" tick / low thump (no bounce) |
| s01_cursor_in | 194 | cursor fades in | (optional) very faint UI air |
| s01_hover | 210 | cursor reaches the button, button brightens | tiny soft hover tone |
| s01_click | 215 | button press + ripple | soft UI click |
| s01_dive_whoosh | 218 → 269 | camera dives into the screen; UI fades 221–236, square-on at 246, exact photo from 252 | rising pass-through whoosh: starts at 218, builds to the cut at 269/270 |
| s01_to_s02 | 270 | photo dissolves into the 3D entrance (scene 2) | whoosh tail (shared with scene 2's first cue) |
