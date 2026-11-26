// 1) Scans public/renders/<sceneId>/ for frame sequences (e.g. 0270.png) and writes
//    src/generated/renders.json, which <SceneSequence> reads to decide image sequence vs. placeholder.
// 2) Mirrors assets/audio/{sfx,music}/ into public/audio/ and assets/{fonts,hero,web_images,brand}/ into public/ so Remotion
//    can serve them (the copies in public/ are git-ignored; assets/ is the source).
// Usage: node scripts/sync-renders.mjs   (npm run sync)
import { cpSync, existsSync, readdirSync, statSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const publicRenders = join(root, "public", "renders");
const manifestPath = join(root, "src", "generated", "renders.json");

const manifest = {};
if (existsSync(publicRenders)) {
  for (const id of readdirSync(publicRenders).sort()) {
    const dir = join(publicRenders, id);
    if (!statSync(dir).isDirectory()) continue;
    const frames = readdirSync(dir)
      .map((f) => /^(\d+)\.(png|jpg)$/i.exec(f))
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
