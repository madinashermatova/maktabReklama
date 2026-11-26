import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame } from "remotion";
import { BRAND_WORDMARK, logoFile } from "../../brand";
import { S01_BEATS as B } from "../../timeline";
import { FONT } from "../fonts";
import { Abs, useU } from "../kit";

/**
 * ZIYO YOG’DUSI website hero (scene 1). Hero image = the approved REAL entrance photo (assets/hero, sky replaced
 * only) — full-bleed and never altered; UI elements sit on top and fade away after the click so that the plain photo
 * fills the screen for the 1 → 2 hand-off. Frame numbers = film frames (S01_BEATS in src/timeline.ts).
 * Text: wordmark (no quotes, no other words beside it), Uzbek navigation and factual labels only — no claims, numbers
 * or prices beyond the real facts (grades 1–11, Samarkand region, private school).
 */
export const TEAL = "#2F6E73";
export const AMBER = "#E3A33B";

/** Primary button geometry in design pixels (the cursor aims at its centre). */
export const HERO_BUTTON = { x: 120, y: 790, w: 412, h: 76 };

const ease = Easing.bezier(0.45, 0, 0.2, 1);
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

export const School: React.FC = () => {
  const f = useCurrentFrame();
  const u = useU();

  const ui = interpolate(f, [B.uiFadeStart, B.uiFadeEnd], [1, 0], { ...clamp, easing: ease });
  const uiLift = (1 - ui) * -10 * u;
  const hover = interpolate(f, [B.cursorArrive - 4, B.cursorArrive + 1], [0, 1], { ...clamp, easing: ease });
  const press = interpolate(f, [B.click - 1, B.click + 1, B.click + 7], [0, 1, 0], { ...clamp, easing: ease });
  const btnScale = 1 - 0.045 * press;

  const bx = HERO_BUTTON.x + HERO_BUTTON.w / 2;
  const by = HERO_BUTTON.y + HERO_BUTTON.h / 2;
  const rip = interpolate(f, [B.click, B.click + 20], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
  const ripOpacity = f < B.click ? 0 : 0.55 * (1 - rip);

  // cursor: eased curved path from the lower right to the button, small press at the click, fades with the UI
  const t = interpolate(f, [B.cursorIn, B.cursorArrive], [0, 1], { ...clamp, easing: Easing.bezier(0.33, 0, 0.15, 1) });
  const p0 = { x: 1180, y: 1010 };
  const p1 = { x: 900, y: 700 }; // control point → gentle arc
  const p2 = { x: bx + 40, y: by + 6 };
  const cx = (1 - t) ** 2 * p0.x + 2 * (1 - t) * t * p1.x + t ** 2 * p2.x;
  const cy = (1 - t) ** 2 * p0.y + 2 * (1 - t) * t * p1.y + t ** 2 * p2.y;
  const cursorIn = interpolate(f, [B.cursorIn, B.cursorIn + 5], [0, 1], clamp);
  const cursorOpacity = Math.min(cursorIn, ui);
  const cursorScale = 1 - 0.12 * press;

  const navItems = ["Bosh sahifa", "Biz haqimizda", "Qabul", "Aloqa"];

  return (
    <AbsoluteFill style={{ backgroundColor: "#0B1416", fontFamily: FONT.montserrat, overflow: "hidden" }}>
      {/* the real photo, exactly as approved — full frame, no crop (1920×1080 source) */}
      <Img src={staticFile("hero/entrance_hero_1920.png")} style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }} />

      <AbsoluteFill style={{ opacity: ui, transform: `translateY(${uiLift}px)` }}>
        {/* legibility scrims (UI layer only; the photo itself is untouched) */}
        <AbsoluteFill
          style={{
            background:
              "linear-gradient(90deg, rgba(8,22,24,0.80) 0%, rgba(8,22,24,0.55) 26%, rgba(8,22,24,0.0) 48%), linear-gradient(180deg, rgba(8,22,24,0.55) 0%, rgba(8,22,24,0) 16%)",
          }}
        />
        {/* header */}
        <Abs
          style={{
            left: 40 * u,
            right: 40 * u,
            top: 28 * u,
            height: 88 * u,
            borderRadius: 22 * u,
            background: "rgba(14,28,30,0.42)",
            border: `${1 * u}px solid rgba(255,255,255,0.16)`,
            backdropFilter: `blur(${18 * u}px)`,
            display: "flex",
            alignItems: "center",
            padding: `0 ${44 * u}px`,
          }}
        >
          {logoFile ? (
            <Img src={staticFile(`brand/${logoFile}`)} style={{ height: 46 * u, marginRight: 18 * u }} />
          ) : null}
          <div style={{ fontFamily: FONT.brand, fontWeight: 700, fontSize: 30 * u, letterSpacing: 3.2 * u, color: "white" }}>
            {BRAND_WORDMARK}
          </div>
          <div style={{ flex: 1 }} />
          <div style={{ display: "flex", alignItems: "center", gap: 50 * u, fontSize: 19 * u, fontWeight: 500, color: "rgba(255,255,255,0.88)" }}>
            {navItems.map((n, i) =>
              i === navItems.length - 1 ? (
                <div key={n} style={{ border: `${1.5 * u}px solid rgba(255,255,255,0.6)`, borderRadius: 30 * u, padding: `${11 * u}px ${28 * u}px`, color: "white", fontWeight: 600 }}>
                  {n}
                </div>
              ) : (
                <div key={n} style={{ position: "relative", color: i === 0 ? "white" : undefined, fontWeight: i === 0 ? 600 : 500 }}>
                  {n}
                  {i === 0 ? (
                    <div style={{ position: "absolute", left: 0, right: 0, bottom: -12 * u, height: 3 * u, borderRadius: 2 * u, background: AMBER }} />
                  ) : null}
                </div>
              ),
            )}
          </div>
        </Abs>

        {/* hero copy — facts only */}
        <Abs style={{ left: 120 * u, top: 470 * u, color: "white", width: 820 * u }}>
          <div style={{ display: "flex", alignItems: "center", gap: 18 * u, fontSize: 18 * u, fontWeight: 600, letterSpacing: 4 * u, color: AMBER }}>
            <div style={{ width: 46 * u, height: 2 * u, background: AMBER }} />
            SAMARQAND VILOYATI
          </div>
          <div style={{ fontSize: 76 * u, fontWeight: 700, lineHeight: 1.06, marginTop: 22 * u, letterSpacing: -1 * u }}>
            1–11-sinflar uchun
            <br />
            xususiy maktab
          </div>
        </Abs>

        {/* buttons */}
        <Abs
          style={{
            left: HERO_BUTTON.x * u,
            top: HERO_BUTTON.y * u,
            width: HERO_BUTTON.w * u,
            height: HERO_BUTTON.h * u,
            borderRadius: 40 * u,
            background: AMBER,
            color: "#1B1408",
            fontSize: 21 * u,
            fontWeight: 700,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 14 * u,
            transform: `scale(${btnScale})`,
            boxShadow: `0 ${(14 - 8 * press) * u}px ${(36 - 16 * press) * u}px rgba(227,163,59,${0.28 + 0.22 * hover})`,
            filter: `brightness(${1 + 0.08 * hover - 0.06 * press})`,
          }}
        >
          Maktab bilan tanishing
          <svg viewBox="0 0 24 24" width={24 * u} height={24 * u}>
            <path d="M4 12h15M13 6l6 6-6 6" fill="none" stroke="#1B1408" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </Abs>
        <Abs
          style={{
            left: (HERO_BUTTON.x + HERO_BUTTON.w + 22) * u,
            top: HERO_BUTTON.y * u,
            height: HERO_BUTTON.h * u,
            padding: `0 ${38 * u}px`,
            borderRadius: 40 * u,
            border: `${1.5 * u}px solid rgba(255,255,255,0.55)`,
            background: "rgba(255,255,255,0.08)",
            backdropFilter: `blur(${10 * u}px)`,
            color: "white",
            fontSize: 21 * u,
            fontWeight: 600,
            display: "flex",
            alignItems: "center",
          }}
        >
          Qabul haqida
        </Abs>

        {/* teal accent rail + scroll hint */}
        <Abs style={{ left: 120 * u, top: 912 * u, width: 140 * u, height: 4 * u, borderRadius: 2 * u, background: TEAL }} />
        <Abs style={{ right: 70 * u, bottom: 56 * u, width: 30 * u, height: 48 * u, borderRadius: 16 * u, border: `${2 * u}px solid rgba(255,255,255,0.7)` }}>
          <div style={{ position: "absolute", left: 12 * u, top: 9 * u, width: 3 * u, height: 10 * u, borderRadius: 2 * u, background: "white" }} />
        </Abs>

        {/* click ripple */}
        <Abs
          style={{
            left: (bx - 40) * u,
            top: (by - 40) * u,
            width: 80 * u,
            height: 80 * u,
            borderRadius: "50%",
            border: `${3 * u}px solid rgba(255,244,220,1)`,
            background: "rgba(255,244,220,0.25)",
            opacity: ripOpacity,
            transform: `scale(${0.3 + 3.2 * rip})`,
          }}
        />
      </AbsoluteFill>

      {/* cursor — generic arrow, no hand */}
      <svg
        viewBox="0 0 24 34"
        width={30 * u}
        height={42 * u}
        style={{
          position: "absolute",
          left: cx * u,
          top: cy * u,
          opacity: cursorOpacity,
          transform: `scale(${cursorScale})`,
          transformOrigin: "0 0",
          filter: `drop-shadow(0 ${3 * u}px ${4 * u}px rgba(0,0,0,0.35))`,
        }}
      >
        <path d="M2 2 L2 27 L8.6 21 L12.8 31 L17.2 29.2 L13 19.6 L21.6 19.6 Z" fill="white" stroke="#14181C" strokeWidth="1.8" strokeLinejoin="round" />
      </svg>
    </AbsoluteFill>
  );
};
