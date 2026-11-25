// Renders the ZiyoCommercial composition.
//   node scripts/render.mjs preview  → 1920×1080 → out/preview.mp4
//   node scripts/render.mjs final    → 3840×2160 → out/final.mp4 (REMOTION_FINAL=1 flips PREVIEW in src/timeline.ts)
import { spawnSync } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const mode = process.argv[2];
if (mode !== "preview" && mode !== "final") {
  console.error("Usage: node scripts/render.mjs <preview|final>");
  process.exit(1);
}

const run = (cmd, args, env) => {
  const r = spawnSync(cmd, args, { cwd: root, stdio: "inherit", shell: process.platform === "win32", env });
  if (r.status !== 0) process.exit(r.status ?? 1);
};

run("node", ["--disable-warning=MODULE_TYPELESS_PACKAGE_JSON", "scripts/export-timeline.mjs"]);
run("node", ["scripts/sync-renders.mjs"]);

const env = { ...process.env };
if (mode === "final") env.REMOTION_FINAL = "1";
else delete env.REMOTION_FINAL;

run("npx", ["remotion", "render", "src/index.ts", "ZiyoCommercial", `out/${mode}.mp4`], env);
