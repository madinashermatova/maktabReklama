// Scene 2 Face ID terminal screen (Remotion → PNG) for the Blender terminal display:
//   composition S02-FaceID-Screen (src/s02/FaceIdScreen.tsx) → renders/_faceid/####.png, numbered with ABSOLUTE film
//   frames of scene 2 (270 … 509), which blender/scripts/scene_02_turnstile.py plays as an image-sequence texture.
// Usage: npm run faceid:render   (then rebuild scene 2 so Blender picks the frames up)
import { bundle } from "@remotion/bundler";
import { renderFrames, selectComposition } from "@remotion/renderer";
import { mkdirSync, readdirSync, renameSync, rmSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import * as t from "../src/timeline.ts";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const outDir = join(root, "renders", "_faceid");
const tmpDir = join(outDir, "_tmp");
rmSync(outDir, { recursive: true, force: true });
mkdirSync(tmpDir, { recursive: true });

const scene = t.SCENES.find((s) => s.id === "s02_turnstile");
console.log("Bundling …");
const serveUrl = await bundle({ entryPoint: join(root, "src", "index.ts"), publicDir: join(root, "public") });
const composition = await selectComposition({ serveUrl, id: "S02-FaceID-Screen" });
await renderFrames({
  serveUrl,
  composition,
  imageFormat: "png",
  outputDir: tmpDir,
  onStart: () => console.log(`Face ID screen ${scene.from}–${t.sceneEnd(scene)} (${composition.width}×${composition.height}) …`),
  onFrameUpdate: () => {},
});
// renderFrames names files element-<local>.png → ####.png with the absolute film frame
for (const f of readdirSync(tmpDir)) {
  const m = /(\d+)\.png$/.exec(f);
  if (m) renameSync(join(tmpDir, f), join(outDir, `${String(scene.from + Number(m[1])).padStart(4, "0")}.png`));
}
rmSync(tmpDir, { recursive: true, force: true });
console.log(`Face ID screen → ${outDir}`);
