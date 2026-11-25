import React from "react";
import { AbsoluteFill, Sequence } from "remotion";
import { SceneSequence } from "./components/SceneSequence";
import { SoundLayer } from "./components/SoundLayer";
import { SCENES } from "./timeline";

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
      <SoundLayer />
    </AbsoluteFill>
  );
};
