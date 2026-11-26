// Fonts for the scene-1 websites. All SIL OFL 1.1 (licences next to the files in assets/fonts/), mirrored to
// public/fonts/ by scripts/sync-renders.mjs. loadFont() holds the render (delayRender) until each font is ready,
// and every text style names ONLY these families — no fallback font is ever used (CLAUDE.md → BRAND).
// Glyph coverage of every string on the pages is checked by tools/check_website_glyphs.py (docs/status.md).
import { loadFont } from "@remotion/fonts";
import { staticFile } from "remotion";

export const FONT = {
  /** Brand wordmark — Montserrat Bold (static file, glyph check recorded in docs/status.md). */
  brand: "ZY Montserrat Bold",
  montserrat: "ZY Montserrat",
  inter: "ZY Inter",
  playfair: "ZY Playfair Display",
  grotesk: "ZY Space Grotesk",
} as const;

const FILES: { family: string; file: string; weight: string }[] = [
  { family: FONT.brand, file: "fonts/Montserrat-Bold.ttf", weight: "700" },
  { family: FONT.montserrat, file: "fonts/montserrat-var/Montserrat.ttf", weight: "100 900" },
  { family: FONT.inter, file: "fonts/inter/Inter.ttf", weight: "100 900" },
  { family: FONT.playfair, file: "fonts/playfair/PlayfairDisplay.ttf", weight: "400 900" },
  { family: FONT.grotesk, file: "fonts/spacegrotesk/SpaceGrotesk.ttf", weight: "300 700" },
];

for (const f of FILES) {
  loadFont({ family: f.family, url: staticFile(f.file), weight: f.weight, format: "truetype" });
}
