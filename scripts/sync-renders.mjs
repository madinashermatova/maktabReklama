// 0) Mirrors every scene's frames renders/<sceneId>/NNNN.png → public/renders/<sceneId>/ (only frames inside the
//    scene's .blend frame range (blendFrom…blendEnd) from blender/timeline.json; changed files are recopied, frames no longer in renders/ are removed).
//    So any render that writes into renders/<sceneId>/ — npm run blender:render or a hand-run blender.exe — reaches
//    Remotion with one `npm run sync` (run automatically by blender:render, dev and preview).
// 1) Scans public/renders/<sceneId>/ for frame sequences (e.g. 0270.png) and writes
//    src/generated/renders.json, which <SceneSequence> reads to decide image sequence vs. placeholder.
// 2) Mirrors assets/audio/{sfx,music}/ into public/audio/ and assets/{fonts,hero,web_images,brand}/ into public/ so Remotion
//    can serve them (the copies in public/ are git-ignored; assets/ is the source).
// Usage: node scripts/sync-renders.mjs   (npm run sync)
import { copyFileSync, cpSync, existsSync, mkdirSync, readdirSync, readFileSync, rmSync, statSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const publicRenders = join(root, "public", "renders");
const manifestPath = join(root, "src", "generated", "renders.json");

const FRAME = /^(\d+)\.(png|jpg)$/i;
const timelinePath = join(root, "blender", "timeline.json");
const scenes = existsSync(timelinePath) ? JSON.parse(readFileSync(timelinePath, "utf8")).scenes : [];
// Scene folders renders/<id>/ plus scene-owned layer folders renders/<id>_<layer>/ (e.g. s02_turnstile_proj).
const rendersRoot = join(root, "renders");
const folders = existsSync(rendersRoot)
  ? readdirSync(rendersRoot).flatMap((dir) => {
      const def = scenes.find((s) => dir === s.id || dir.startsWith(`${s.id}_`));
      return def ? [{ dir, def }] : [];
    })
  : [];
for (const { dir, def } of folders) {
  const src = join(rendersRoot, dir);
  if (!statSync(src).isDirectory()) continue;
  const frames = readdirSync(src).filter((f) => {
    const m = FRAME.exec(f);
    return m && Number(m[1]) >= (def.blendFrom ?? def.from) && Number(m[1]) <= (def.blendEnd ?? def.end);
  });
  if (frames.length === 0) continue; // nothing rendered here yet: leave any existing public copy alone
  const dst = join(publicRenders, dir);
  mkdirSync(dst, { recursive: true });
  const keep = new Set(frames);
  let copied = 0;
  let removed = 0;
  for (const f of readdirSync(dst)) {
    if (FRAME.test(f) && !keep.has(f)) {
      rmSync(join(dst, f));
      removed++;
    }
  }
  for (const f of frames) {
    const a = statSync(join(src, f));
    const out = join(dst, f);
    const b = existsSync(out) ? statSync(out) : null;
    if (!b || b.size !== a.size || b.mtimeMs < a.mtimeMs) {
      copyFileSync(join(src, f), out);
      copied++;
    }
  }
  console.log(`  renders/${dir} → public/renders/${dir}: ${frames.length} frames (${copied} copied, ${removed} removed)`);
}

const manifest = {};
if (existsSync(publicRenders)) {
  for (const id of readdirSync(publicRenders).sort()) {
    const dir = join(publicRenders, id);
    if (!statSync(dir).isDirectory()) continue;
    const frames = readdirSync(dir)
      .map((f) => FRAME.exec(f))
      .filter(Boolean)
      .map((m) => ({ n: Number(m[1]), pad: m[1].length, ext: m[2].toLowerCase() }))
      .sort((a, b) => a.n - b.n);
    if (frames.length === 0) continue;
    // Count only the contiguous run from the first frame, so a gap never plays the wrong image.
    let count = 1;
    while (count < frames.length && frames[count].n === frames[0].n + count) count++;
    if (count < frames.length) {
      console.warn(`! ${id}: gap after frame ${frames[0].n + count - 1}; using the first ${count} frames only`);
    }
    manifest[id] = { dir: `renders/${id}`, first: frames[0].n, count, pad: frames[0].pad, ext: frames[0].ext };
    console.log(`  ${id}: ${count} frames from ${frames[0].n}`);
  }
}
writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + "\n");
console.log(`render manifest → ${manifestPath} (${Object.keys(manifest).length} scenes with frames)`);

for (const sub of ["sfx", "music"]) {
  const src = join(root, "assets", "audio", sub);
  if (existsSync(src)) {
    cpSync(src, join(root, "public", "audio", sub), {
      recursive: true,
      filter: (p) => !p.endsWith(".gitkeep"),
    });
  }
}

for (const sub of ["fonts", "hero", "web_images", "brand"]) {
  const src = join(root, "assets", sub);
  if (existsSync(src)) cpSync(src, join(root, "public", sub), { recursive: true });
}
