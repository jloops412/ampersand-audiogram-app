import assert from 'node:assert/strict';
import test from 'node:test';

import { cloudRunAccessToken, initiateResumableUpload, readObjectMetadata } from './gcs.js';

test('obtains a bounded Cloud Run metadata token', async () => {
  const calls = [];
  const token = await cloudRunAccessToken(async (url, options) => {
    calls.push({ url, options });
    return new Response(JSON.stringify({ access_token: 'a'.repeat(32) }), { status: 200 });
  });
  assert.equal(token, 'a'.repeat(32));
  assert.equal(calls[0].options.headers['Metadata-Flavor'], 'Google');
});

test('initiates a scoped resumable upload without exposing the access token', async () => {
  const calls = [];
  const location =
    'https://storage.googleapis.com/upload/storage/v1/b/test-bucket/o?uploadType=resumable&upload_id=session-1';
  const result = await initiateResumableUpload({
    bucket: 'test-bucket',
    objectName: 'incoming/11111111-1111-4111-8111-111111111111/source.wav',
    contentType: 'audio/wav',
    sizeBytes: 90000000,
    origin: 'https://ampersand.example',
    metadata: { 'ampersand-upload-id': '11111111-1111-4111-8111-111111111111' },
    tokenProvider: async () => 'token-value-that-is-long-enough',
    fetchImpl: async (url, options) => {
      calls.push({ url, options });
      return new Response(null, { status: 200, headers: { Location: location } });
    },
  });
  assert.equal(result, location);
  assert.match(calls[0].url, /uploadType=resumable/);
  assert.match(calls[0].url, /ifGenerationMatch=0/);
  assert.equal(calls[0].options.headers['X-Upload-Content-Length'], '90000000');
  assert.equal(calls[0].options.headers.Origin, 'https://ampersand.example');
  assert.equal(JSON.stringify(calls).includes(location), false);
});

test('rejects unscoped object names and non-web origins', async () => {
  const common = {
    bucket: 'test-bucket',
    contentType: 'audio/wav',
    sizeBytes: 1,
    tokenProvider: async () => 'token-value-that-is-long-enough',
    fetchImpl: async () => new Response(),
  };
  await assert.rejects(
    initiateResumableUpload({ ...common, objectName: '../private.wav', origin: 'https://ampersand.example' }),
    /object name/,
  );
  await assert.rejects(
    initiateResumableUpload({
      ...common,
      objectName: 'incoming/11111111-1111-4111-8111-111111111111/source.wav',
      origin: 'file:///private',
    }),
    /origin/,
  );
});

test('verifies completed object metadata without reading media bytes', async () => {
  const objectName = 'incoming/11111111-1111-4111-8111-111111111111/source.wav';
  const result = await readObjectMetadata({
    bucket: 'test-bucket',
    objectName,
    tokenProvider: async () => 'token-value-that-is-long-enough',
    fetchImpl: async (url, options) => {
      assert.match(url, /fields=name%2Csize%2CcontentType%2Cgeneration|fields=name,size,contentType,generation/);
      assert.match(options.headers.Authorization, /^Bearer /);
      return new Response(JSON.stringify({ name: objectName, size: '90000000', contentType: 'audio/wav' }), {
        status: 200,
      });
    },
  });
  assert.deepEqual(result, { sizeBytes: 90000000, contentType: 'audio/wav' });
});
