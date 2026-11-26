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

## Scene 3 — CCTV security (450–599)

Servo moves have a short overshoot + settle: "stop" = the frame the move settles (start + 10 for the left pan, + 13 for the right pan). Three cameras: bullet L (left wall), dome (ceiling pendant), bullet R (right wall), staggered by 2–4 frames so they never sound (or move) identically.

| Id | Frame(s) | Event (picture) | Sound |
|---|---|---|---|
| s03_slab_tail | 450–456 | slab pass (ENTRY S), camera inside the slab | tail of scene 2's downward whoosh |
| s03_ceiling_out | 457 | camera emerges through the ceiling into the corridor | soft air "open" swell, corridor room tone fades in |
| s03_monitor_on | 484 | security monitor shows the live feeds | faint monitor tick / hum |
| s03_rail_L | 484 → 502 | bullet L slides out of its wall housing on rails | short smooth linear-rail glide, soft stop at 502 |
| s03_rail_dome | 488 → 506 | dome lowers from the ceiling hatch on its pendant rod | telescopic glide (slightly lower pitch), soft stop at 506 |
| s03_rail_R | 492 → 510 | bullet R slides out | rail glide, soft stop at 510 |
| s03_pan_left | start 510 / 512 / 514 → stop 520 / 522 / 524 | each camera pans LEFT 35° (L / dome / R) | quick servo whir, tiny settle click at each stop |
| s03_pan_right | start 535 / 537 / 539 → stop 548 / 550 / 552 | each camera pans RIGHT 70° | longer servo whir, settle click at each stop |
| s03_light_appear | 550 → 556 | the glowing light point appears at the far end | soft shimmer |
| s03_light_travel | 556 → 588 | the light travels down the corridor and passes the camera | gentle airy pass-by (doppler-ish, peak ≈ 578) |
| s03_track | 560 / 562 / 564 → | cameras start tracking (L / dome / R) | continuous fine servo micro-whirs |
| s03_lock_on | 567 / 569 / 571 | blue status LEDs pulse brighter: lock-on (L / dome / R) | three soft digital "lock" blips |
| s03_push_whoosh | 568 → 599 | camera pushes forward-and-down into the dome lens | rising whoosh, muffled as it enters the glass |
| s03_lens_pass | 596–599 | inside the coated lens (EXIT C) | soft glassy "thunk" / pressure drop into scene 4 |
