// Single source of truth for all timings of the ZIYO YOGʻDUSI commercial.
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
};

export const SCENES: readonly SceneDef[] = [
  { id: "s01_website", name: "Website", from: 0, durationInFrames: 270, source: "blender" },
  { id: "s02_turnstile", name: "Turnstile with Face ID", from: 270, durationInFrames: 180, source: "blender" },
  { id: "s03_cctv", name: "CCTV", from: 450, durationInFrames: 150, source: "blender" },
  { id: "s04_english", name: "English class", from: 600, durationInFrames: 210, source: "blender" },
  { id: "s05_russian", name: "Russian class", from: 810, durationInFrames: 180, source: "blender" },
  { id: "s06_football", name: "Football field", from: 990, durationInFrames: 240, source: "blender" },
  { id: "s07_it", name: "IT class", from: 1230, durationInFrames: 240, source: "blender" },
  { id: "s08_cafeteria", name: "Cafeteria — plov", from: 1470, durationInFrames: 240, source: "blender" },
  { id: "s09_dormitory", name: "Dormitory", from: 1710, durationInFrames: 210, source: "blender" },
  { id: "s10_rewind", name: "Rewind", from: 1920, durationInFrames: 150, source: "remotion" },
  { id: "s11_brand", name: "Brand reveal", from: 2070, durationInFrames: 180, source: "blender" },
];

export const TOTAL_FRAMES = 2250; // 75 s × 30 fps

export const sceneEnd = (s: SceneDef): number => s.from + s.durationInFrames - 1;
export const framesDirOf = (s: SceneDef): string => s.framesDir ?? `renders/${s.id}`;

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
