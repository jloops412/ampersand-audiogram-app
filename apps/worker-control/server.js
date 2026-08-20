import { execFile, spawn } from 'node:child_process';
import { createHmac, randomUUID } from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { promisify } from 'node:util';

import express from 'express';
import { formidable } from 'formidable';

import {
  normalizeTitle,
  publicJob,
  readJson,
  safeDownloadFilename,
  safeErrorMessage,
  safeMediaExtension,
  sha256File,
  tokenMatches,
  validClientRequestId,
  validOpaqueId,
  withinRoot,
  writeJsonAtomic,
} from './storage.js';

const execFileAsync = promisify(execFile);
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DATA_DIR = path.resolve(process.env.AMPERSAND_DATA_DIR || '/data/ampersand');
const WORK_DIR = path.resolve(process.env.AMPERSAND_WORK_DIR || '/tmp/ampersand-work');
const STATIC_DIR = path.resolve(process.env.AMPERSAND_STATIC_DIR || path.join(__dirname, '..', '..', '..', 'dist'));
const PRODUCTIONS_DIR = withinRoot(DATA_DIR, 'productions');
const SOURCES_DIR = withinRoot(DATA_DIR, 'sources');
const UPLOADS_DIR = withinRoot(WORK_DIR, 'uploads');
const ENGINE_BIN = process.env.AMPERSAND_ENGINE_BIN || 'ampersand-engine';
const PORT = Number(process.env.PORT || 8080);
const MAX_UPLOAD_BYTES = Number(process.env.AMPERSAND_MAX_UPLOAD_BYTES || 30 * 1024 * 1024);
const BETA_TOKEN = process.env.AMPERSAND_BETA_TOKEN || '';
const BETA_SESSION = BETA_TOKEN
  ? createHmac('sha256', BETA_TOKEN).update('ampersand-private-beta-session-v1').digest('hex')
  : '';

const STEP_ORDER = [
  'validate/probe',
  'canonicalize if needed',
  'measure, build waveform, and analyze semantics',
  'build Processing Router V0 shadow plan',
  'plan Adaptive Leveler shadow candidate',
  'render deterministic WAV and MP3',
  'validate outputs and report',
  'complete',
];

const jobs = new Map();
const pendingQueue = [];
const persistenceChains = new Map();
const pendingDeletion = new Set();
let active = null;
let draining = false;

function jobDirectory(jobId) {
  if (!/^[a-f0-9-]{36}$/.test(jobId)) throw new Error('Invalid production identifier.');
  return withinRoot(PRODUCTIONS_DIR, jobId);
}

function jobFilename(jobId) {
  return withinRoot(jobDirectory(jobId), 'job.json');
}

function jobWorkDirectory(jobId, attempt = null) {
  if (!/^[a-f0-9-]{36}$/.test(jobId)) throw new Error('Invalid production identifier.');
  const base = withinRoot(WORK_DIR, jobId);
  return attempt === null ? base : withinRoot(base, `attempt-${attempt}`);
}

async function persistJob(job) {
  job.updatedAt = new Date().toISOString();
  const snapshot = JSON.parse(JSON.stringify(job));
  const previous = persistenceChains.get(job.id) || Promise.resolve();
  const current = previous.then(() => writeJsonAtomic(jobFilename(job.id), snapshot));
  persistenceChains.set(job.id, current.catch(() => {}));
  await current;
}

function fieldValue(fields, name) {
  const value = fields[name];
  return Array.isArray(value) ? value[0] : value;
}

function fileValue(files, name) {
  const value = files[name];
  return Array.isArray(value) ? value[0] : value;
}

async function parseUpload(request) {
  const form = formidable({
    uploadDir: UPLOADS_DIR,
    keepExtensions: false,
    maxFileSize: MAX_UPLOAD_BYTES,
    maxFiles: 1,
    multiples: false,
    allowEmptyFiles: false,
  });
  return await new Promise((resolve, reject) => {
    form.parse(request, (error, fields, files) => {
      if (error) reject(error);
      else resolve({ fields, files });
    });
  });
}

