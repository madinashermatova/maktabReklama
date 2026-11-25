import React from "react";
import { Html5Audio, Sequence, staticFile } from "remotion";
import { MUSIC, SOUND_CUES } from "../soundCues";

/** Music bed + every sound-synced SFX cue from src/soundCues.ts. Empty until cues are locked. */
export const SoundLayer: React.FC = () => {
  return (
    <>
      {MUSIC ? (
        <Html5Audio src={staticFile(`audio/${MUSIC.file}`)} volume={MUSIC.volume} trimBefore={MUSIC.trimBefore} />
      ) : null}
      {SOUND_CUES.map((cue) => (
        <Sequence key={cue.id} from={cue.frame} durationInFrames={cue.durationInFrames} name={`SFX ${cue.id}`} layout="none">
          <Html5Audio src={staticFile(`audio/${cue.file}`)} volume={cue.volume ?? 1} />
        </Sequence>
      ))}
    </>
  );
};
