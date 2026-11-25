// Exports src/timeline.ts to blender/timeline.json so Blender scripts use the same frame ranges.
// Usage: node scripts/export-timeline.mjs   (npm run timeline:export)
import { writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import * as t from "../src/timeline.ts";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const out = join(root, "blender", "timeline.json");

const data = {
  _comment: "GENERATED from src/timeline.ts by scripts/export-timeline.mjs — do not edit by hand.",
  fps: t.FPS,
  totalFrames: t.TOTAL_FRAMES,
  baseWidth: t.BLENDER_BASE_WIDTH,
  baseHeight: t.BLENDER_BASE_HEIGHT,
  previewPercentage: t.BLENDER_PREVIEW_PERCENTAGE,
  previewSamples: t.BLENDER_PREVIEW_SAMPLES,
  scenes: t.SCENES.map((s, i) => ({
    index: i + 1,
    id: s.id,
    name: s.name,
    from: s.from,
    end: t.sceneEnd(s),
    durationInFrames: s.durationInFrames,
    source: s.source,
    framesDir: t.framesDirOf(s),
  })),
};

writeFileSync(out, JSON.stringify(data, null, 2) + "\n");
console.log(`timeline → ${out} (${data.scenes.length} scenes, ${data.totalFrames} frames)`);
