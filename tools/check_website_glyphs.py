"""Glyph coverage of the scene-1 website fonts (CLAUDE.md → BRAND: no font fallback, ever).

    tools/py.sh tools/check_website_glyphs.py

Checks every font loaded in src/website/fonts.ts against printable ASCII plus every non-ASCII character that
appears in src/website/**/*.tsx and src/brand.ts (’ “ ” – — − ·). Prints missing characters per font; exit 1
if the brand font misses anything in the wordmark or any font misses a used character.
"""

import sys
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = {
    "Montserrat Bold (wordmark)": "assets/fonts/Montserrat-Bold.ttf",
    "Montserrat (variable)": "assets/fonts/montserrat-var/Montserrat.ttf",
    "Inter": "assets/fonts/inter/Inter.ttf",
    "Playfair Display": "assets/fonts/playfair/PlayfairDisplay.ttf",
    "Space Grotesk": "assets/fonts/spacegrotesk/SpaceGrotesk.ttf",
}
src = "".join(p.read_text(encoding="utf-8") for p in sorted((ROOT / "src" / "website").rglob("*.tsx")))
src += (ROOT / "src" / "brand.ts").read_text(encoding="utf-8")
used = {chr(c) for c in range(0x20, 0x7F)} | {ch for ch in src if ord(ch) > 0x7E}
# characters that appear only in code comments (never rendered); everything else is checked conservatively
used -= {"→", "×", "…"}
bad = False
for name, rel in FONTS.items():
    cmap = TTFont(ROOT / rel).getBestCmap()
    missing = sorted(ch for ch in used if ord(ch) not in cmap)
    shown = " ".join(f"{ch!r}(U+{ord(ch):04X})" for ch in missing) or "none"
    print(f"{name:28s} {len(used)} chars checked, missing: {shown}")
    if missing:
        bad = True
print("non-ASCII used:", " ".join(f"{ch}(U+{ord(ch):04X})" for ch in sorted(used) if ord(ch) > 0x7E))
sys.exit(1 if bad else 0)
