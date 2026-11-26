# CLAUDE.md — ZIYO YOG’DUSI commercial: permanent rulebook

These rules apply to every step of this project. If a request conflicts with them, stop and ask.

## PROJECT

- Cinematic commercial for the real private school **ZIYO YOG’DUSI** (grades 1–11, Samarkand region, Uzbekistan). Goal: parents feel the school is **modern, safe, technologically advanced, comfortable and inspiring**.
- Format: 16:9, **30 fps**, target **75 s = 2250 frames** (0–2249).
- Render engine: **EEVEE for everything**. This PC (Intel i5-12400, Intel UHD 730 iGPU, 16 GB RAM) has no GPU Cycles can use; Cycles on CPU measured ~56 s/frame at 1080p vs EEVEE ~14 s/frame.
- Previews: **960×540, ~16 EEVEE samples**. Final: **1920×1080**. 4K is a later option (AI upscale or GPU render farm), so every Blender scene and the Remotion composition must be **resolution-independent**: set resolution only via one setting per file (base 1920×1080 + `resolution_percentage`), never hard-code pixel sizes in Remotion — derive from `useVideoConfig()` width/height.
- Simulations run on the CPU with 16 GB RAM: prefer **Geometry Nodes, rigid bodies and light cloth**; no heavy Mantaflow fluid; keep bakes small (low-res sims + subdivision after).
- Style: photorealistic cinematic 3D — realistic lighting, soft shadows, reflections (EEVEE raytracing / screen-space), ambient occlusion, depth of field.
- **No voice-over, narration, TTS, dialogue or subtitles. Ever.** The only on-screen text: website UI text (scene 1), the school's **one real entrance signboard** replicated exactly — `“ZIYO YOG’DUSI” XUSUSIY MAKTABI` (scenes 1–2, in the hero photo and the 3D replica) — and the final brand name (scene 11). Any other signage needs a new decision from the user (2026-11-26).
- **No students or other people** (no bodies, faces, hands or silhouettes) in the film or in reference material. Life is suggested through objects, light and motion. This includes UI graphics: the Face ID scan (scene 2) shows only an abstract dot/mesh grid — never a face, head, silhouette or body shape (no oval, eyes, nose or shoulders).

## HONESTY RULES

- Never invent statistics, awards, prices, phone numbers, addresses, dates or claims about the school.
- Show only facilities the school really has.
- **Real reference: `assets/reference/entrance_front.jpg`** (added 2026-11-26) shows the real entrance. It is the reference for the exterior/entrance and for the scene 1 → 2 transition; any further photos in `assets/reference/` are references too. The 3D entrance is a faithful replica of what the photos show; for parts no photo shows, invent only neutral detail that contradicts nothing in them, and say so in `docs/status.md`. Spaces with no photo (corridors, classrooms, cafeteria, sports ground, dormitory, …) are still designed in Blender in the chosen design language (see DESIGN LANGUAGE). Respect every real detail; never contradict it.
- The website hero image (scene 1) is the **real entrance photo**, not a render. The only permitted edit is replacing the sky (plus a slight matching colour grade); buildings, gate, booth, signboard and its text are never altered.
- There is **no official logo yet**. Never draw or invent a symbol, emblem, monogram or icon for the school. See BRAND below.
- Never show real third-party websites, brands or logos (no real OS, browser, social network, sportswear, food or device brands). Generic invented UIs and unbranded products only.
- Never present a placeholder as finished. Mark placeholders visibly (magenta `#FF00FF` label "PLACEHOLDER") and list them in `docs/status.md`.

## BRAND

- The brand is a **typographic wordmark only**: `ZIYO YOG’DUSI` — uppercase, with **’ (U+2019, right single quotation mark) exactly as on the real signboard** (user decision 2026-11-26) — not an ASCII apostrophe `'` (U+0027), not ʻ (U+02BB), not ‘ (U+2018). Use exactly this spelling everywhere in the film.
- **Where it appears:** the website (scene 1) and the brand reveal (scene 11) show only `ZIYO YOG’DUSI` — no quotation marks, no other words; **the film ends on this wordmark alone**. The 3D signboard replica (scenes 1–2) shows exactly `“ZIYO YOG’DUSI” XUSUSIY MAKTABI` (curly quotes U+201C/U+201D), like the real sign.
- In code, write the character as `’` (`’`) and keep both strings in one shared constant module per codebase (`src/brand.ts`, `blender/scripts/common/brand.py`).
- Never draw or invent a symbol, emblem, monogram or icon for the school.
- **Fonts for the wordmark:** the typeface must contain U+2019 (and U+201C/U+201D for the signboard) **natively**. Before using a font, check its glyph coverage programmatically (`cmap` lookup for 0x2019, 0x201C, 0x201D and every letter used) and record the result in `docs/status.md`. Never allow fallback to another font: in Remotion load the font with `@remotion/fonts`/`loadFont` and wait for it before render; in Blender use a `VectorFont` loaded from the file in `assets/fonts/` (never the built-in `Bfont`). The font licence must allow commercial use (e.g. SIL OFL); keep the licence file next to the font in `assets/fonts/`.
- **Logo slot:** scenes 1 and 11 must accept a logo added later to `assets/brand/` **without rebuilding them**: the logo is an optional layer driven by one config entry (`src/brand.ts` → `logoFile: string | null`). With `null`, only the wordmark is shown, laid out so it looks complete on its own. Scene 11 wordmark/logo are composited in Remotion over a Blender light/background plate, so adding a logo needs no Blender change. Scene 1's website UI is a Remotion-rendered sequence used by Blender as an external image-sequence texture: adding a logo means re-rendering that sequence and the scene 1 frames, with no change to the `.blend` or its build script.

