// Single source of truth for all timings of the ZIYO YOG’DUSI commercial.
// Every other file (Remotion and, via blender/timeline.json, Blender) reads frame ranges from here.
// After changing anything here run `npm run timeline:export` (done automatically by the npm scripts).
//
// Keep this file free of imports and non-erasable TypeScript (no enums/namespaces):
// scripts/export-timeline.mjs imports it directly with Node's type stripping.

export const FPS = 30;

/**
 * PREVIEW = true  → Remotion output 1920×1080 (default).
 * PREVIEW = false → Remotion output 3840×2160; set by `npm run render:final` via REMOTION_FINAL=1.
 * Blender always renders at the 1920×1080 base (see BLENDER_BASE_*); 4K is a later upscale / farm option.
 */
const readFinalFlag = (): boolean => {
  const env = (globalThis as { process?: { env?: Record<string, string | undefined> } }).process?.env;
  return env?.REMOTION_FINAL === "1";
};
export const PREVIEW: boolean = !readFinalFlag();
export const WIDTH = PREVIEW ? 1920 : 3840;
export const HEIGHT = PREVIEW ? 1080 : 2160;

/** Blender render base resolution and preview settings (CLAUDE.md). */
export const BLENDER_BASE_WIDTH = 1920;
export const BLENDER_BASE_HEIGHT = 1080;
export const BLENDER_PREVIEW_PERCENTAGE = 50; // 960×540
export const BLENDER_PREVIEW_SAMPLES = 16;

export type SceneSource = "blender" | "remotion" | "footage";

export type SceneDef = {
  /** Also the .blend name (blender/scenes/<id>.blend) and render folder (renders/<id>/). */
  id: string;
  name: string;
  /** Absolute film frame where the scene starts (inclusive). */
  from: number;
  durationInFrames: number;
  source: SceneSource;
  /** Folder inside public/ with the frame sequence. Default: renders/<id> */
  framesDir?: string;
  /**
   * Frame numbering of the scene's .blend and its rendered files, when it differs from `from` — i.e. the scene
   * was built and rendered before a timeline shift. Blender keeps building/rendering at blendFrom … blendFrom +
   * durationInFrames − 1 (so the existing .blend and frames stay valid; no re-render), and Remotion plays the
   * frames by scene-local index, so they appear at `from`. Remove it when the scene is rebuilt at its new position.
   */
  blendFrom?: number;
};

export const SCENES: readonly SceneDef[] = [
  { id: "s01_website", name: "Website", from: 0, durationInFrames: 270, source: "blender" },
  { id: "s02_turnstile", name: "Turnstile with Face ID", from: 270, durationInFrames: 240, source: "blender" }, // 8 s (2026-11-27)
  // Moved 450 → 510 on 2026-11-27; its .blend and approved preview are numbered 450–599 (not re-rendered).
  { id: "s03_cctv", name: "CCTV", from: 510, durationInFrames: 150, source: "blender", blendFrom: 450 },
  { id: "s04_english", name: "English class", from: 660, durationInFrames: 210, source: "blender" },
  { id: "s05_russian", name: "Russian class", from: 870, durationInFrames: 150, source: "blender" }, // 6 → 5 s (2026-11-27)
  { id: "s06_football", name: "Football field", from: 1020, durationInFrames: 210, source: "blender" }, // 8 → 7 s (2026-11-27)
  { id: "s07_it", name: "IT class", from: 1230, durationInFrames: 240, source: "blender" },
  { id: "s08_cafeteria", name: "Cafeteria — plov", from: 1470, durationInFrames: 240, source: "blender" },
  { id: "s09_dormitory", name: "Dormitory", from: 1710, durationInFrames: 210, source: "blender" },
  { id: "s10_rewind", name: "Rewind", from: 1920, durationInFrames: 150, source: "remotion" },
  { id: "s11_brand", name: "Brand reveal", from: 2070, durationInFrames: 180, source: "blender" },
];

export const TOTAL_FRAMES = 2250; // 75 s × 30 fps

// --------------------------------------------------------------------------- scene 1 beats

/** Scene 1 "Digital website universe" beats — absolute film frames (scene 1 starts at 0). docs/storyboard.md → Scene 1. */
export const S01_BEATS = {
  fadeInEnd: 12, // black → picture
  scrollStart: 14, // strip starts to move (slow), accelerates, flies, decelerates
  scrollStop: 190, // precise stop on the school website hero
  cursorIn: 194, // cursor fades in
  cursorArrive: 210, // cursor reaches the hero button (hover)
  click: 215, // press + ripple
  diveStart: 218, // camera starts the dive into the screen
  uiFadeStart: 221, // website UI fades away, leaving only the hero photo
  uiFadeEnd: 236,
  alignedAt: 246, // camera square-on to the screen, centred, roll matched
  photoOverlayStart: 252, // Remotion lays the exact photo pixels over the render (cross-fade) …
  photoOverlayEnd: 258, // … fully the exact photo from here to the cut
};

