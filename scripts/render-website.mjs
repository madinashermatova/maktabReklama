// Scene 1 website textures (Remotion → PNG) for the Blender display.
//   1) the 6 generic pages + the school page at S01_BEATS.scrollStop → renders/_website/pages/NN_<id>.png
//   2) the school page sequence S01_BEATS.scrollStop … end of scene 1 → renders/_website/school_seq/####.png
//      (absolute film frame numbers; Blender plays it as an image-sequence texture after the scroll stops)
// Then tools/build_website_strip.py stacks the 7 pages into blender/kit/textures/website_strip.png.
// Usage: npm run website:render
import { bundle } from "@remotion/bundler";
import { renderFrames, renderStill, selectComposition } from "@remotion/renderer";
import { spawnSync } from "node:child_process";
import { mkdirSync, readdirSync, renameSync, rmSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import * as t from "../src/timeline.ts";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
spawnSync("node", ["--disable-warning=MODULE_TYPELESS_PACKAGE_JSON", "scripts/sync-renders.mjs"], { cwd: root, stdio: "inherit" });

const pagesDir = join(root, "renders", "_website", "pages");
const seqDir = join(root, "renders", "_website", "school_seq");
rmSync(pagesDir, { recursive: true, force: true });
rmSync(seqDir, { recursive: true, force: true });
mkdirSync(pagesDir, { recursive: true });
mkdirSync(seqDir, { recursive: true });

console.log("Bundling …");
const serveUrl = await bundle({ entryPoint: join(root, "src", "index.ts"), publicDir: join(root, "public") });

const pageIds = [
  "S01-Web-1-Travel",
  "S01-Web-2-Store",
  "S01-Web-3-News",
  "S01-Web-4-Fitness",
  "S01-Web-5-Bank",
  "S01-Web-6-Portfolio",
];
for (const [i, id] of pageIds.entries()) {
  const composition = await selectComposition({ serveUrl, id });
  const output = join(pagesDir, `${String(i + 1).padStart(2, "0")}_${id}.png`);
  await renderStill({ serveUrl, composition, output, frame: 0, imageFormat: "png" });
  console.log(`  ${output}`);
}

const school = await selectComposition({ serveUrl, id: "S01-SchoolSite" });
const stop = t.S01_BEATS.scrollStop;
await renderStill({ serveUrl, composition: school, output: join(pagesDir, "07_S01-SchoolSite.png"), frame: stop, imageFormat: "png" });
console.log("  school page (strip) at frame", stop);

const end = t.sceneEnd(t.SCENES[0]);
await renderFrames({
  serveUrl,
  composition: school,
  imageFormat: "png",
  outputDir: seqDir,
  frameRange: [stop, end],
  onStart: () => console.log(`School sequence ${stop}–${end} …`),
  onFrameUpdate: () => {},
});
// renderFrames names files element-<n>.png → rename to ####.png (absolute film frame)
for (const f of readdirSync(seqDir)) {
  const m = /(\d+)\.png$/.exec(f);
  if (m) renameSync(join(seqDir, f), join(seqDir, `${String(Number(m[1])).padStart(4, "0")}.png`));
}
console.log(`School sequence → ${seqDir}`);
