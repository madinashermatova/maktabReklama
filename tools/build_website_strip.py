"""Stack the 7 scene-1 website pages (renders/_website/pages/, from `npm run website:render`) top → bottom into one
vertical strip texture: blender/kit/textures/website_strip.png (school website LAST). Page size is read from the
files (1920×1080 base; any 16:9 size works), so the strip stays resolution-independent.

    tools/py.sh tools/build_website_strip.py
"""

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
pages = sorted((ROOT / "renders" / "_website" / "pages").glob("*.png"))
assert len(pages) == 7 and "School" in pages[-1].name, [p.name for p in pages]
ims = [Image.open(p).convert("RGB") for p in pages]
w, h = ims[0].size
assert all(i.size == (w, h) for i in ims)
strip = Image.new("RGB", (w, h * len(ims)))
for k, im in enumerate(ims):
    strip.paste(im, (0, k * h))
out = ROOT / "blender" / "kit" / "textures" / "website_strip.png"
out.parent.mkdir(parents=True, exist_ok=True)
strip.save(out, optimize=True)
print(f"strip {strip.size[0]}x{strip.size[1]} ({len(ims)} pages) -> {out}")
for k, p in enumerate(pages):
    print(f"  page {k}: {p.name}")