async function validateSettings(settingsFilename) {
  try {
    await execFileAsync(ENGINE_BIN, ['validate-manifest', 'ProductionSettings', settingsFilename], {
      timeout: 15_000,
      maxBuffer: 256 * 1024,
      env: { ...process.env, LC_ALL: 'C', LANG: 'C', TZ: 'UTC' },
    });
  } catch (error) {
    const detail = safeErrorMessage(error?.stderr || error?.message, [DATA_DIR, settingsFilename]);
    const validationError = new Error(detail.replace(/^ampersand:\s*error:\s*/i, ''));
    validationError.statusCode = 400;
    throw validationError;
  }
}

function betaTokenFrom(request) {
  const authorization = request.get('authorization') || '';
  if (authorization.startsWith('Bearer ')) return authorization.slice('Bearer '.length);
  return request.get('x-ampersand-beta-token') || '';
}

function betaSessionFrom(request) {
  const cookie = request.get('cookie') || '';
  for (const part of cookie.split(';')) {
    const [name, ...value] = part.trim().split('=');
    if (name === 'ampersand_beta_session') return value.join('=');
  }
  return '';
}

function requireBetaAccess(request, response, next) {
  const headerAuthorized = tokenMatches(BETA_TOKEN, betaTokenFrom(request));
  const sessionAuthorized = Boolean(BETA_SESSION) && tokenMatches(BETA_SESSION, betaSessionFrom(request));
  if (headerAuthorized || sessionAuthorized) return next();
  response.status(401).json({
    error: { code: 'beta_access_required', message: 'Enter the private beta access key.' },
  });
}

function enqueue(jobId) {
  if (!pendingQueue.includes(jobId)) pendingQueue.push(jobId);
  void drainQueue();
}

async function drainQueue() {
  if (draining || active) return;
  draining = true;
  try {
    const jobId = pendingQueue.shift();
    if (!jobId) return;
    const job = jobs.get(jobId);
    if (!job || job.status !== 'queued') return;
    active = { jobId: job.id, child: null };
    try {
      await runJob(job);
    } catch (error) {
      job.status = 'failed';
      job.currentStep = 'failed';
      job.completedAt = new Date().toISOString();
      job.error = {
        code: 'runner_failure',
        message: safeErrorMessage(error?.message, [DATA_DIR, job.source.path]),
      };
      await persistJob(job).catch(() => {});
    }
  } finally {
    active = null;
    draining = false;
    if (pendingQueue.length) void drainQueue();
  }
}

function updateProgress(job, message) {
  const index = STEP_ORDER.indexOf(message);
  if (index < 0) return;
  job.currentStep = message;
  job.completedSteps = STEP_ORDER.slice(0, index);
  job.progressPercent = Math.round((index / (STEP_ORDER.length - 1)) * 100);
  void persistJob(job);
}

async function buildSummary(outputDirectory) {
  const [probe, before, after, report, resolved, output] = await Promise.all([
    readJson(path.join(outputDirectory, 'probe.json')),
    readJson(path.join(outputDirectory, 'loudness-before.json')),
    readJson(path.join(outputDirectory, 'loudness-after.json')),
    readJson(path.join(outputDirectory, 'processing-report.json')),
    readJson(path.join(outputDirectory, 'resolved-settings.json')),
    readJson(path.join(outputDirectory, 'output-manifest.json')),
  ]);
  return {
    durationUs: probe.duration_us,
    channels: probe.channels,
    sampleRateHz: probe.sample_rate_hz,
    formatName: probe.format_name,
    loudnessBefore: before,
    loudnessAfter: after,
    resolvedSettingsId: resolved.resolved_settings_id,
    resolvedSettingsSha256: resolved.settings_sha256,
    decisions: report.decisions,
    warnings: report.warnings,
    artifacts: output.artifacts.map((artifact) => ({
      kind: artifact.kind,
      sizeBytes: artifact.size_bytes,
      mimeType: artifact.mime_type,
    })),
    externalApiCostUsd: report.external_api_cost_usd,
  };
}

async function runJob(job) {
  job.status = 'running';
  job.startedAt = new Date().toISOString();
  job.completedAt = null;
  job.attempt += 1;
  job.error = null;
  job.currentStep = 'starting engine';
  job.progressPercent = 1;
  await persistJob(job);

  const workDirectory = jobWorkDirectory(job.id, job.attempt);
  try {
    await runJobAttempt(job, workDirectory);
  } finally {
    await fs.rm(workDirectory, { recursive: true, force: true }).catch(() => {});
  }
}