## DESIGN LANGUAGE

- Architecture with no reference photo is invented in Blender. The **entrance is a replica of the real one** (`assets/reference/entrance_front.jpg`), not design language A: real materials and colours win wherever a photo shows them.
- Chosen design language: **A — Warm modern** (user decision, 2026-11-25), **fixed for the whole film**: warm white walls `#ECE6DC`, light oak floors/doors/skirting, teal `#2F6E73` accent, amber `#E3A33B` small accents, graphite window frames, white tile ceiling that always reads white. Full spec: `docs/design-language.md`. Never reintroduce options B or C.
- **Real details of the school (from `entrance_front.jpg`, 2026-11-26):** entrance between two buildings — left a 3-storey cream/beige building with a brown roof edge; right a light grey/white building with a grey plinth, arched wall niches, gutters and downpipes and a CCTV camera on its corner; dark grey square entrance pillars with horizontal grooves; dark signboard with warm yellow illuminated letters `“ZIYO YOG’DUSI” XUSUSIY MAKTABI`; laser-cut metal gate with an Islamic geometric pattern; guard booth on the right with patterned glass doors; white tensile canopy frame with cables over the entrance; grey/white checkerboard paving; potted plants behind the gate. These override the design-language samples. The generic kit building (`PIECE_school_building`) is **superseded** for the hero image and the entrance; whether anything of it may still appear (e.g. stadium background, scene 6) needs a user decision.

## CAMERA AND CONTINUITY

- The world is **one continuous vertical film strip**: scenes are stacked top to bottom; the camera always travels **DOWNWARD** between scenes. Forward dolly moves are allowed inside a scene.
- Each scene has a defined **ENTRY** frame and **EXIT** frame (camera position, rotation, focal length, light colour) — see `docs/storyboard.md`. The exit of scene N must match the entry of scene N+1 so cuts are invisible.
- The **floor-slab pass** is the DEFAULT transition, not the only one: the camera descends through the shared floor slab (`blender/kit/slab`) and the cut happens at the slab midpoint, where both scenes show the identical slab interior.
- Other transitions are used where they are motivated, and the film uses **at least 3 different transition types** so it never feels repetitive. Fixed choices: scene 1→2 is a **photo-to-3D dissolve** (the camera pushes into the real entrance photo on the website; the photo dissolves into the 3D replica at the matched camera; the camera then moves through the gate toward the turnstile — user decision 2026-11-26); transitions into and out of the outdoor stadium (5→6, 6→7) use a **window/sky** move. The full transition list is in `docs/storyboard.md` → "Transitions"; every transition still moves the camera downward (or forward-and-down) and has a matched EXIT/ENTRY definition.
- **Lenses:** 24 / 35 / 50 mm are the standard set. Also allowed: **18 mm** for wide establishing shots (website void, stadium; use sparingly indoors to avoid distortion) and **85 / 100 mm** for close-ups (plov, camera lens, turnstile LED, smart-board code). **Nothing wider than 18 mm or longer than 100 mm.** Enforced by `_common.set_lens()`.
- No random camera shake. Every speed change uses smooth easing (speed ramps, Bezier — no linear starts/stops).

## ANIMATION QUALITY

- Physically plausible motion: weight, acceleration, deceleration, contact, settling. No cartoon squash/stretch, no clipping through floors, walls or other objects.
- Do not reuse one entrance move ("falls from the ceiling") in every scene. Vary entrances: assemble, slide, unfold, rise, rotate into place.
- Use real 3D geometry where 3D is requested; no flat images as substitutes (screen contents and textures are fine).
- Consistent architecture: all interiors share one design language — same wall/floor materials palette, window frames, ceiling system and lighting fixtures from `blender/kit/`.

## PIPELINE RULES

- Folders:
  - `blender/scenes/` — one `.blend` per scene (`s01_website.blend` …)
  - `blender/scripts/` — Python that builds each scene, so it is reproducible
  - `blender/kit/` — shared assets (slab, architecture, fixtures, materials)
  - `renders/<scene>/` — frame sequences (git-ignored)
  - `public/` — files Remotion uses (render frames are linked/copied here at assembly time)
  - `src/` — Remotion code
  - `docs/` — production plan, storyboard, status, sound cues
- Every Blender scene is built by a re-runnable Python script in `blender/scripts/`; the MCP is used to run and inspect it.
- Heavy work (simulation bakes, renders) runs **only through the Blender CLI in the background** (`blender.exe -b file.blend --python ...` / `-a`), never through the MCP — avoids timeouts and a frozen UI.
- After building or changing a scene, use the MCP `look` tool to inspect the viewport and fix visible problems before reporting.
- Render 3D as PNG sequences (RGBA when compositing is needed). Remotion assembles everything; **one centralized timeline file** (`src/timeline.ts`) defines all frame ranges — no frame numbers hard-coded elsewhere.
- Sound: create sound effects **only** with the elevenlabs MCP tool `text_to_sound_effects`, saved to `assets/audio/sfx/`. Never use text-to-speech, voice, dubbing or speech tools — the film has no voice. The deny rules in `.claude/settings.json` stay exactly as they are. Music comes only from files the user puts in `assets/audio/music/`. Keep a cue sheet (`docs/sound-cues.md`) of every sound-synced event with its exact frame.
- Commit to git after each approved step.
- Blender executable: `C:\Program Files\Blender Foundation\Blender 5.3\blender.exe` (Blender 5.3.0). Remotion 4.0.547.
