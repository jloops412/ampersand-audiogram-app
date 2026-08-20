import { createHash, randomUUID, timingSafeEqual } from 'node:crypto';
import { createReadStream } from 'node:fs';
import fs from 'node:fs/promises';
import path from 'node:path';

const SAFE_EXTENSION = /^\.[a-z0-9]{1,8}$/;

export function safeMediaExtension(filename) {
  const extension = path.extname(String(filename || '')).toLowerCase();
  return SAFE_EXTENSION.test(extension) ? extension : '.media';
}

export function normalizeTitle(value, fallback = 'Untitled production') {
  const compact = String(value || '')
    .replace(/[\u0000-\u001f\u007f]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
  return (compact || fallback).slice(0, 160);
}

export function safeDownloadFilename(value, fallback = 'ampersand-audio') {
  return normalizeTitle(value, fallback)
    .replace(/["\\/<>:|?*]/g, '-')
    .replace(/\.+$/g, '')
    .trim()
    .slice(0, 180) || fallback;
}

export function validOpaqueId(value) {
  return typeof value === 'string' && /^[a-z0-9][a-z0-9._:-]{1,127}$/.test(value);
}

export function validClientRequestId(value) {
  return typeof value === 'string' && /^[a-zA-Z0-9._:-]{8,128}$/.test(value);
}

export function tokenMatches(expected, received) {
  if (!expected || !received) return false;
  const expectedBytes = Buffer.from(expected);
  const receivedBytes = Buffer.from(received);
  return expectedBytes.length === receivedBytes.length && timingSafeEqual(expectedBytes, receivedBytes);
}

export async function sha256File(filename) {
  const digest = createHash('sha256');
  await new Promise((resolve, reject) => {
    const stream = createReadStream(filename);
    stream.on('data', (chunk) => digest.update(chunk));
    stream.on('error', reject);
    stream.on('end', resolve);
  });
  return digest.digest('hex');
}

export async function writeJsonAtomic(filename, value) {
  await fs.mkdir(path.dirname(filename), { recursive: true });
  const temporary = `${filename}.tmp-${process.pid}-${randomUUID()}`;
  await fs.writeFile(temporary, `${JSON.stringify(value, null, 2)}\n`, { encoding: 'utf8', mode: 0o600 });
  await fs.rename(temporary, filename);
}

export async function readJson(filename) {
  return JSON.parse(await fs.readFile(filename, 'utf8'));
}

export function withinRoot(root, ...parts) {
  const resolvedRoot = path.resolve(root);
  const candidate = path.resolve(resolvedRoot, ...parts);
  if (candidate !== resolvedRoot && !candidate.startsWith(`${resolvedRoot}${path.sep}`)) {
    throw new Error('Resolved path escapes the configured data directory.');
  }
  return candidate;
}

export function publicJob(job) {
  const outputs = job.status === 'succeeded'
    ? {
        original: `/api/v2/productions/${job.id}/media/original`,
        wav: job.result?.wavSha256 ? `/api/v2/productions/${job.id}/media/wav` : null,
        mp3: job.result?.mp3Sha256 ? `/api/v2/productions/${job.id}/media/mp3` : null,
        report: `/api/v2/productions/${job.id}/report`,
        waveform: `/api/v2/productions/${job.id}/waveform`,
      }
    : null;
  return {
    id: job.id,
    requestId: job.requestId,
    title: job.title,
    status: job.status,
    intent: job.intent,
    templateVersionId: job.templateVersionId || null,
    settings: job.settings,
    source: {
      filename: job.source.filename,
      sizeBytes: job.source.sizeBytes,
    },
    createdAt: job.createdAt,
    updatedAt: job.updatedAt,
    startedAt: job.startedAt || null,
    completedAt: job.completedAt || null,
    currentStep: job.currentStep,
    completedSteps: job.completedSteps,
    progressPercent: job.progressPercent,
    attempt: job.attempt,
    error: job.error || null,
    summary: job.summary || null,
    outputs,
  };
}

export function safeErrorMessage(value, privateRoots = []) {
  let message = String(value || 'Processing failed.');
  for (const root of privateRoots.filter(Boolean)) {
    message = message.split(String(root)).join('[private-media]');
  }
  message = message.replace(/[\r\n]+/g, ' ').replace(/\s+/g, ' ').trim();
  return message.slice(0, 500) || 'Processing failed.';
}
