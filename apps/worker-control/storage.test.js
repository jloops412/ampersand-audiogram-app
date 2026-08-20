import assert from 'node:assert/strict';
import test from 'node:test';

import {
  normalizeTitle,
  publicJob,
  safeDownloadFilename,
  safeErrorMessage,
  safeMediaExtension,
  tokenMatches,
  validClientRequestId,
  withinRoot,
} from './storage.js';

test('normalizes user-controlled names without making paths from them', () => {
  assert.equal(safeMediaExtension('../../private/VOICE.M4A'), '.m4a');
  assert.equal(safeMediaExtension('recording.reallylongextension'), '.media');
  assert.equal(normalizeTitle('\u0000  My   Episode  '), 'My Episode');
  assert.equal(safeDownloadFilename('My "Episode"/Final.wav'), 'My -Episode--Final.wav');
});

test('bounds identifiers, tokens, and resolved paths', () => {
  assert.equal(validClientRequestId('request:browser:1234'), true);
  assert.equal(validClientRequestId('../escape'), false);
  assert.equal(tokenMatches('secret', 'secret'), true);
  assert.equal(tokenMatches('secret', 'wrong'), false);
  assert.equal(tokenMatches('', ''), false);
  assert.equal(tokenMatches('', 'anything'), false);
  assert.throws(() => withinRoot('/tmp/ampersand-test', '..', 'escape'), /escapes/);
});

test('public job projection excludes internal paths and source hashes', () => {
  const projected = publicJob({
    id: 'beta-123',
    requestId: 'request:browser:1234',
    title: 'Test',
    status: 'queued',
    intent: 'podcast',
    settings: {},
    source: {
      filename: 'test.wav',
      sizeBytes: 42,
      sha256: 'a'.repeat(64),
      path: '/private/source.wav',
    },
    createdAt: '2026-08-20T00:00:00.000Z',
    updatedAt: '2026-08-20T00:00:00.000Z',
    currentStep: 'queued',
    completedSteps: [],
    progressPercent: 0,
    attempt: 0,
    outputDirectory: '/private/output',
  });
  const serialized = JSON.stringify(projected);
  assert.equal(serialized.includes('/private'), false);
  assert.equal(serialized.includes('aaaaaaaa'), false);
});

test('error messages redact private roots and collapse newlines', () => {
  assert.equal(
    safeErrorMessage('failed at /data/private/source.wav\nnext', ['/data/private']),
    'failed at [private-media]/source.wav next',
  );
});
