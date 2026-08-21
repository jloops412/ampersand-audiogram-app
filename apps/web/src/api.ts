import type { Capabilities, Production, ProductionSettings, ProductionIntent, WaveformPeaks } from './types';

const TOKEN_KEY = 'ampersand-beta-token';

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export function savedToken(): string {
  return sessionStorage.getItem(TOKEN_KEY) || '';
}

export function rememberToken(token: string): void {
  if (token) sessionStorage.setItem(TOKEN_KEY, token);
  else sessionStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, options: RequestInit = {}, token = savedToken()): Promise<T> {
  const headers = new Headers(options.headers);
  if (token) headers.set('Authorization', `Bearer ${token}`);
  const response = await fetch(path, { ...options, headers, credentials: 'same-origin' });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new ApiError(payload?.error?.message || `Request failed (${response.status}).`, response.status);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export async function openSession(token: string): Promise<void> {
  await request<{ status: string }>('/api/v2/session', { method: 'POST' }, token);
  rememberToken(token);
}

export async function listProductions(): Promise<Production[]> {
  const payload = await request<{ productions: Production[] }>('/api/v2/productions');
  return payload.productions;
}

export async function getCapabilities(): Promise<Capabilities> {
  return await request<Capabilities>('/api/v2/capabilities');
}

export async function getProduction(id: string): Promise<Production> {
  const payload = await request<{ production: Production }>(`/api/v2/productions/${id}`);
  return payload.production;
}

export async function createProduction(input: {
  source: File;
  artwork?: File | null;
  title: string;
  intent: ProductionIntent;
  templateVersionId: string | null;
  settings: ProductionSettings;
  capabilities: Capabilities;
  onProgress?: (progress: number, phase: string) => void;
}): Promise<Production> {
  if (input.capabilities.directUpload.enabled) {
    const sourceUploadId = await uploadAsset(
      input.source,
      'source',
      input.capabilities.directUpload.chunkBytes,
      (progress) => input.onProgress?.(progress * 0.85, 'Uploading audio'),
    );
    const artworkUploadId = input.artwork
      ? await uploadAsset(
          input.artwork,
          'artwork',
          input.capabilities.directUpload.chunkBytes,
          (progress) => input.onProgress?.(85 + progress * 0.15, 'Uploading artwork'),
        )
      : null;
    input.onProgress?.(100, 'Queueing production');
    const payload = await request<{ production: Production }>('/api/v2/productions/from-upload', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sourceUploadId,
        artworkUploadId,
        requestId: `request:browser:${crypto.randomUUID()}`,
        title: input.title,
        intent: input.intent,
        templateVersionId: input.templateVersionId,
        settings: input.settings,
      }),
    });
    return payload.production;
  }
  if (input.source.size > input.capabilities.maxUploadBytes) {
    throw new ApiError('This revision needs direct Cloud Storage uploads enabled for a file this large.', 413);
  }
  if (input.artwork) {
    throw new ApiError('Artwork uploads require direct Cloud Storage uploads on this revision.', 503);
  }
  const form = new FormData();
  form.set('source', input.source);
  form.set('requestId', `request:browser:${crypto.randomUUID()}`);
  form.set('title', input.title);
  form.set('intent', input.intent);
  if (input.templateVersionId) form.set('templateVersionId', input.templateVersionId);
  form.set('settings', JSON.stringify(input.settings));
  input.onProgress?.(10, 'Uploading audio');
  const payload = await request<{ production: Production }>('/api/v2/productions', {
    method: 'POST',
    body: form,
  });
  input.onProgress?.(100, 'Queued');
  return payload.production;
}

async function uploadAsset(
  file: File,
  kind: 'source' | 'artwork',
  chunkBytes: number,
  onProgress: (progress: number) => void,
): Promise<string> {
  const session = await request<{
    upload: { id: string; uploadUrl: string; chunkBytes: number };
  }>('/api/v2/uploads', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      kind,
      filename: file.name,
      sizeBytes: file.size,
      mimeType: file.type || 'application/octet-stream',
    }),
  });
  const uploadUrl = session.upload.uploadUrl;
  const size = Math.max(256 * 1024, chunkBytes || session.upload.chunkBytes || 8 * 1024 * 1024);
  let offset = 0;
  while (offset < file.size) {
    const endExclusive = Math.min(file.size, offset + size);
    const response = await putChunkWithRetry(uploadUrl, file, offset, endExclusive);
    if (response.status === 200 || response.status === 201) {
      offset = file.size;
    } else if (response.status === 308) {
      const persisted = persistedOffset(response.headers.get('Range'));
      offset = persisted === null ? endExclusive : persisted;
    } else {
      throw new ApiError(`Cloud Storage rejected the upload (${response.status}).`, response.status);
    }
    onProgress(Math.min(100, (offset / file.size) * 100));
  }
  return session.upload.id;
}

async function putChunkWithRetry(
  uploadUrl: string,
  file: File,
  start: number,
  endExclusive: number,
): Promise<Response> {
  let lastError: unknown = null;
  for (let attempt = 0; attempt < 4; attempt += 1) {
    try {
      const response = await fetch(uploadUrl, {
        method: 'PUT',
        headers: {
          'Content-Type': file.type || 'application/octet-stream',
          'Content-Range': `bytes ${start}-${endExclusive - 1}/${file.size}`,
        },
        body: file.slice(start, endExclusive),
      });
      if (response.status < 500) return response;
      lastError = new Error(`Cloud Storage temporarily returned ${response.status}.`);
    } catch (error) {
      lastError = error;
    }
    await new Promise((resolve) => window.setTimeout(resolve, 300 * 2 ** attempt));
  }
  throw new ApiError(lastError instanceof Error ? lastError.message : 'The upload was interrupted.', 503);
}

function persistedOffset(range: string | null): number | null {
  const match = /^bytes=0-(\d+)$/.exec(range || '');
  return match ? Number(match[1]) + 1 : null;
}

export async function deleteProduction(id: string): Promise<void> {
  await request<void>(`/api/v2/productions/${id}`, { method: 'DELETE' });
}

export async function retryProduction(id: string): Promise<Production> {
  const payload = await request<{ production: Production }>(`/api/v2/productions/${id}/retry`, {
    method: 'POST',
  });
  return payload.production;
}

export async function getWaveform(url: string): Promise<WaveformPeaks> {
  return await request<WaveformPeaks>(url);
}
