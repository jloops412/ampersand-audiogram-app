import type { WaveformPeaks } from './types';

export const DEFAULT_MAX_WAVEFORM_SAMPLES_PER_CHANNEL = 240_000;
export const MIN_AUDITION_SECONDS = 0.25;
export const MAX_AUDITION_SECONDS = 60;

export interface AuditionRange {
  start: number;
  end: number;
}

export interface SourceSwitchSnapshot {
  resumeAt: number;
  wasPlaying: boolean;
  auditionEnd?: number;
}

export interface AuditionPlaybackState {
  end?: number;
  expectedSeek?: number;
}

export type WaveformLevel = WaveformPeaks['levels'][number];

export function waveformDurationSeconds(waveform: WaveformPeaks): number {
  const duration = waveform.duration_us / 1_000_000;
  if (!Number.isFinite(duration) || duration <= 0) {
    throw new Error('Waveform duration must be a positive finite value.');
  }
  return duration;
}

export function selectWaveformLevel(
  waveform: WaveformPeaks,
  maxSamplesPerChannel = DEFAULT_MAX_WAVEFORM_SAMPLES_PER_CHANNEL,
): WaveformLevel {
  if (!Number.isSafeInteger(maxSamplesPerChannel) || maxSamplesPerChannel < 2) {
    throw new Error('Waveform sample budget must be an integer of at least two.');
  }
  const populated = waveform.levels.filter(
    (level) => Number.isSafeInteger(level.samples_per_window) && level.samples_per_window > 0 && level.windows.length > 0,
  );
  if (!populated.length) throw new Error('Waveform does not contain a populated peak level.');

  const ordered = [...populated].sort((left, right) => left.samples_per_window - right.samples_per_window);
  return ordered.find((level) => level.windows.length * 2 <= maxSamplesPerChannel) ?? ordered[ordered.length - 1];
}

export function toWaveSurferPeaks(
  waveform: WaveformPeaks,
  maxSamplesPerChannel = DEFAULT_MAX_WAVEFORM_SAMPLES_PER_CHANNEL,
): Float32Array[] {
  waveformDurationSeconds(waveform);
  if (!Number.isSafeInteger(waveform.channels) || waveform.channels <= 0) {
    throw new Error('Waveform channel count must be a positive integer.');
  }
  if (!Number.isSafeInteger(waveform.sample_rate_hz) || waveform.sample_rate_hz <= 0) {
    throw new Error('Waveform sample rate must be a positive integer.');
  }

  const level = selectWaveformLevel(waveform, maxSamplesPerChannel);
  const channels = Array.from(
    { length: waveform.channels },
    () => new Float32Array(level.windows.length * 2),
  );

  level.windows.forEach((window, windowIndex) => {
    if (!Array.isArray(window) || window.length !== waveform.channels) {
      throw new Error('Waveform peak window does not match its declared channel count.');
    }
    window.forEach((bounds, channelIndex) => {
      if (!Array.isArray(bounds) || bounds.length !== 2) {
        throw new Error('Waveform peak bounds must contain one minimum and maximum.');
      }
      const [minimum, maximum] = bounds;
      if (
        !Number.isFinite(minimum) ||
        !Number.isFinite(maximum) ||
        minimum < -1.1 ||
        maximum > 1.1 ||
        minimum > maximum
      ) {
        throw new Error('Waveform peak bounds are invalid.');
      }
      const offset = windowIndex * 2;
      channels[channelIndex][offset] = clamp(minimum, -1, 1);
      channels[channelIndex][offset + 1] = clamp(maximum, -1, 1);
    });
  });

  return channels;
}

export function auditionRangeAt(
  playheadSeconds: number,
  durationSeconds: number,
  requestedLengthSeconds = 10,
): AuditionRange {
  assertDuration(durationSeconds);
  const minimumLength = Math.min(MIN_AUDITION_SECONDS, durationSeconds);
  const length = clamp(requestedLengthSeconds, minimumLength, Math.min(MAX_AUDITION_SECONDS, durationSeconds));
  const requestedStart = clamp(playheadSeconds, 0, durationSeconds);
  const start = Math.min(requestedStart, durationSeconds - length);
  return { start, end: start + length };
}

export function normalizeAuditionRange(
  firstSeconds: number,
  secondSeconds: number,
  durationSeconds: number,
): AuditionRange {
  assertDuration(durationSeconds);
  if (!Number.isFinite(firstSeconds) || !Number.isFinite(secondSeconds)) {
    throw new Error('Audition bounds must be finite.');
  }
  const minimumLength = Math.min(MIN_AUDITION_SECONDS, durationSeconds);
  const maximumLength = Math.min(MAX_AUDITION_SECONDS, durationSeconds);
  let start = clamp(Math.min(firstSeconds, secondSeconds), 0, durationSeconds);
  let end = clamp(Math.max(firstSeconds, secondSeconds), 0, durationSeconds);

  if (end - start < minimumLength) {
    end = Math.min(durationSeconds, start + minimumLength);
    start = Math.max(0, end - minimumLength);
  }
  if (end - start > maximumLength) end = start + maximumLength;
  return { start, end };
}

export function clampPlaybackTime(timeSeconds: number, durationSeconds: number): number {
  assertDuration(durationSeconds);
  return Number.isFinite(timeSeconds) ? clamp(timeSeconds, 0, durationSeconds) : 0;
}

export function preserveSourceSwitchSnapshot(
  pending: SourceSwitchSnapshot | null,
  currentTimeSeconds: number,
  durationSeconds: number,
  wasPlaying: boolean,
  auditionEnd?: number,
): SourceSwitchSnapshot {
  if (pending) return pending;
  const resumeAt = clampPlaybackTime(currentTimeSeconds, durationSeconds);
  const boundedAuditionEnd = auditionEnd == null
    ? undefined
    : clampPlaybackTime(auditionEnd, durationSeconds);
  return {
    resumeAt,
    wasPlaying,
    auditionEnd: boundedAuditionEnd && boundedAuditionEnd > resumeAt ? boundedAuditionEnd : undefined,
  };
}

export function beginAuditionPlayback(range: AuditionRange): AuditionPlaybackState {
  return { end: range.end, expectedSeek: range.start };
}

export function auditionPlaybackAfterSeeking(
  state: AuditionPlaybackState,
  seekTimeSeconds: number,
): AuditionPlaybackState {
  if (
    state.end != null &&
    state.expectedSeek != null &&
    Number.isFinite(seekTimeSeconds) &&
    Math.abs(seekTimeSeconds - state.expectedSeek) <= 0.05
  ) {
    return { end: state.end };
  }
  return {};
}

function assertDuration(durationSeconds: number): void {
  if (!Number.isFinite(durationSeconds) || durationSeconds <= 0) {
    throw new Error('Audio duration must be a positive finite value.');
  }
}

function clamp(value: number, minimum: number, maximum: number): number {
  return Math.min(maximum, Math.max(minimum, value));
}
