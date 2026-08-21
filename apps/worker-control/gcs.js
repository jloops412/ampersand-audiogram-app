const METADATA_TOKEN_URL =
  'http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token';

function assertBucketName(bucket) {
  if (!/^[a-z0-9][a-z0-9._-]{1,220}[a-z0-9]$/.test(bucket)) {
    throw new Error('AMPERSAND_GCS_BUCKET is missing or invalid.');
  }
}

function assertOrigin(origin) {
  const parsed = new URL(origin);
  if (!['https:', 'http:'].includes(parsed.protocol) || parsed.username || parsed.password) {
    throw new Error('The upload origin is invalid.');
  }
  return parsed.origin;
}

export async function cloudRunAccessToken(fetchImpl = fetch) {
  const response = await fetchImpl(METADATA_TOKEN_URL, {
    headers: { 'Metadata-Flavor': 'Google' },
    signal: AbortSignal.timeout(5_000),
  });
  if (!response.ok) throw new Error('Cloud Run could not obtain a storage access token.');
  const payload = await response.json();
  if (typeof payload?.access_token !== 'string' || payload.access_token.length < 20) {
    throw new Error('Cloud Run returned an invalid storage access token.');
  }
  return payload.access_token;
}

export async function initiateResumableUpload({
  bucket,
  objectName,
  contentType,
  sizeBytes,
  origin,
  metadata = {},
  fetchImpl = fetch,
  tokenProvider = cloudRunAccessToken,
}) {
  assertBucketName(bucket);
  if (!/^incoming\/[a-f0-9-]{36}\/[a-z]+\.[a-z0-9]{1,8}$/.test(objectName)) {
    throw new Error('The storage object name is invalid.');
  }
  if (!Number.isSafeInteger(sizeBytes) || sizeBytes <= 0) throw new Error('The upload size is invalid.');
  const allowedOrigin = assertOrigin(origin);
  const accessToken = await tokenProvider(fetchImpl);
  const body = JSON.stringify({
    contentType: contentType || 'application/octet-stream',
    metadata,
  });
  const endpoint =
    `https://storage.googleapis.com/upload/storage/v1/b/${encodeURIComponent(bucket)}/o` +
    `?uploadType=resumable&name=${encodeURIComponent(objectName)}&ifGenerationMatch=0`;
  const response = await fetchImpl(endpoint, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${accessToken}`,
      'Content-Type': 'application/json; charset=utf-8',
      'Content-Length': String(Buffer.byteLength(body)),
      'X-Upload-Content-Type': contentType || 'application/octet-stream',
      'X-Upload-Content-Length': String(sizeBytes),
      Origin: allowedOrigin,
    },
    body,
    signal: AbortSignal.timeout(10_000),
  });
  const location = response.headers.get('location');
  if (!response.ok || !location) throw new Error('Cloud Storage could not start the resumable upload.');
  const session = new URL(location);
  if (session.protocol !== 'https:' || session.hostname !== 'storage.googleapis.com' || !session.searchParams.has('upload_id')) {
    throw new Error('Cloud Storage returned an invalid resumable session.');
  }
  return location;
}

export async function readObjectMetadata({
  bucket,
  objectName,
  fetchImpl = fetch,
  tokenProvider = cloudRunAccessToken,
}) {
  assertBucketName(bucket);
  if (!/^incoming\/[a-f0-9-]{36}\/[a-z]+\.[a-z0-9]{1,8}$/.test(objectName)) {
    throw new Error('The storage object name is invalid.');
  }
  const accessToken = await tokenProvider(fetchImpl);
  const endpoint =
    `https://storage.googleapis.com/storage/v1/b/${encodeURIComponent(bucket)}/o/` +
    `${encodeURIComponent(objectName)}?fields=name,size,contentType,generation`;
  const response = await fetchImpl(endpoint, {
    headers: { Authorization: `Bearer ${accessToken}` },
    signal: AbortSignal.timeout(10_000),
  });
  if (!response.ok) {
    const error = new Error(
      response.status === 404
        ? 'The resumable upload has not completed yet.'
        : 'Cloud Storage could not verify the completed upload.',
    );
    error.statusCode = response.status === 404 ? 409 : 502;
    throw error;
  }
  const payload = await response.json();
  const sizeBytes = Number(payload?.size);
  if (payload?.name !== objectName || !Number.isSafeInteger(sizeBytes) || sizeBytes <= 0) {
    throw new Error('Cloud Storage returned invalid upload metadata.');
  }
  return { sizeBytes, contentType: String(payload.contentType || 'application/octet-stream') };
}
