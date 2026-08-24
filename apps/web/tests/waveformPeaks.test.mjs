import assert from 'node:assert/strict';
import test from 'node:test';

import {
  auditionPlaybackAfterSeeking,
  auditionRangeAt,
  beginAuditionPlayback,
  clampPlaybackTime,
  normalizeAuditionRange,
  preserveSourceSwitchSnapshot,
  selectWaveformLevel,
  toWaveSurferPeaks,
  waveformDurationSeconds,
} from '../.test-dist/waveformPeaks.js';

function waveform(overrides = {}) {
  return {
    schema_version: '1.0.0',
    waveform_id: 'waveform:test',
    source_asset_id: 'asset:test',
    sample_rate_hz: 48_000,
    duration_us: 10_000_000,
    channels: 1,
    levels: [
      {
        samples_per_window: 960,
        windows: [
          [[-0.5, 0.75]],
          [[-1.05, 1.05]],
        ],
      },
    ],
    ...overrides,
  };
}

test('converts mono min/max windows to bounded WaveSurfer channel data', () => {
  const input = waveform();
  const channels = toWaveSurferPeaks(input);

  assert.equal(waveformDurationSeconds(input), 10);
  assert.equal(channels.length, 1);
  assert.deepEqual(Array.from(channels[0]), [-0.5, 0.75, -1, 1]);
});

test('preserves independent stereo peak channels', () => {
  const input = waveform({
    channels: 2,
    levels: [
      {
        samples_per_window: 960,
        windows: [
          [[-0.5, 0.7], [-0.25, 0.3]],
          [[-0.1, 0.2], [-0.8, 0.9]],
        ],
      },
    ],
  });

  const channels = toWaveSurferPeaks(input);
  assert.deepEqual(roundPeaks(channels[0]), [-0.5, 0.7, -0.1, 0.2]);
  assert.deepEqual(roundPeaks(channels[1]), [-0.25, 0.3, -0.8, 0.9]);
});

test('selects the finest pyramid level inside the long-file sample budget', () => {
  const levels = [
    { samples_per_window: 960, windows: Array.from({ length: 8 }, () => [[-0.1, 0.1]]) },
    { samples_per_window: 1_920, windows: Array.from({ length: 4 }, () => [[-0.1, 0.1]]) },
    { samples_per_window: 3_840, windows: Array.from({ length: 2 }, () => [[-0.1, 0.1]]) },
  ];
  const input = waveform({ levels });

  assert.equal(selectWaveformLevel(input, 8).samples_per_window, 1_920);
  assert.equal(selectWaveformLevel(input, 4).samples_per_window, 3_840);
});

test('selects a bounded level from synthetic three-hour pyramid metadata', () => {
  const input = waveform({
    duration_us: 10_800_000_000,
    levels: [
      { samples_per_window: 960, windows: new Array(540_000) },
      { samples_per_window: 1_920, windows: new Array(270_000) },
      { samples_per_window: 3_840, windows: new Array(135_000) },
      { samples_per_window: 7_680, windows: new Array(67_500) },
    ],
  });

  const selected = selectWaveformLevel(input, 240_000);
  assert.equal(selected.samples_per_window, 7_680);
  assert.equal(selected.windows.length * 2, 135_000);
});

test('rejects malformed, nonfinite, out-of-range, and channel-mismatched peaks', () => {
  assert.throws(() => toWaveSurferPeaks(waveform({ duration_us: 0 })), /duration/i);
  assert.throws(() => toWaveSurferPeaks(waveform({ sample_rate_hz: 0 })), /sample rate/i);
  assert.throws(
    () => toWaveSurferPeaks(waveform({ levels: [{ samples_per_window: 960, windows: [[[Number.NaN, 0.1]]] }] })),
    /bounds are invalid/i,
  );
  assert.throws(
    () => toWaveSurferPeaks(waveform({ levels: [{ samples_per_window: 960, windows: [[[-1.2, 0.1]]] }] })),
    /bounds are invalid/i,
  );
  assert.throws(
    () => toWaveSurferPeaks(waveform({ channels: 2 })),
    /channel count/i,
  );
});

test('creates and normalizes one bounded preview audition range', () => {
  assert.deepEqual(auditionRangeAt(98, 100, 10), { start: 90, end: 100 });
  assert.deepEqual(auditionRangeAt(-3, 100, 10), { start: 0, end: 10 });
  assert.deepEqual(normalizeAuditionRange(20, 10, 100), { start: 10, end: 20 });
  assert.deepEqual(normalizeAuditionRange(10, 200, 300), { start: 10, end: 70 });
  assert.deepEqual(normalizeAuditionRange(9, 9, 10), { start: 9, end: 9.25 });
});

test('clamps preserved A/B playback positions to the shared timeline', () => {
  assert.equal(clampPlaybackTime(12.5, 60), 12.5);
  assert.equal(clampPlaybackTime(100, 60), 60);
  assert.equal(clampPlaybackTime(Number.NaN, 60), 0);
});

test('preserves the first playback snapshot across rapid A/B load replacements', () => {
  const first = preserveSourceSwitchSnapshot(null, 42.5, 60, true, 50);
  const rapidReplacement = preserveSourceSwitchSnapshot(first, 0, 60, false, undefined);

  assert.deepEqual(first, { resumeAt: 42.5, wasPlaying: true, auditionEnd: 50 });
  assert.equal(rapidReplacement, first);
});

test('preserves an audition end through WaveSurfer programmatic seeking but clears it for user seeking', () => {
  const started = beginAuditionPlayback({ start: 12, end: 22 });
  const afterProgrammaticSeek = auditionPlaybackAfterSeeking(started, 12.01);
  const afterUserSeek = auditionPlaybackAfterSeeking(afterProgrammaticSeek, 18);

  assert.deepEqual(started, { end: 22, expectedSeek: 12 });
  assert.deepEqual(afterProgrammaticSeek, { end: 22 });
  assert.deepEqual(afterUserSeek, {});
});

function roundPeaks(values) {
  return Array.from(values, (value) => Math.round(value * 100) / 100);
}
