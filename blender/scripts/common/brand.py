"""Single source of truth for brand text in Blender scripts (CLAUDE.md → BRAND). Mirrors src/brand.ts.

Apostrophe = U+2019 (’), exactly as on the real signboard (user decision 2026-11-26).
"""

APOSTROPHE = "’"

#: Website (scene 1) and brand reveal (scene 11): the name only — no quotes, no other words.
BRAND_WORDMARK = f"ZIYO YOG{APOSTROPHE}DUSI"

#: The real entrance signboard, replicated only on the 3D sign (scenes 1–2).
SIGNBOARD_TEXT = f"“{BRAND_WORDMARK}” XUSUSIY MAKTABI"

assert len(APOSTROPHE) == 1 and ord(APOSTROPHE) == 0x2019
