// Single source of truth for brand text in Remotion (CLAUDE.md → BRAND).
// Apostrophe = U+2019 (’), exactly as on the real signboard (user decision 2026-11-26).

export const APOSTROPHE = "’";

/** Website (scene 1) and brand reveal (scene 11): the name only — no quotes, no other words. */
export const BRAND_WORDMARK = `ZIYO YOG${APOSTROPHE}DUSI`;

/** The real entrance signboard, replicated only on the 3D sign (scenes 1–2). */
export const SIGNBOARD_TEXT = `“${BRAND_WORDMARK}” XUSUSIY MAKTABI`;

/** Optional logo in assets/brand/ — none exists yet, so only the wordmark is shown. */
export const logoFile: string | null = null;
