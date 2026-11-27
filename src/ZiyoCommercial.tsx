import React from "react";
import { AbsoluteFill, Sequence } from "remotion";
import { SceneSequence } from "./components/SceneSequence";
import { S01ExitPhoto } from "./components/S01ExitPhoto";
import { S02EntryPhoto } from "./components/S02EntryPhoto";
import { SoundLayer } from "./components/SoundLayer";
import { S01_BEATS, S02_BEATS, SCENES, sceneEnd } from "./timeline";

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
      {/* D hand-off 1 → 2, scene-2 side: projected-photo layer (exact photo pixels, alpha) over the 3D render */}
      <Sequence from={SCENES[1].from} durationInFrames={S02_BEATS.dissolveEnd - SCENES[1].from + 1} name="2. Entry photo (D hand-off)">
        <S02EntryPhoto />
      </Sequence>
      <SoundLayer />
    </AbsoluteFill>
  );
};