async function runJobAttempt(job, workDirectory) {
  await fs.mkdir(workDirectory, { recursive: true });
  const processingSource = withinRoot(workDirectory, `source${safeMediaExtension(job.source.filename)}`);
  const processingOutput = withinRoot(workDirectory, 'output');
  await fs.copyFile(job.source.path, processingSource);
  if (pendingDeletion.has(job.id)) {
    pendingDeletion.delete(job.id);
    await deleteJobFiles(job);
    return;
  }

  const argumentsList = [
    'process',
    processingSource,
    '--output',
    processingOutput,
    '--title',
    job.title,
    '--intent',
    job.intent,
    '--settings',
    job.settingsPath,
    '--settings-source',
    job.templateVersionId ? 'template' : 'run_override',
  ];
  if (job.templateVersionId) argumentsList.push('--template-version-id', job.templateVersionId);

  const child = spawn(ENGINE_BIN, argumentsList, {
    env: { ...process.env, LC_ALL: 'C', LANG: 'C', TZ: 'UTC', PYTHONUNBUFFERED: '1' },
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  active = { jobId: job.id, child };
  let stdout = '';
  let stderr = '';
  let stderrBuffer = '';
  child.stdout.on('data', (chunk) => {
    stdout = `${stdout}${chunk}`.slice(-256 * 1024);
  });
  child.stderr.on('data', (chunk) => {
    const text = chunk.toString();
    stderr = `${stderr}${text}`.slice(-256 * 1024);
    stderrBuffer += text;
    const lines = stderrBuffer.split(/\r?\n/);
    stderrBuffer = lines.pop() || '';
    for (const line of lines) {
      const match = /^ampersand:\s+(.+)$/.exec(line.trim());
      if (match && !match[1].startsWith('error:')) updateProgress(job, match[1]);
    }
  });

  const exitCode = await new Promise((resolve) => {
    child.once('error', () => resolve(-1));
    child.once('close', (code) => resolve(code ?? -1));
  });

  if (pendingDeletion.has(job.id)) {
    pendingDeletion.delete(job.id);
    await deleteJobFiles(job);
    return;
  }

  if (exitCode === 0) {
    try {
      const resultLine = stdout.trim().split(/\r?\n/).at(-1) || '{}';
      const result = JSON.parse(resultLine);
      await fs.rm(job.outputDirectory, { recursive: true, force: true });
      await fs.cp(processingOutput, job.outputDirectory, {
        recursive: true,
        force: false,
        errorOnExist: true,
      });
      job.result = {
        productionId: result.production_id,
        runId: result.run_id,
        wavSha256: result.wav_sha256 || null,
        mp3Sha256: result.mp3_sha256 || null,
      };
      job.summary = await buildSummary(job.outputDirectory);
      job.status = 'succeeded';
      job.currentStep = 'complete';
      job.completedSteps = STEP_ORDER;
      job.progressPercent = 100;
      job.completedAt = new Date().toISOString();
      await persistJob(job);
      return;
    } catch (error) {
      stderr = `Completed engine output could not be indexed: ${error.message}`;
    }
  }

  job.status = 'failed';
  job.currentStep = 'failed';
  job.completedAt = new Date().toISOString();
  job.error = {
    code: exitCode === -1 ? 'engine_unavailable' : 'processing_failed',
    message: safeErrorMessage(stderr.trim().split(/\r?\n/).at(-1), [DATA_DIR, job.source.path]),
  };
  await persistJob(job);
}

async function deleteJobFiles(job) {
  jobs.delete(job.id);
  pendingQueue.splice(0, pendingQueue.length, ...pendingQueue.filter((id) => id !== job.id));
  await Promise.all([
    fs.rm(jobDirectory(job.id), { recursive: true, force: true }),
    fs.rm(jobWorkDirectory(job.id), { recursive: true, force: true }),
  ]);
  const sourceStillUsed = [...jobs.values()].some((candidate) => candidate.source.sha256 === job.source.sha256);
  if (!sourceStillUsed) {
    await fs.rm(path.dirname(job.source.path), { recursive: true, force: true });
  }
}

async function loadJobs() {
  await fs.mkdir(WORK_DIR, { recursive: true });
  const workEntries = await fs.readdir(WORK_DIR, { withFileTypes: true });
  await Promise.all(
    workEntries
      .filter((entry) => entry.isDirectory() && /^[a-f0-9-]{36}$/.test(entry.name))
      .map((entry) => fs.rm(jobWorkDirectory(entry.name), { recursive: true, force: true })),
  );
  await fs.rm(UPLOADS_DIR, { recursive: true, force: true });
  await Promise.all([
    fs.mkdir(PRODUCTIONS_DIR, { recursive: true }),
    fs.mkdir(SOURCES_DIR, { recursive: true }),
    fs.mkdir(UPLOADS_DIR, { recursive: true }),
  ]);
  const entries = await fs.readdir(PRODUCTIONS_DIR, { withFileTypes: true });
  for (const entry of entries) {
    if (!entry.isDirectory() || !/^[a-f0-9-]{36}$/.test(entry.name)) continue;
    try {
      const job = await readJson(jobFilename(entry.name));
      if (job.status === 'running') {
        job.status = 'interrupted';
        job.currentStep = 'interrupted';
        job.error = {
          code: 'service_restarted',
          message: 'The beta service restarted during this run. Retry without re-uploading.',
        };
        await persistJob(job);
      }
      jobs.set(job.id, job);
      if (job.status === 'queued') pendingQueue.push(job.id);
    } catch {
      // Ignore malformed state here; it remains on disk for operator inspection rather than being deleted.
    }
  }
}

export async function createApp() {
  await loadJobs();
  const app = express();
  app.disable('x-powered-by');
  app.use((request, response, next) => {
    response.setHeader('X-Content-Type-Options', 'nosniff');
    response.setHeader('Referrer-Policy', 'no-referrer');
    response.setHeader('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');
    response.setHeader(
      'Content-Security-Policy',
      "default-src 'self'; connect-src 'self'; img-src 'self' data: blob:; media-src 'self' blob:; " +
        "style-src 'self' 'unsafe-inline'; font-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
    );
    next();
  });

  app.get('/healthz', (_request, response) => response.json({ status: 'ok' }));
  app.post('/api/v2/session', requireBetaAccess, (request, response) => {
    if (BETA_SESSION) {
      const secure = request.secure || request.get('x-forwarded-proto') === 'https';
      response.cookie('ampersand_beta_session', BETA_SESSION, {
        httpOnly: true,
        sameSite: 'strict',
        secure,
        maxAge: 8 * 60 * 60 * 1000,
        path: '/',
      });
    }
    response.setHeader('Cache-Control', 'no-store, private');
    response.json({ status: 'ok' });
  });
  app.use('/api/v2', requireBetaAccess, (_request, response, next) => {
    response.setHeader('Cache-Control', 'no-store, private');
    next();
  });
  app.use(express.json({ limit: '256kb' }));

  app.get('/api/v2/capabilities', (_request, response) => {
    response.json({
      apiVersion: 'v2-beta-1',
      recipe: 'smart-spoken-word-v0',
      maxUploadBytes: MAX_UPLOAD_BYTES,
      intents: ['podcast', 'natural_voice', 'broadcast', 'social_voice'],
      executableSettings: [
        'mastering.target_integrated_lufs',
        'mastering.max_true_peak_dbtp',
        'mastering.target_loudness_range_lu',
        'export.wav',
        'export.mp3',
        'export.mp3_bitrate_kbps',
      ],
      betaLimitations: [
        'Processing Router and Adaptive Leveler are analyzed and reported but not applied.',
        'Neural denoise, transcription, and audiogram rendering are not enabled.',
        'The beta runner processes one production at a time and needs one persistent data volume.',
      ],
    });
  });

  app.get('/api/v2/productions', (_request, response) => {
    const ordered = [...jobs.values()]
      .sort((left, right) => right.createdAt.localeCompare(left.createdAt))
      .map(publicJob);
    response.json({ productions: ordered });
  });

  app.post('/api/v2/productions', async (request, response, next) => {
    let uploadedPath = null;
    let provisionalJobId = null;
    try {
      const { fields, files } = await parseUpload(request);
      const uploaded = fileValue(files, 'source');
      if (!uploaded) {
        const error = new Error('Choose one audio file to process.');
        error.statusCode = 400;
        throw error;
      }
      uploadedPath = uploaded.filepath;
      const requestId = fieldValue(fields, 'requestId');
      if (!validClientRequestId(requestId)) {
        const error = new Error('The request identifier is missing or invalid.');
        error.statusCode = 400;
        throw error;
      }
      const existing = [...jobs.values()].find((job) => job.requestId === requestId);
      if (existing) {
        await fs.rm(uploadedPath, { force: true });
        response.status(200).json({ production: publicJob(existing), reused: true });
        return;
      }

      const intent = fieldValue(fields, 'intent');
      if (!['podcast', 'natural_voice', 'broadcast', 'social_voice'].includes(intent)) {
        const error = new Error('Choose a supported quick-start intent.');
        error.statusCode = 400;
        throw error;
      }
      const templateVersionId = fieldValue(fields, 'templateVersionId') || null;
      if (templateVersionId && !validOpaqueId(templateVersionId)) {
        const error = new Error('The template version identifier is invalid.');
        error.statusCode = 400;
        throw error;
      }
      let settings;
      try {
        settings = JSON.parse(fieldValue(fields, 'settings') || '{}');
      } catch {
        const error = new Error('Settings must be valid JSON.');
        error.statusCode = 400;
        throw error;
      }

      const jobId = randomUUID();
      provisionalJobId = jobId;
      const directory = jobDirectory(jobId);
      const settingsPath = withinRoot(directory, 'request-settings.json');
      await fs.mkdir(directory, { recursive: true });
      await writeJsonAtomic(settingsPath, settings);
      await validateSettings(settingsPath);

      const sourceSha = await sha256File(uploadedPath);
      const extension = safeMediaExtension(uploaded.originalFilename);
      const sourceDirectory = withinRoot(SOURCES_DIR, sourceSha);
      const sourcePath = withinRoot(sourceDirectory, `source${extension}`);
      await fs.mkdir(sourceDirectory, { recursive: true });
      try {
        await fs.copyFile(uploadedPath, sourcePath, 1);
      } catch (error) {
        if (error.code !== 'EEXIST') throw error;
      }
      await fs.rm(uploadedPath, { force: true });
      uploadedPath = null;

      const now = new Date().toISOString();
      const job = {
        id: jobId,
        requestId,
        title: normalizeTitle(fieldValue(fields, 'title'), uploaded.originalFilename || 'Untitled production'),
        status: 'queued',
        intent,
        templateVersionId,
        settings,
        settingsPath,
        source: {
          path: sourcePath,
          sha256: sourceSha,
          filename: String(uploaded.originalFilename || 'source').slice(0, 255),
          sizeBytes: uploaded.size,
          mimeType: uploaded.mimetype || 'application/octet-stream',
        },
        outputDirectory: withinRoot(directory, 'output'),
        createdAt: now,
        updatedAt: now,
        startedAt: null,
        completedAt: null,
        currentStep: 'queued',
        completedSteps: [],
        progressPercent: 0,
        attempt: 0,
        error: null,
        result: null,
        summary: null,
      };
      jobs.set(job.id, job);
      await persistJob(job);
      provisionalJobId = null;
      enqueue(job.id);
      response.status(202).json({ production: publicJob(job), reused: false });
    } catch (error) {
      if (uploadedPath) await fs.rm(uploadedPath, { force: true }).catch(() => {});
      if (provisionalJobId) {
        jobs.delete(provisionalJobId);
        await fs.rm(jobDirectory(provisionalJobId), { recursive: true, force: true }).catch(() => {});
      }
      next(error);
    }
  });

  app.get('/api/v2/productions/:id', (request, response) => {
    const job = jobs.get(request.params.id);
    if (!job) return response.status(404).json({ error: { code: 'not_found', message: 'Production not found.' } });
    response.json({ production: publicJob(job) });
  });

  app.post('/api/v2/productions/:id/retry', async (request, response, next) => {
    try {
      const job = jobs.get(request.params.id);
      if (!job) return response.status(404).json({ error: { code: 'not_found', message: 'Production not found.' } });
      if (!['failed', 'interrupted'].includes(job.status)) {
        return response.status(409).json({
          error: { code: 'not_retryable', message: 'Only failed or interrupted beta runs can be retried.' },
        });
      }
      await fs.rm(job.outputDirectory, { recursive: true, force: true });
      job.status = 'queued';
      job.currentStep = 'queued';
      job.completedSteps = [];
      job.progressPercent = 0;
      job.error = null;
      await persistJob(job);
      enqueue(job.id);
      response.status(202).json({ production: publicJob(job) });
    } catch (error) {
      next(error);
    }
  });

  app.delete('/api/v2/productions/:id', async (request, response, next) => {
    try {
      const job = jobs.get(request.params.id);
      if (!job) return response.status(204).end();
      if (active?.jobId === job.id) {
        pendingDeletion.add(job.id);
        jobs.delete(job.id);
        active.child?.kill('SIGTERM');
        return response.status(202).json({ status: 'deleting' });
      }
      await deleteJobFiles(job);
      response.status(204).end();
    } catch (error) {
      next(error);
    }
  });

  app.get('/api/v2/productions/:id/waveform', async (request, response, next) => {
    try {
      const job = jobs.get(request.params.id);
      if (!job || job.status !== 'succeeded') {
        return response.status(404).json({ error: { code: 'not_ready', message: 'Waveform is not ready.' } });
      }
      response.sendFile(path.join(job.outputDirectory, 'waveform-peaks.json'));
    } catch (error) {
      next(error);
    }
  });

  app.get('/api/v2/productions/:id/report', async (request, response, next) => {
    try {
      const job = jobs.get(request.params.id);
      if (!job || job.status !== 'succeeded') {
        return response.status(404).json({ error: { code: 'not_ready', message: 'Report is not ready.' } });
      }
      response.setHeader('Content-Disposition', `attachment; filename="ampersand-${job.id}-report.json"`);
      response.sendFile(path.join(job.outputDirectory, 'processing-report.json'));
    } catch (error) {
      next(error);
    }
  });

  app.get('/api/v2/productions/:id/media/:kind', async (request, response, next) => {
    try {
      const job = jobs.get(request.params.id);
      if (!job) return response.status(404).json({ error: { code: 'not_found', message: 'Production not found.' } });
      const media = {
        original: { filename: job.source.path, type: job.source.mimeType, download: job.source.filename },
        wav: {
          filename: path.join(job.outputDirectory, 'artifacts', 'master.wav'),
          type: 'audio/wav',
          download: `${job.title}.wav`,
        },
        mp3: {
          filename: path.join(job.outputDirectory, 'artifacts', 'master.mp3'),
          type: 'audio/mpeg',
          download: `${job.title}.mp3`,
        },
      }[request.params.kind];
      if (!media || (request.params.kind !== 'original' && job.status !== 'succeeded')) {
        return response.status(404).json({ error: { code: 'not_ready', message: 'Media is not ready.' } });
      }
      await fs.access(media.filename);
      response.setHeader('Content-Type', media.type);
      response.setHeader('Content-Disposition', `inline; filename="${safeDownloadFilename(media.download)}"`);
      response.sendFile(media.filename);
    } catch (error) {
      if (error.code === 'ENOENT') {
        return response.status(404).json({ error: { code: 'not_ready', message: 'Requested output is unavailable.' } });
      }
      next(error);
    }
  });

  app.use('/api/v2', (_request, response) => {
    response.status(404).json({ error: { code: 'not_found', message: 'API route not found.' } });
  });
  app.use(express.static(STATIC_DIR, { index: false, maxAge: '1h', etag: true }));
  app.get('*', (_request, response) => {
    response.setHeader('Cache-Control', 'no-cache');
    response.sendFile(path.join(STATIC_DIR, 'index.html'));
  });
  app.use((error, _request, response, _next) => {
    const status = Number(error.statusCode || error.httpCode || (error.code === 1009 ? 413 : 500));
    const message = status >= 500 ? 'The beta service could not complete that request.' : safeErrorMessage(error.message);
    response.status(status).json({
      error: { code: status === 413 ? 'upload_too_large' : 'request_failed', message },
    });
  });
  return app;
}

async function main() {
  if (BETA_TOKEN.length < 24) {
    throw new Error('AMPERSAND_BETA_TOKEN must be configured with at least 24 characters.');
  }
  const app = await createApp();
  const server = app.listen(PORT, '0.0.0.0', () => {
    console.log(`Ampersand private beta listening on port ${PORT}.`);
    console.log('Private beta API access is enabled.');
  });
  const shutdown = () => {
    active?.child?.kill('SIGTERM');
    server.close(() => process.exit(0));
  };
  process.once('SIGTERM', shutdown);
  process.once('SIGINT', shutdown);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  void main().catch((error) => {
    console.error(`Ampersand startup failed: ${safeErrorMessage(error?.message)}`);
    process.exitCode = 1;
  });
}
