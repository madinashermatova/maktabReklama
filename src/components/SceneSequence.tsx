import React from "react";
import { AbsoluteFill, Img, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import renders from "../generated/renders.json";
import { type SceneDef, SCENES, sceneEnd } from "../timeline";

/** One entry per scene, written by scripts/sync-renders.mjs after scanning public/renders/<id>/. */
type RenderEntry = {
  dir: string; // folder inside public/
  first: number; // number in the first file name (the .blend numbering: film frame, or SceneDef.blendFrom)
  count: number; // contiguous frames available from `first`
  pad: number; // zero padding of the file names
  ext: string; // "png"
};
const manifest = renders as Record<string, RenderEntry | undefined>;

/**
 * Plays a scene's rendered frame sequence frame-accurately by SCENE-LOCAL index (file first + local frame), so a scene
 * moved on the timeline after rendering (SceneDef.blendFrom) still plays its frames at its new position.
 * Plays it if it exists in public/renders/<id>/,
 * otherwise (or past the last rendered frame) shows a clearly labelled PLACEHOLDER card.
 * Must be placed inside a <Sequence> starting at scene.from, so useCurrentFrame() is scene-local.
 */
export const SceneSequence: React.FC<{ scene: SceneDef }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const entry = manifest[scene.id];

  if (entry && frame < entry.count) {
    const n = String(entry.first + frame).padStart(entry.pad, "0");
    return (
      <AbsoluteFill>
        <Img
          src={staticFile(`${entry.dir}/${n}.${entry.ext}`)}
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
      </AbsoluteFill>
    );
  }

  return <PlaceholderCard scene={scene} rendered={entry?.count ?? 0} />;
};

const PlaceholderCard: React.FC<{ scene: SceneDef; rendered: number }> = ({ scene, rendered }) => {
  const frame = useCurrentFrame();
  const { width, fps } = useVideoConfig();
  const u = width / 1920; // resolution-independent unit: 1 px at 1080p
  const index = SCENES.findIndex((s) => s.id === scene.id) + 1;
  const absolute = scene.from + frame;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#16161c",
        color: "#e8e8ee",
        fontFamily: "system-ui, sans-serif",
        justifyContent: "center",
        alignItems: "center",
        gap: 28 * u,
      }}
    >
      <div
        style={{
          backgroundColor: "#FF00FF",
          color: "#000",
          fontWeight: 800,
          fontSize: 44 * u,
          letterSpacing: 6 * u,
          padding: `${10 * u}px ${28 * u}px`,
        }}
      >
        PLACEHOLDER
      </div>
      <div style={{ fontSize: 96 * u, fontWeight: 700 }}>
        {index}. {scene.name}
      </div>
      <div style={{ fontSize: 40 * u, opacity: 0.8, fontVariantNumeric: "tabular-nums" }}>
        frames {scene.from}–{sceneEnd(scene)} · {scene.durationInFrames} f · {(scene.durationInFrames / fps).toFixed(1)} s ·{" "}
        {scene.source}
      </div>
      <div style={{ fontSize: 32 * u, opacity: 0.6, fontVariantNumeric: "tabular-nums" }}>
        film frame {absolute} · scene frame {frame}
        {rendered > 0 ? ` · ${rendered}/${scene.durationInFrames} frames rendered` : ""}
      </div>
    </AbsoluteFill>
  );
};
