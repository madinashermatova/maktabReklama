import React from "react";
import { AbsoluteFill, Sequence } from "remotion";
import { SceneSequence } from "./components/SceneSequence";
import { S01ExitPhoto } from "./components/S01ExitPhoto";
import { SoundLayer } from "./components/SoundLayer";
import { S01_BEATS, SCENES, sceneEnd } from "./timeline";

/** Main film: all 11 scenes laid out from src/timeline.ts, plus the sound layer. */
export const ZiyoCommercial: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      {SCENES.map((scene, i) => (
        <Sequence
          key={scene.id}
          from={scene.from}
          durationInFrames={scene.durationInFrames}
          name={`${i + 1}. ${scene.name}`}
        >
          <SceneSequence scene={scene} />
        </Sequence>
      ))}
      {/* D hand-off 1 → 2: exact hero-photo pixels over the end of the scene-1 render */}
      <Sequence
        from={S01_BEATS.photoOverlayStart}
        durationInFrames={sceneEnd(SCENES[0]) - S01_BEATS.photoOverlayStart + 1}
        name="1. Exit photo (D hand-off)"
      >
        <S01ExitPhoto />
      </Sequence>
      <SoundLayer />
    </AbsoluteFill>
  );
};
