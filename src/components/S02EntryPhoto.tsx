import React from "react";
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from "remotion";
import renders from "../generated/renders.json";

/** Manifest id of the projected-photo layer (renders/s02_turnstile_proj/, rendered from blender/kit/entrance.blend). */
const LAYER_ID = "s02_turnstile_proj";

type RenderEntry = { dir: string; first: number; count: number; pad: number; ext: string };
const manifest = renders as Record<string, RenderEntry | undefined>;

/**
 * D hand-off 1 → 2, scene-2 side. The ENTRANCE_PROJ layer holds the exact hero-photo pixels projected onto the 3D
 * replica from the scene-2 camera, with alpha fading per surface (grazing surfaces hand over to 3D first) until it is
 * fully transparent at S02_BEATS.dissolveEnd. Laid over the scene-2 render with straight alpha:
 *   final = render · (1 − α) + photo · α   (same operation as tools/composite_handoff.py).
 * Played by scene-local index. Place inside a <Sequence from={SCENES[1].from}>. Renders nothing until the layer exists.
 */
export const S02EntryPhoto: React.FC = () => {
  const frame = useCurrentFrame();
  const entry = manifest[LAYER_ID];
  if (!entry || frame >= entry.count) return null;
  const n = String(entry.first + frame).padStart(entry.pad, "0");
  return (
    <AbsoluteFill>
      <Img src={staticFile(`${entry.dir}/${n}.${entry.ext}`)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
    </AbsoluteFill>
  );
};
