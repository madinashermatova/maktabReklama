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

## Scene 2 — Turnstile with Face ID (270–509)

Frames from `S02_BEATS` (`src/timeline.ts`; real layout since 2026-11-27: one turnstile beside the guard booth). The wing swing settles with a ≈1 % overshoot near its end frame.

| Id | Frame(s) | Event (picture) | Sound |
|---|---|---|---|
| s02_dissolve | 270 → 300 | photo dissolves into the 3D entrance | tail of `s01_dive_whoosh`, settling into soft morning outdoor air |
| s02_approach | 300 → 358 | camera glides toward the guard booth and the turnstile, decelerating | soft airy glide that settles into stillness at 358 |
| s02_stop | 358 | exact stop on the Face ID terminal | (silence beat) |
| s02_scan | 362 → 388 | red scan line sweeps the dot lattice | soft rising scanning tone |
| s02_ticks | 366 → 388 | dots light up in rows | tiny digital ticks in small groups |
| s02_granted | 391 | lattice + LEDs red → green, check glyph | two-tone confirmation beep |
| s02_wing | 395 → 415 | the glass wing swings open | quiet servo whir, soft settle click at ≈ 415 |
| s02_pass | 405 → 420 | camera passes through the lane beside the booth | light close pass-by air |
| s02_courtyard | 420 → 470 | slow calm glide into the courtyard toward the glass cafeteria | morning courtyard air; a faint warm room tone through the glass (no voices), soft leaf rustle as the palms pass (≈ 430–450) |
| s02_dive_whoosh | 460 → 509 | camera tilts down and sinks smoothly into the paving and the slab | soft, slowly building downward whoosh (no sudden hit) into scene 3's `s03_slab_tail` |

## Scene 3 — CCTV security (510–659)

Film frames (scene 3 moved 450 → 510 on 2026-11-27; `.blend` / render frame = film − 60). Servo moves have a short overshoot + settle: "stop" = the frame the move settles (start + 10 for the left pan, + 13 for the right pan). Three cameras: bullet L (left wall), dome (ceiling pendant), bullet R (right wall), staggered by 2–4 frames so they never sound (or move) identically.

| Id | Frame(s) | Event (picture) | Sound |
|---|---|---|---|
| s03_slab_tail | 510–516 | slab pass (ENTRY S), camera inside the slab | tail of scene 2's downward whoosh |
| s03_ceiling_out | 517 | camera emerges through the ceiling into the corridor | soft air "open" swell, corridor room tone fades in |
| s03_monitor_on | 544 | security monitor shows the live feeds | faint monitor tick / hum |
| s03_rail_L | 544 → 562 | bullet L slides out of its wall housing on rails | short smooth linear-rail glide, soft stop at 562 |
| s03_rail_dome | 548 → 566 | dome lowers from the ceiling hatch on its pendant rod | telescopic glide (slightly lower pitch), soft stop at 566 |
| s03_rail_R | 552 → 570 | bullet R slides out | rail glide, soft stop at 570 |
| s03_pan_left | start 570 / 572 / 574 → stop 580 / 582 / 584 | each camera pans LEFT 35° (L / dome / R) | quick servo whir, tiny settle click at each stop |
| s03_pan_right | start 595 / 597 / 599 → stop 608 / 610 / 612 | each camera pans RIGHT 70° | longer servo whir, settle click at each stop |
| s03_light_appear | 610 → 616 | the glowing light point appears at the far end | soft shimmer |
| s03_light_travel | 616 → 648 | the light travels down the corridor and passes the camera | gentle airy pass-by (doppler-ish, peak ≈ 638) |
| s03_track | 620 / 622 / 624 → | cameras start tracking (L / dome / R) | continuous fine servo micro-whirs |
| s03_lock_on | 627 / 629 / 631 | blue status LEDs pulse brighter: lock-on (L / dome / R) | three soft digital "lock" blips |
| s03_push_whoosh | 628 → 659 | camera pushes forward-and-down into the dome lens | rising whoosh, muffled as it enters the glass |
| s03_lens_pass | 656–659 | inside the coated lens (EXIT C) | soft glassy "thunk" / pressure drop into scene 4 |
