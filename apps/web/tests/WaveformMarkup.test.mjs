import assert from 'node:assert/strict';
import test from 'node:test';

import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

import { Waveform } from '../.test-dist/Waveform.js';

const VALID_WAVEFORM = {
  schema_version: '1.0.0',
  waveform_id: 'waveform:test',
  source_asset_id: 'asset:test',
  sample_rate_hz: 48_000,
  duration_us: 30_000_000,
  channels: 1,
  levels: [{ samples_per_window: 960, windows: [[[-0.5, 0.5]], [[-0.25, 0.25]]] }],
};

test('renders an accessible source timeline and honest preview-only audition controls', () => {
  const markup = renderToStaticMarkup(
    React.createElement(Waveform, {
      waveform: VALID_WAVEFORM,
      audioUrl: '/api/v2/productions/test/media/wav',
      sourceLabel: 'Master',
    }),
  );

  assert.match(markup, />Source timeline</);
  assert.match(markup, /Interactive source waveform/);
  assert.match(markup, /Timeline zoom/);
  assert.match(markup, /Set 10s here/);
  assert.match(markup, /Set in/);
  assert.match(markup, /Set out/);
  assert.match(markup, /Play selection/);
  assert.match(markup, /This does not change, trim, or re-render exports/);
  assert.match(markup, /aria-label="Master audio"/);
  assert.doesNotMatch(markup, /contenteditable/);
});

test('fails closed to authenticated native playback when peak validation fails', () => {
  const markup = renderToStaticMarkup(
    React.createElement(Waveform, {
      waveform: { ...VALID_WAVEFORM, sample_rate_hz: 0 },
      audioUrl: '/api/v2/productions/test/media/original',
      sourceLabel: 'Original',
    }),
  );

  assert.match(markup, /Waveform sample rate must be a positive integer/);
  assert.match(markup, /Native audio playback remains available/);
  assert.match(markup, /src="\/api\/v2\/productions\/test\/media\/original"/);
  assert.match(markup, /aria-label="Original audio"/);
});
