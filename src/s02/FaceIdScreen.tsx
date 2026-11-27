import React, { useMemo } from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { S02_BEATS, SCENES } from "../timeline";

/**
 * Scene 2 Face ID terminal display (portrait 9:16), rendered to renders/_faceid/####.png (absolute film frames) by
 * `npm run faceid:render` and used by blender/scripts/scene_02_turnstile.py as the screen's image-sequence texture.
 *
 * Content rule (CLAUDE.md / storyboard): ONLY an abstract dot/mesh grid — a rounded-square lattice of 20 × 20 points
 * joined by thin triangulated lines, gently undulating like a surface. Red while locked / scanning, green when granted. No face, head, silhouette or body shape
 * (no oval, eyes, nose, mouth or shoulders), no text — colour and one generic check glyph only.
 */
const N = 20;
const SCENE2 = SCENES[1];

const RED_DIM = [232, 58, 64];
const RED_LIT = [255, 168, 160];
const WHITE = [255, 255, 255];
const GREEN = [64, 228, 140];

const mix = (a: number[], b: number[], t: number) => a.map((v, i) => v + (b[i] - v) * t);
const rgba = (c: number[], a: number) => `rgba(${c.map((v) => Math.round(v)).join(",")},${a.toFixed(3)})`;
const clamp01 = (t: number) => Math.min(1, Math.max(0, t));
const smooth = (t: number) => {
  const x = clamp01(t);
  return x * x * (3 - 2 * x);
};

type Pt = { i: number; j: number; u: number; v: number };

