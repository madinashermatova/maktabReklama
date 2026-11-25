// Sound layer data. Mirrors docs/sound-cues.md (the human-readable cue sheet) once frames are locked.
// Files are served from public/audio/ (copied from assets/audio/ by scripts/sync-renders.mjs).
// SFX come only from ElevenLabs text_to_sound_effects (assets/audio/sfx/); music only from assets/audio/music/.
// There is no voice in this film — never add voice/TTS files here.

export type SoundCue = {
  /** Unique id, matches the row in docs/sound-cues.md. */
  id: string;
  /** Absolute film frame where the sound starts. */
  frame: number;
  /** Path relative to public/audio/, e.g. "sfx/s02_confirm_beep.mp3". */
  file: string;
  /** 0–1, default 1. */
  volume?: number;
  /** Optional cut length in frames. */
  durationInFrames?: number;
};

export type MusicTrack = {
  /** Path relative to public/audio/, e.g. "music/track.mp3". */
  file: string;
  volume: number;
  /** Frames to skip at the start of the music file. */
  trimBefore?: number;
};

export const MUSIC: MusicTrack | null = null;

export const SOUND_CUES: SoundCue[] = [];
