import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { S01_BEATS, s01PhotoScale } from "../timeline";

/**
 * D hand-off, scene-1 side: over the last frames of scene 1 the exact hero-photo pixels are laid over the Blender
 * render at the same scale the Blender camera sees (s01PhotoScale), so frame 269 equals scene 2's photo layer
 * one frame earlier. Place inside a <Sequence from={S01_BEATS.photoOverlayStart}>.
 */
export const S01ExitPhoto: React.FC = () => {
  const local = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const frame = S01_BEATS.photoOverlayStart + local;
  const s = s01PhotoScale(frame);
  const opacity = interpolate(frame, [S01_BEATS.photoOverlayStart, S01_BEATS.photoOverlayEnd], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.sin),
  });
  const w = width * s;
  const h = (w * 9) / 16;
  return (
    <AbsoluteFill style={{ opacity }}>
      <Img
        src={staticFile("hero/entrance_hero_1920.png")}
        style={{ position: "absolute", width: w, height: h, left: (width - w) / 2, top: (height - h) / 2 }}
      />
    </AbsoluteFill>
  );
};