export const FaceIdScreen: React.FC = () => {
  const { width, height } = useVideoConfig();
  const frame = SCENE2.from + useCurrentFrame(); // absolute film frame
  const t = frame / 30;

  // Lattice points inside a rounded SQUARE (superellipse |u|^8 + |v|^8 ≤ 1: only the 4 corner points trimmed) — never an oval.
  const points = useMemo(() => {
    const pts: (Pt | null)[][] = [];
    for (let i = 0; i < N; i++) {
      pts.push([]);
      for (let j = 0; j < N; j++) {
        const u = (i / (N - 1)) * 2 - 1;
        const v = (j / (N - 1)) * 2 - 1;
        pts[i].push(u ** 8 + v ** 8 <= 1.0 ? { i, j, u, v } : null);
      }
    }
    return pts;
  }, []);

  // Gently undulating surface, tilted back a little and projected with mild perspective.
  const side = width * 0.74;
  const cx = width / 2;
  const cy = height * 0.46;
  const tilt = (8 * Math.PI) / 180; // small, so the outline stays square (no tapering toward the bottom)
  const project = (p: Pt) => {
    const z =
      0.07 * Math.sin(2.2 * p.u + 1.25 * t) + 0.055 * Math.sin(1.8 * p.v - 0.95 * t) + 0.035 * Math.sin(3.1 * (p.u + p.v) + 1.6 * t);
    const y3 = p.v * Math.cos(tilt) - z * Math.sin(tilt);
    const z3 = p.v * Math.sin(tilt) + z * Math.cos(tilt);
    const k = 1 / (1 + 0.05 * z3);
    return { x: cx + p.u * (side / 2) * k, y: cy + y3 * (side / 2) * k, z };
  };

  // Scan line: top → bottom of the lattice; dots behind the line stay lit.
  const scanP = interpolate(frame, [S02_BEATS.scanStart, S02_BEATS.scanEnd], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });
  const scanning = frame >= S02_BEATS.scanStart && frame <= S02_BEATS.scanEnd + 4;
  const top = cy - (side / 2) * Math.cos(tilt) * 1.05;
  const bottom = cy + (side / 2) * Math.cos(tilt) * 1.05;
  const scanY = top + (bottom - top) * scanP;
  const granted = smooth((frame - S02_BEATS.granted) / 7);
  const breathe = 0.5 + 0.5 * Math.sin(t * 2.1);
  const wake = smooth((frame - (S02_BEATS.scanStart - 12)) / 12); // display brightens as the scan begins

  const proj = points.map((row) => row.map((p) => (p ? { ...project(p), p } : null)));

  const dotStyle = (y: number) => {
    const passed = frame >= S02_BEATS.scanStart && y <= scanY;
    const near = scanning ? Math.exp(-(((y - scanY) / (height * 0.018)) ** 2)) : 0;
    const lit = passed ? 1 : 0;
    let col = mix(RED_DIM, RED_LIT, lit);
    col = mix(col, WHITE, near);
    col = mix(col, GREEN, granted);
    const a = 0.42 + 0.1 * breathe * (1 - wake) + 0.4 * wake * lit + 0.45 * near + 0.5 * granted;
    const r = width * (0.0062 + 0.0035 * lit + 0.004 * near + 0.0022 * granted);
    return { col, a: Math.min(1, a), r, lit: Math.max(lit, near) };
  };

  const lines: React.ReactNode[] = [];
  const dots: React.ReactNode[] = [];
  for (let i = 0; i < N; i++) {
    for (let j = 0; j < N; j++) {
      const a = proj[i][j];
      if (!a) continue;
      const nbrs = [proj[i + 1]?.[j], proj[i]?.[j + 1], proj[i + 1]?.[j + 1]];
      for (const [k, b] of nbrs.entries()) {
        if (!b) continue;
        const s = dotStyle((a.y + b.y) / 2);
        const alpha = (0.22 + 0.28 * s.lit + 0.25 * granted) * (k === 2 ? 0.75 : 1);
        lines.push(
          <line
            key={`l${i}-${j}-${k}`}
            x1={a.x}
            y1={a.y}
            x2={b.x}
            y2={b.y}
            stroke={rgba(s.col, alpha)}
            strokeWidth={width * 0.0022}
          />,
        );
      }
      const s = dotStyle(a.y);
      dots.push(<circle key={`d${i}-${j}`} cx={a.x} cy={a.y} r={s.r} fill={rgba(s.col, s.a)} />);
    }
  }

  // Generic check glyph at the lattice centre.
  const ck = width * 0.15 * interpolate(granted, [0, 1], [0.9, 1]);
  const checkPath = `M ${cx - ck * 0.55} ${cy + ck * 0.02} L ${cx - ck * 0.12} ${cy + ck * 0.42} L ${cx + ck * 0.6} ${cy - ck * 0.38}`;
  const checkDraw = smooth((frame - S02_BEATS.granted - 2) / 9);

  const bandH = height * 0.05;
  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 46%, #1A0B0E 0%, #0C0507 62%, #050203 100%)" }}>
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
        <defs>
          <linearGradient id="scanband" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="rgba(255,140,140,0)" />
            <stop offset="0.85" stopColor="rgba(255,170,165,0.30)" />
            <stop offset="1" stopColor="rgba(255,240,238,0.95)" />
          </linearGradient>
          <radialGradient id="okglow">
            <stop offset="0" stopColor="rgba(64,228,140,0.38)" />
            <stop offset="1" stopColor="rgba(64,228,140,0)" />
          </radialGradient>
        </defs>
        <g>{lines}</g>
        <g>{dots}</g>
        {scanning ? (
          <rect x={width * 0.08} y={scanY - bandH} width={width * 0.84} height={bandH} fill="url(#scanband)" opacity={0.9} />
        ) : null}
        {granted > 0 ? (
          <>
            <circle cx={cx} cy={cy} r={width * 0.3} fill="url(#okglow)" opacity={granted} />
            <path
              d={checkPath}
              fill="none"
              stroke={rgba([235, 255, 242], granted)}
              strokeWidth={width * 0.028}
              strokeLinecap="round"
              strokeLinejoin="round"
              pathLength={1}
              strokeDasharray={1}
              strokeDashoffset={1 - checkDraw}
            />
          </>
        ) : null}
        {/* status bar: three generic indicator dots (no text) */}
        {[0, 1, 2].map((k) => (
          <circle
            key={`s${k}`}
            cx={width * (0.44 + k * 0.06)}
            cy={height * 0.9}
            r={width * 0.009}
            fill={rgba(mix(RED_DIM, GREEN, granted), 0.35 + 0.5 * (scanning ? (Math.floor(frame / 4) % 3 === k ? 1 : 0) : granted))}
          />
        ))}
      </svg>
    </AbsoluteFill>
  );
};
