import type { Production, ProductionSettings, ProductionIntent, WaveformPeaks } from './types';

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

export async function getProduction(id: string): Promise<Production> {
  const payload = await request<{ production: Production }>(`/api/v2/productions/${id}`);
  return payload.production;
}

export async function createProduction(input: {
  source: File;
  title: string;
  intent: ProductionIntent;
  templateVersionId: string | null;
  settings: ProductionSettings;
}): Promise<Production> {
  const form = new FormData();
  form.set('source', input.source);
  form.set('requestId', `request:browser:${crypto.randomUUID()}`);
  form.set('title', input.title);
  form.set('intent', input.intent);
  if (input.templateVersionId) form.set('templateVersionId', input.templateVersionId);
  form.set('settings', JSON.stringify(input.settings));
  const payload = await request<{ production: Production }>('/api/v2/productions', {
    method: 'POST',
    body: form,
  });
  return payload.production;
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
