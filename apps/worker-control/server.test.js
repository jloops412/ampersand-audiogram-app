import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';

test('exposes health, capabilities, and authenticated private artifacts', async (context) => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'ampersand-control-health-'));
  context.after(async () => fs.rm(root, { recursive: true, force: true }));
  process.env.AMPERSAND_DATA_DIR = path.join(root, 'data');
  process.env.AMPERSAND_WORK_DIR = path.join(root, 'work');
  process.env.AMPERSAND_STATIC_DIR = path.join(root, 'static');
  process.env.AMPERSAND_BETA_TOKEN = 'test-beta-token-with-24-characters';
  await fs.mkdir(process.env.AMPERSAND_STATIC_DIR, { recursive: true });
  const productionId = '00000000-0000-4000-8000-000000000043';
  const productionDirectory = path.join(process.env.AMPERSAND_DATA_DIR, 'productions', productionId);
  const outputDirectory = path.join(productionDirectory, 'output');
  const sourceDirectory = path.join(productionDirectory, 'source');
  const sourcePath = path.join(sourceDirectory, 'fixture.wav');
  const masterPath = path.join(outputDirectory, 'artifacts', 'master.wav');
  await fs.mkdir(path.dirname(masterPath), { recursive: true });
  await fs.mkdir(sourceDirectory, { recursive: true });
  await fs.writeFile(sourcePath, Buffer.from('original-audio-bytes'));
  await fs.writeFile(masterPath, Buffer.from('master-audio-bytes'));
  await fs.writeFile(
    path.join(outputDirectory, 'cleanup-plan.json'),
    `${JSON.stringify({ cleanup_plan_id: 'cleanup-plan:test', mode: 'smart', decision: 'protect' })}\n`,
  );
  const waveformFixture = {
    schema_version: '1.0.0',
    waveform_id: 'waveform:test',
    source_asset_id: 'asset:test',
    sample_rate_hz: 48_000,
    channels: 1,
    duration_us: 1_000_000,
    levels: [
      { samples_per_window: 960, windows: [[[-0.25, 0.5]], [[-0.5, 0.75]]] },
      { samples_per_window: 1_920, windows: [[[-0.5, 0.75]]] },
    ],
  };
  const studioWaveformFixture = { ...waveformFixture, levels: [waveformFixture.levels[1]] };
  await fs.writeFile(
    path.join(outputDirectory, 'waveform-peaks.json'),
    `${JSON.stringify(waveformFixture)}\n`,
  );
  await fs.writeFile(
    path.join(outputDirectory, 'waveform-studio.json'),
    `${JSON.stringify(studioWaveformFixture)}\n`,
  );
  await fs.writeFile(
    path.join(productionDirectory, 'job.json'),
    `${JSON.stringify({
      id: productionId,
      requestId: 'request:browser:test-cleanup-plan',
      title: 'Cleanup plan fixture',
      status: 'succeeded',
      intent: 'podcast',
      templateVersionId: null,
      settings: {},
      source: { filename: 'fixture.wav', sizeBytes: 20, path: sourcePath, mimeType: 'audio/wav' },
      createdAt: '2026-08-24T00:00:00.000Z',
      updatedAt: '2026-08-24T00:00:00.000Z',
      startedAt: '2026-08-24T00:00:01.000Z',
      completedAt: '2026-08-24T00:00:02.000Z',
      currentStep: 'complete',
      completedSteps: [],
      progressPercent: 100,
      attempt: 1,
      error: null,
      result: { wavSha256: '0'.repeat(64) },
      summary: null,
      outputDirectory,
    })}\n`,
  );

  const { createApp } = await import('./server.js');
  const app = await createApp();
  const server = await new Promise((resolve) => {
    const listening = app.listen(0, '127.0.0.1', () => resolve(listening));
  });
  context.after(
    () => new Promise((resolve, reject) => server.close((error) => (error ? reject(error) : resolve()))),
  );

  const address = server.address();
  assert.notEqual(address, null);
  const response = await fetch(`http://127.0.0.1:${address.port}/health`);
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), { status: 'ok' });

  const capabilitiesResponse = await fetch(`http://127.0.0.1:${address.port}/api/v2/capabilities`, {
    headers: { authorization: `Bearer ${process.env.AMPERSAND_BETA_TOKEN}` },
  });
  assert.equal(capabilitiesResponse.status, 200);
  const capabilities = await capabilitiesResponse.json();
  assert.equal(capabilities.apiVersion, 'v2-beta-3');
  assert.ok(capabilities.executableSettings.includes('cleanup.mode'));
  assert.ok(capabilities.executableSettings.includes('cleanup.declip'));
  assert.match(capabilities.betaLimitations.join(' '), /Smart Cleanup protects/);

  const unauthenticatedPlan = await fetch(
    `http://127.0.0.1:${address.port}/api/v2/productions/${productionId}/cleanup-plan`,
  );
  assert.equal(unauthenticatedPlan.status, 401);
  const cleanupPlanResponse = await fetch(
    `http://127.0.0.1:${address.port}/api/v2/productions/${productionId}/cleanup-plan`,
    { headers: { authorization: `Bearer ${process.env.AMPERSAND_BETA_TOKEN}` } },
  );
  assert.equal(cleanupPlanResponse.status, 200);
  assert.match(cleanupPlanResponse.headers.get('content-disposition'), /cleanup-plan\.json/);
  assert.equal((await cleanupPlanResponse.json()).cleanup_plan_id, 'cleanup-plan:test');

  const unauthenticatedWaveform = await fetch(
    `http://127.0.0.1:${address.port}/api/v2/productions/${productionId}/waveform`,
  );
  assert.equal(unauthenticatedWaveform.status, 401);

  const sessionResponse = await fetch(`http://127.0.0.1:${address.port}/api/v2/session`, {
    method: 'POST',
    headers: { authorization: `Bearer ${process.env.AMPERSAND_BETA_TOKEN}` },
  });
  assert.equal(sessionResponse.status, 200);
  const sessionCookie = sessionResponse.headers.get('set-cookie')?.split(';')[0];
  assert.match(sessionCookie || '', /^ampersand_beta_session=/);

  const waveformResponse = await fetch(
    `http://127.0.0.1:${address.port}/api/v2/productions/${productionId}/waveform`,
    { headers: { cookie: sessionCookie } },
  );
  assert.equal(waveformResponse.status, 200);
  assert.match(waveformResponse.headers.get('content-type') || '', /^application\/json/);
  assert.deepEqual(await waveformResponse.json(), studioWaveformFixture);

  await fs.rm(path.join(outputDirectory, 'waveform-studio.json'));
  const legacyWaveformResponse = await fetch(
    `http://127.0.0.1:${address.port}/api/v2/productions/${productionId}/waveform`,
    { headers: { cookie: sessionCookie } },
  );
  assert.equal(legacyWaveformResponse.status, 200);
  assert.deepEqual(await legacyWaveformResponse.json(), waveformFixture);

  const rangeResponse = await fetch(
    `http://127.0.0.1:${address.port}/api/v2/productions/${productionId}/media/wav`,
    { headers: { cookie: sessionCookie, range: 'bytes=0-5' } },
  );
  assert.equal(rangeResponse.status, 206);
  assert.equal(rangeResponse.headers.get('content-range'), 'bytes 0-5/18');
  assert.equal(Buffer.from(await rangeResponse.arrayBuffer()).toString(), 'master');

  await fs.rm(path.join(outputDirectory, 'waveform-peaks.json'));
  const missingWaveformResponse = await fetch(
    `http://127.0.0.1:${address.port}/api/v2/productions/${productionId}/waveform`,
    { headers: { cookie: sessionCookie } },
  );
  assert.equal(missingWaveformResponse.status, 404);
});
