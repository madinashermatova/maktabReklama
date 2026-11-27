// Renders blender/scenes/<scene>.blend with the Blender CLI (background) into renders/<scene>/,
// then copies the frames to public/renders/<scene>/ and refreshes the render manifest.
//
// Usage: npm run blender:render -- <scene> [--preview] [--frames <start>..<end>]
//   <scene>    scene id from src/timeline.ts, e.g. s02_turnstile
//   --preview  960×540 at 16 EEVEE samples (from blender/timeline.json)
//   --frames   render a sub-range, in the .blend frame numbering (= film frames unless the scene has blendFrom)
// Blender path: env BLENDER_EXE, default C:\Program Files\Blender Foundation\Blender 5.3\blender.exe
import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const blender = process.env.BLENDER_EXE ?? "C:\\Program Files\\Blender Foundation\\Blender 5.3\\blender.exe";

const args = process.argv.slice(2);
const scene = args.find((a) => !a.startsWith("--") && !/^\d+\.\.\d+$/.test(a));
const preview = args.includes("--preview");
const framesArg = args.includes("--frames") ? args[args.indexOf("--frames") + 1] : null;

const fail = (msg) => {
  console.error(msg);
  process.exit(1);
};
if (!scene) fail("Usage: npm run blender:render -- <scene> [--preview] [--frames <start>..<end>]");

// Keep blender/timeline.json current before Blender reads it.
spawnSync("node", ["--disable-warning=MODULE_TYPELESS_PACKAGE_JSON", "scripts/export-timeline.mjs"], { cwd: root, stdio: "inherit" });
const timeline = JSON.parse(readFileSync(join(root, "blender", "timeline.json"), "utf8"));
const def = timeline.scenes.find((s) => s.id === scene);
if (!def) fail(`Unknown scene "${scene}". Known: ${timeline.scenes.map((s) => s.id).join(", ")}`);

const blendFile = join(root, "blender", "scenes", `${scene}.blend`);
if (!existsSync(blendFile)) fail(`Missing ${blendFile}`);
if (!existsSync(blender)) fail(`Blender not found at ${blender} (set BLENDER_EXE)`);

// Blender numbering (= film frames unless the scene has blendFrom: built before a timeline shift).
const [bFrom, bEnd] = [def.blendFrom ?? def.from, def.blendEnd ?? def.end];
let [start, end] = [bFrom, bEnd];
if (framesArg) {
  const m = /^(\d+)\.\.(\d+)$/.exec(framesArg);
  if (!m) fail("--frames expects <start>..<end>");
  [start, end] = [Number(m[1]), Number(m[2])];
  if (start < bFrom || end > bEnd || start > end) fail(`--frames must lie within ${bFrom}..${bEnd} (.blend numbering)`);
}

const outDir = join(root, "renders", scene);
mkdirSync(outDir, { recursive: true });

// Settings applied on top of the .blend just for this run (nothing is saved back to the file).
const expr = [
  "import bpy",
  "s = bpy.context.scene",
  `s.frame_start, s.frame_end = ${start}, ${end}`,
  "s.render.image_settings.file_format = 'PNG'",
  ...(preview
    ? [`s.render.resolution_percentage = ${timeline.previewPercentage}`, `s.eevee.taa_render_samples = ${timeline.previewSamples}`]
    : ["s.render.resolution_percentage = 100"]),
].join("; ");

console.log(`Rendering ${scene} frames ${start}–${end}${preview ? " (preview)" : ""} …`);
const t0 = Date.now();
const r = spawnSync(
  blender,
  ["-b", blendFile, "--python-expr", expr, "-o", join(outDir, "####"), "-a"],
  { cwd: root, stdio: "inherit" },
);
const secs = (Date.now() - t0) / 1000;

// ALWAYS sync — also after a failed or interrupted render, so the frames that did finish reach Studio.
// sync-renders mirrors renders/<scene>/ → public/renders/<scene>/ and rewrites src/generated/renders.json.
console.log(`Syncing renders/${scene} → public/renders/${scene} and the render manifest …`);
const sync = spawnSync("node", ["--disable-warning=MODULE_TYPELESS_PACKAGE_JSON", "scripts/sync-renders.mjs"], {
  cwd: root,
  stdio: "inherit",
});
if (r.status !== 0) fail(`Blender exited with ${r.status} (frames rendered so far were synced)`);
if (sync.status !== 0) fail(`sync-renders failed with ${sync.status}`);
console.log(`Done in ${secs.toFixed(0)} s (${(secs / (end - start + 1)).toFixed(2)} s/frame incl. startup)`);