/**
 * D hand-off (1 → 2). Scene 2's first frame (270) shows the hero photo at ENTRY_SCALE (18 mm vs the 15.33 mm photo
 * lens) and the scene-2 camera moves forward at ENTRY_SPEED toward the facade FACADE_DISTANCE away
 * (blender/scripts/build_entrance.py), i.e. an apparent push rate of ENTRY_SPEED / FACADE_DISTANCE per frame.
 * Scene 1 reaches the same scale and rate: s(269) = ENTRY_SCALE / (1 + rate), constant rate over the last HOLD frames.
 */
export const HANDOFF_D = {
  entryScale: 1.174,
  entrySpeed: 0.03,
  facadeDistance: 8.48,
  holdFrames: 6,
  /** Photo scale (photo width / frame width) when the dive starts; Blender places the camera from it. */
  diveStartScale: 0.6,
};

/**
 * Scale of the website/photo (screen width / frame width) on the scene-1 dive, film frames diveStart … 269.
 * Blender's camera distance and Remotion's exact-photo overlay both use this one curve (via blender/timeline.json).
 * ln s: cubic Hermite (slope 0 → push rate) from diveStart to 269 − holdFrames, then constant rate to the cut.
 */
export const s01PhotoScale = (frame: number): number => {
  const end = SCENES[0].from + SCENES[0].durationInFrames - 1; // 269, the last frame of scene 1
  const rate = Math.log(1 + HANDOFF_D.entrySpeed / HANDOFF_D.facadeDistance); // ln-scale per frame
  const lnAt270 = Math.log(HANDOFF_D.entryScale);
  const t1 = end - HANDOFF_D.holdFrames;
  const ln1 = lnAt270 - rate * (end + 1 - t1);
  const ln0 = Math.log(HANDOFF_D.diveStartScale);
  if (frame <= S01_BEATS.diveStart) return HANDOFF_D.diveStartScale;
  if (frame >= t1) return Math.exp(ln1 + rate * (frame - t1));
  const n = t1 - S01_BEATS.diveStart;
  const u = (frame - S01_BEATS.diveStart) / n;
  const h00 = 2 * u ** 3 - 3 * u ** 2 + 1;
  const h10 = u ** 3 - 2 * u ** 2 + u;
  const h01 = -2 * u ** 3 + 3 * u ** 2;
  const h11 = u ** 3 - u ** 2;
  return Math.exp(h00 * ln0 + h10 * 0 * n + h01 * ln1 + h11 * rate * n);
};

// --------------------------------------------------------------------------- scene 2 beats

/**
 * Scene 2 "Turnstile with Face ID" beats — absolute film frames (scene 2 = 270–509). docs/storyboard.md → Scene 2.
 * Read by blender/scripts/scene_02_turnstile.py (via blender/timeline.json) and by the Face ID screen (src/s02/).
 */
export const S02_BEATS = {
  dissolveEnd: 300, // projected photo → 3D replica complete (ENTRANCE_PROJ alpha 0; fixed by blender/kit/entrance.blend)
  zoomStart: 330, // camera glides toward the guard booth, 18 → 85 mm while it decelerates …
  boothStop: 358, // … exact stop, close on the Face ID terminal of the turnstile beside the booth
  scanStart: 366, // scan line sweeps the dot lattice top → bottom (display red) — slower, unhurried (2026-11-28)
  scanEnd: 408,
  granted: 412, // display + turnstile LEDs red → green, check glyph
  wingsOpenStart: 418, // the turnstile glass wing swings open (calm motorised swing) …
  wingsOpenEnd: 448,
  moveOn: 424, // camera leaves the terminal, into the lane (85 → 24 mm)
  lanePass: 465, // camera passes the wing line → fast courtyard slide + dive into the paving (465–509 ≈ 1.5 s, 2026-11-28)
  tiltStart: 472, // the camera tilts down to the paving while it accelerates into the dive
  exitHold: 503, // S hand-off window 503–509 (constant 0.12 m/frame down)
};

export const sceneEnd = (s: SceneDef): number => s.from + s.durationInFrames - 1;
export const framesDirOf = (s: SceneDef): string => s.framesDir ?? `renders/${s.id}`;
/** First frame number of the scene inside its .blend and render files (see SceneDef.blendFrom). */
export const blendFromOf = (s: SceneDef): number => s.blendFrom ?? s.from;

// Fail loudly if the timeline has gaps, overlaps or the wrong total length.
(() => {
  let expected = 0;
  for (const s of SCENES) {
    if (s.from !== expected) {
      throw new Error(`timeline.ts: scene ${s.id} starts at ${s.from}, expected ${expected} (gap or overlap)`);
    }
    expected = s.from + s.durationInFrames;
  }
  if (expected !== TOTAL_FRAMES) {
    throw new Error(`timeline.ts: scenes end at ${expected}, expected ${TOTAL_FRAMES}`);
  }
})();
