import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';

test('exposes the Cloud Run-safe health endpoint', async (context) => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'ampersand-control-health-'));
  context.after(async () => fs.rm(root, { recursive: true, force: true }));
  process.env.AMPERSAND_DATA_DIR = path.join(root, 'data');
  process.env.AMPERSAND_WORK_DIR = path.join(root, 'work');
  process.env.AMPERSAND_STATIC_DIR = path.join(root, 'static');
  await fs.mkdir(process.env.AMPERSAND_STATIC_DIR, { recursive: true });

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
});
