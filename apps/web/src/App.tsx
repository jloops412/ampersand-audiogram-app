import { FormEvent, useEffect, useMemo, useRef, useState } from 'react';

import {
  ApiError,
  createProduction,
  deleteProduction,
  getProduction,
  getWaveform,
  listProductions,
  openSession,
  retryProduction,
  savedToken,
} from './api';
import {
  BUILT_IN_TEMPLATES,
  cloneSettings,
  createOrVersionTemplate,
  flattenUserTemplates,
  loadUserTemplates,
  saveUserTemplates,
} from './templates';
import type {
  Production,
  ProductionIntent,
  ProductionSettings,
  SelectableTemplate,
  UserTemplate,
  WaveformPeaks,
} from './types';
import { Waveform } from './Waveform';

type View = 'library' | 'new' | 'production';
const MAX_DIRECT_UPLOAD_BYTES = 30 * 1024 * 1024;

const STEP_LABELS = [
  ['validate/probe', 'Validate source'],
  ['canonicalize if needed', 'Prepare working audio'],
  ['measure, build waveform, and analyze semantics', 'Analyze audio'],
  ['build Processing Router V0 shadow plan', 'Plan safe processing'],
  ['plan Adaptive Leveler shadow candidate', 'Analyze leveling'],
  ['render deterministic WAV and MP3', 'Master and encode'],
  ['validate outputs and report', 'Validate delivery'],
] as const;

const INTENT_COPY: Record<ProductionIntent, { eyebrow: string; description: string }> = {
  podcast: { eyebrow: '-16 LUFS', description: 'A familiar podcast delivery level with balanced dynamics.' },
  natural_voice: { eyebrow: '-18 LUFS', description: 'Gentler gain for ceremonies, interviews, and emotional speech.' },
  broadcast: { eyebrow: '-23 LUFS', description: 'Conservative broadcast-style program loudness.' },
  social_voice: { eyebrow: '-14 LUFS', description: 'A louder voice-forward target for social playback.' },
};

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  const units = ['KB', 'MB', 'GB'];
  let value = bytes / 1024;
  let unit = units[0];
  for (let index = 1; index < units.length && value >= 1024; index += 1) {
    value /= 1024;
    unit = units[index];
  }
  return `${value.toFixed(value >= 10 ? 1 : 2)} ${unit}`;
}

function formatDuration(microseconds: number): string {
  const seconds = Math.round(microseconds / 1_000_000);
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainder = seconds % 60;
  return hours > 0
    ? `${hours}:${String(minutes).padStart(2, '0')}:${String(remainder).padStart(2, '0')}`
    : `${minutes}:${String(remainder).padStart(2, '0')}`;
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }).format(
    new Date(value),
  );
}

function statusLabel(status: Production['status']): string {
  return {
    queued: 'Queued',
    running: 'Processing',
    succeeded: 'Ready',
    failed: 'Needs attention',
    interrupted: 'Interrupted',
  }[status];
}

function StatusPill({ status }: { status: Production['status'] }) {
  return <span className={`status-pill status-${status}`}><i />{statusLabel(status)}</span>;
}

function BrandMark() {
  return <span className="brand-mark" aria-hidden="true">&amp;</span>;
}

function AccessGate({ onUnlock }: { onUnlock: () => void }) {
  const [token, setToken] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      await openSession(token.trim());
      onUnlock();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not open the beta.');
    } finally {
      setBusy(false);
    }
  };
  return (
    <main className="access-shell">
      <div className="access-card">
        <BrandMark />
        <p className="eyebrow">Ampersand private beta</p>
        <h1>Welcome back.</h1>
        <p>This preview processes private audio with Ampersand’s independent deterministic engine.</p>
        <form onSubmit={submit}>
          <label htmlFor="beta-token">Beta access key</label>
          <input
            id="beta-token"
            type="password"
            value={token}
            onChange={(event) => setToken(event.target.value)}
            autoComplete="current-password"
            autoFocus
          />
          {error && <p className="form-error" role="alert">{error}</p>}
          <button className="button button-primary" disabled={busy || !token.trim()}>
            {busy ? 'Opening…' : 'Open Studio'}
          </button>
        </form>
      </div>
    </main>
  );
}

function LibraryView({
  productions,
  onOpen,
  onNew,
  onDelete,
}: {
  productions: Production[];
  onOpen: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
}) {
  return (
    <section className="page page-library">
      <div className="page-heading">
        <div>
          <p className="eyebrow">Your work</p>
          <h1>Productions</h1>
          <p>Source media stays immutable. Every master keeps its exact settings and processing report.</p>
        </div>
        <button className="button button-primary" onClick={onNew}>New production</button>
      </div>
      {productions.length === 0 ? (
        <div className="empty-state">
          <span className="empty-wave" aria-hidden="true">⌁⌁⌁</span>
          <h2>Make the first master.</h2>
          <p>Upload spoken-word audio, choose a starting point, then tune the delivery settings.</p>
          <button className="button button-primary" onClick={onNew}>Start a production</button>
        </div>
      ) : (
        <div className="production-grid">
          {productions.map((production) => (
            <article className="production-card" key={production.id}>
              <button className="card-open" onClick={() => onOpen(production.id)} aria-label={`Open ${production.title}`}>
                <div className="mini-wave" aria-hidden="true"><i /><i /><i /><i /><i /><i /><i /></div>
                <div className="card-body">
                  <StatusPill status={production.status} />
                  <h2>{production.title}</h2>
                  <p>{production.source.filename}</p>
                  <dl>
                    <div><dt>Target</dt><dd>{production.settings.mastering.target_integrated_lufs} LUFS</dd></div>
                    <div><dt>Created</dt><dd>{formatDate(production.createdAt)}</dd></div>
                  </dl>
                </div>
              </button>
              <button className="icon-button delete-button" onClick={() => onDelete(production.id)} aria-label={`Delete ${production.title}`}>×</button>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

function NewProductionView({
  onCreated,
  onCancel,
}: {
  onCreated: (production: Production) => void;
  onCancel: () => void;
}) {
  const [source, setSource] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [userTemplates, setUserTemplates] = useState<UserTemplate[]>(loadUserTemplates);
  const allTemplates = useMemo(
    () => [...BUILT_IN_TEMPLATES, ...flattenUserTemplates(userTemplates)],
    [userTemplates],
  );
  const [selected, setSelected] = useState<SelectableTemplate>(BUILT_IN_TEMPLATES[0]);
  const [intent, setIntent] = useState<ProductionIntent>(selected.intent);
  const [settings, setSettings] = useState<ProductionSettings>(cloneSettings(selected.settings));
  const [dirty, setDirty] = useState(false);
  const [templateName, setTemplateName] = useState('');
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const applyTemplate = (template: SelectableTemplate) => {
    setSelected(template);
    setIntent(template.intent);
    setSettings(cloneSettings(template.settings));
    setDirty(false);
    setTemplateName(template.builtIn ? '' : template.name);
  };
  const updateSettings = (updater: (current: ProductionSettings) => ProductionSettings) => {
    setSettings((current) => updater(cloneSettings(current)));
    setDirty(true);
  };
  const chooseIntent = (nextIntent: ProductionIntent) => {
    const template = BUILT_IN_TEMPLATES.find((item) => item.intent === nextIntent) || BUILT_IN_TEMPLATES[0];
    applyTemplate(template);
  };
  const saveTemplate = () => {
    const name = templateName.trim() || (selected.builtIn ? `${selected.name} copy` : selected.name);
    const selectedTemplateId = selected.builtIn ? null : selected.templateId;
    const result = createOrVersionTemplate(userTemplates, name, intent, selectedTemplateId, settings);
    setUserTemplates(result.templates);
    saveUserTemplates(result.templates);
    setSelected(result.selected);
    setTemplateName(result.selected.name);
    setDirty(false);
  };
  const acceptFile = (file: File | null) => {
    if (!file) return;
    if (file.size > MAX_DIRECT_UPLOAD_BYTES) {
      setSource(null);
      setError('This first Cloud Run beta accepts files up to 30 MB. Direct-to-storage uploads are next.');
      return;
    }
    setSource(file);
    if (!title) setTitle(file.name.replace(/\.[^.]+$/, ''));
    setError('');
  };
  const submit = async () => {
    if (!source) {
      setError('Choose an audio file first.');
      return;
    }
    setBusy(true);
    setError('');
    try {
      const production = await createProduction({
        source,
        title: title.trim() || source.name,
        intent,
        templateVersionId: dirty ? null : selected.templateVersionId,
        settings,
      });
      onCreated(production);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not start this production.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="page page-new">
      <button className="back-link" onClick={onCancel}>← Productions</button>
      <div className="page-heading compact-heading">
        <div>
          <p className="eyebrow">New production</p>
          <h1>Shape the delivery.</h1>
          <p>Start simply, then adjust only the settings Ampersand can execute today.</p>
        </div>
      </div>

      <div className="new-layout">
        <div className="new-main">
          <section className="studio-section">
            <div className="section-number">01</div>
            <div className="section-content">
              <div className="section-heading"><div><h2>Add your audio</h2><p>WAV, MP3, M4A, FLAC, or another FFmpeg-readable audio file · 30 MB beta limit.</p></div></div>
              <div
                className={`drop-zone ${dragging ? 'is-dragging' : ''} ${source ? 'has-file' : ''}`}
                onDragEnter={(event) => { event.preventDefault(); setDragging(true); }}
                onDragOver={(event) => event.preventDefault()}
                onDragLeave={() => setDragging(false)}
                onDrop={(event) => { event.preventDefault(); setDragging(false); acceptFile(event.dataTransfer.files[0] || null); }}
                onClick={() => fileInputRef.current?.click()}
                role="button"
                tabIndex={0}
                onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') fileInputRef.current?.click(); }}
              >
                <input ref={fileInputRef} type="file" accept="audio/*,.m4a,.flac,.ogg,.opus" onChange={(event) => acceptFile(event.target.files?.[0] || null)} hidden />
                <span className="upload-glyph" aria-hidden="true">↑</span>
                {source ? <><strong>{source.name}</strong><span>{formatBytes(source.size)} · click to replace</span></> : <><strong>Drop audio here</strong><span>or choose a file from your device</span></>}
              </div>
              <label className="field-label" htmlFor="production-title">Production title</label>
              <input id="production-title" className="text-input" value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Episode, ceremony, interview…" />
            </div>
          </section>

          <section className="studio-section">
            <div className="section-number">02</div>
            <div className="section-content">
              <div className="section-heading"><div><h2>Choose a starting point</h2><p>These shortcuts fill real mastering values. You can tune every value below.</p></div></div>
              <div className="intent-grid">
                {BUILT_IN_TEMPLATES.map((template) => (
                  <button key={template.intent} className={`intent-card ${intent === template.intent ? 'selected' : ''}`} onClick={() => chooseIntent(template.intent)}>
                    <span>{INTENT_COPY[template.intent].eyebrow}</span>
                    <strong>{template.name}</strong>
                    <small>{INTENT_COPY[template.intent].description}</small>
                  </button>
                ))}
              </div>
              <div className="template-row">
                <label htmlFor="template-select">Reusable template</label>
                <select id="template-select" value={selected.key} onChange={(event) => {
                  const template = allTemplates.find((item) => item.key === event.target.value);
                  if (template) applyTemplate(template);
                }}>
                  <optgroup label="Built in">
                    {BUILT_IN_TEMPLATES.map((template) => <option key={template.key} value={template.key}>{template.name} · v{template.version}</option>)}
                  </optgroup>
                  {userTemplates.length > 0 && <optgroup label="Your templates">
                    {flattenUserTemplates(userTemplates).map((template) => <option key={template.key} value={template.key}>{template.name} · v{template.version}</option>)}
                  </optgroup>}
                </select>
              </div>
            </div>
          </section>

          <section className="studio-section">
            <div className="section-number">03</div>
            <div className="section-content">
              <div className="section-heading"><div><h2>Mastering settings</h2><p>Safe beta ranges, stored exactly with this run.</p></div><span className="live-chip">Executable</span></div>
              <div className="control-stack">
                <label className="range-control">
                  <span><strong>Integrated loudness</strong><small>Overall delivery level</small></span>
                  <input type="range" min="-24" max="-14" step="0.5" value={settings.mastering.target_integrated_lufs} onChange={(event) => updateSettings((next) => { next.mastering.target_integrated_lufs = Number(event.target.value); return next; })} />
                  <output>{settings.mastering.target_integrated_lufs.toFixed(1)} LUFS</output>
                </label>
                <label className="range-control">
                  <span><strong>True-peak ceiling</strong><small>Headroom for delivery codecs</small></span>
                  <input type="range" min="-3" max="-1" step="0.1" value={settings.mastering.max_true_peak_dbtp} onChange={(event) => updateSettings((next) => { next.mastering.max_true_peak_dbtp = Number(event.target.value); return next; })} />
                  <output>{settings.mastering.max_true_peak_dbtp.toFixed(1)} dBTP</output>
                </label>
                <label className="range-control">
                  <span><strong>Loudness range target</strong><small>How much program dynamics to retain</small></span>
                  <input type="range" min="5" max="20" step="1" value={settings.mastering.target_loudness_range_lu} onChange={(event) => updateSettings((next) => { next.mastering.target_loudness_range_lu = Number(event.target.value); return next; })} />
                  <output>{settings.mastering.target_loudness_range_lu.toFixed(0)} LU</output>
                </label>
              </div>

              <div className="engine-boundaries">
                <article><span className="boundary-icon">◎</span><div><strong>Semantic analysis</strong><p>Waveform, loudness, speech probability, and safe routing report included.</p></div><em>On</em></article>
                <article><span className="boundary-icon">≈</span><div><strong>Adaptive Leveler</strong><p>Analyzed and reported, but not yet applied until listening approval.</p></div><em>Shadow</em></article>
                <article><span className="boundary-icon">✦</span><div><strong>Neural cleanup</strong><p>Protected in this beta; no private audio is sent to an outside processor.</p></div><em>Off</em></article>
              </div>
            </div>
          </section>

          <section className="studio-section">
            <div className="section-number">04</div>
            <div className="section-content">
              <div className="section-heading"><div><h2>Delivery</h2><p>Choose one or both validated outputs.</p></div></div>
              <div className="delivery-grid">
                <label className={`format-card ${settings.export.wav ? 'selected' : ''}`}>
                  <input type="checkbox" checked={settings.export.wav} onChange={(event) => updateSettings((next) => {
                    if (!event.target.checked && !next.export.mp3) return next;
                    next.export.wav = event.target.checked; return next;
                  })} />
                  <span>WAV</span><strong>24-bit / 48 kHz</strong><small>Archive and editing master</small>
                </label>
                <label className={`format-card ${settings.export.mp3 ? 'selected' : ''}`}>
                  <input type="checkbox" checked={settings.export.mp3} onChange={(event) => updateSettings((next) => {
                    if (!event.target.checked && !next.export.wav) return next;
                    next.export.mp3 = event.target.checked; return next;
                  })} />
                  <span>MP3</span><strong>Delivery copy</strong><small>Portable spoken-word output</small>
                </label>
              </div>
              {settings.export.mp3 && <label className="select-control"><span>MP3 bitrate</span><select value={settings.export.mp3_bitrate_kbps} onChange={(event) => updateSettings((next) => { next.export.mp3_bitrate_kbps = Number(event.target.value) as 128 | 160 | 192 | 256 | 320; return next; })}><option value="128">128 kbps</option><option value="160">160 kbps</option><option value="192">192 kbps</option><option value="256">256 kbps</option><option value="320">320 kbps</option></select></label>}
            </div>
          </section>
        </div>

        <aside className="run-sidebar">
          <div className="run-card">
            <p className="eyebrow">Run summary</p>
            <h2>{title || source?.name.replace(/\.[^.]+$/, '') || 'Untitled production'}</h2>
            <dl className="summary-list">
              <div><dt>Starting point</dt><dd>{selected.name}{dirty ? ' · modified' : ` · v${selected.version}`}</dd></div>
              <div><dt>Loudness</dt><dd>{settings.mastering.target_integrated_lufs.toFixed(1)} LUFS</dd></div>
              <div><dt>Peak ceiling</dt><dd>{settings.mastering.max_true_peak_dbtp.toFixed(1)} dBTP</dd></div>
              <div><dt>Outputs</dt><dd>{[settings.export.wav && 'WAV', settings.export.mp3 && 'MP3'].filter(Boolean).join(' + ')}</dd></div>
            </dl>
            <div className="privacy-note"><span>⌾</span><p><strong>Private by design</strong> No hosted audio processor, no external processing API, no training use.</p></div>
            {error && <p className="form-error" role="alert">{error}</p>}
            <button className="button button-primary button-block" onClick={submit} disabled={busy || !source}>{busy ? 'Uploading…' : 'Create master'}</button>
            <small className="run-hint">You may close this page after the job is queued.</small>
          </div>
          <div className="template-save-card">
            <h3>{selected.builtIn ? 'Save as your template' : 'Create a new version'}</h3>
            <p>Reuse these exact settings later. Existing versions stay unchanged.</p>
            <input className="text-input" value={templateName} onChange={(event) => setTemplateName(event.target.value)} placeholder={selected.builtIn ? `${selected.name} copy` : selected.name} />
            <button className="button button-secondary button-block" onClick={saveTemplate}>{selected.builtIn ? 'Save template' : 'Save new version'}</button>
          </div>
        </aside>
      </div>
    </section>
  );
}

function ProductionView({ production, onBack, onRetry, onDelete }: { production: Production; onBack: () => void; onRetry: () => void; onDelete: () => void }) {
  const [waveform, setWaveform] = useState<WaveformPeaks | null>(null);
  const [listenMode, setListenMode] = useState<'original' | 'master'>('master');
  const audioRef = useRef<HTMLAudioElement>(null);
  const pendingPlayback = useRef<{ time: number; paused: boolean } | null>(null);
  const masterUrl = production.outputs?.mp3 || production.outputs?.wav || null;
  const audioUrl = listenMode === 'master' && masterUrl ? masterUrl : production.outputs?.original || '';

  useEffect(() => {
    if (!production.outputs?.waveform) return;
    getWaveform(production.outputs.waveform).then(setWaveform).catch(() => setWaveform(null));
  }, [production.outputs?.waveform]);

  const switchAudio = (mode: 'original' | 'master') => {
    if (mode === listenMode || (mode === 'master' && !masterUrl)) return;
    const audio = audioRef.current;
    pendingPlayback.current = audio ? { time: audio.currentTime, paused: audio.paused } : null;
    setListenMode(mode);
  };
  const restorePosition = () => {
    const audio = audioRef.current;
    const pending = pendingPlayback.current;
    if (!audio || !pending) return;
    audio.currentTime = Math.min(pending.time, Number.isFinite(audio.duration) ? audio.duration : pending.time);
    if (!pending.paused) void audio.play();
    pendingPlayback.current = null;
  };

  const summary = production.summary;
  const completed = new Set(production.completedSteps);
  return (
    <section className="page page-production">
      <button className="back-link" onClick={onBack}>← Productions</button>
      <div className="production-title-row">
        <div><StatusPill status={production.status} /><h1>{production.title}</h1><p>{production.source.filename} · {formatBytes(production.source.sizeBytes)}</p></div>
        <button className="button button-danger-quiet" onClick={onDelete}>Delete production</button>
      </div>

      {production.status === 'succeeded' && production.outputs ? (
        <>
          <section className="listen-panel">
            <div className="listen-heading">
              <div><p className="eyebrow">Same-position comparison</p><h2>Hear what changed.</h2></div>
              <div className="ab-toggle" role="group" aria-label="Choose original or master">
                <button className={listenMode === 'original' ? 'selected' : ''} onClick={() => switchAudio('original')}>Original</button>
                <button className={listenMode === 'master' ? 'selected' : ''} onClick={() => switchAudio('master')}>Master</button>
              </div>
            </div>
            <Waveform waveform={waveform} />
            <audio ref={audioRef} src={audioUrl} controls preload="metadata" onLoadedMetadata={restorePosition} />
          </section>

          <div className="result-grid">
            <section className="result-card loudness-card">
              <p className="eyebrow">Measured delivery</p>
              <div className="metric-comparison"><div><span>Before</span><strong>{summary?.loudnessBefore.integrated_lufs.toFixed(1)}</strong><small>LUFS</small></div><i>→</i><div><span>Master</span><strong>{summary?.loudnessAfter.integrated_lufs.toFixed(1)}</strong><small>LUFS</small></div></div>
              <dl><div><dt>True peak</dt><dd>{summary?.loudnessAfter.true_peak_dbtp.toFixed(1)} dBTP</dd></div><div><dt>Duration</dt><dd>{summary ? formatDuration(summary.durationUs) : '—'}</dd></div><div><dt>External API cost</dt><dd>${summary?.externalApiCostUsd.toFixed(2)}</dd></div></dl>
            </section>
            <section className="result-card download-card">
              <p className="eyebrow">Delivery files</p><h2>Ready to use.</h2>
              <div className="download-list">
                {production.outputs.wav && <a href={production.outputs.wav} download><span>WAV</span><div><strong>24-bit master</strong><small>For archive and editing</small></div><b>↓</b></a>}
                {production.outputs.mp3 && <a href={production.outputs.mp3} download><span>MP3</span><div><strong>{production.settings.export.mp3_bitrate_kbps} kbps delivery</strong><small>For upload and sharing</small></div><b>↓</b></a>}
                <a href={production.outputs.report} download><span>JSON</span><div><strong>Processing report</strong><small>Decisions, versions, and hashes</small></div><b>↓</b></a>
              </div>
            </section>
          </div>

          <section className="report-panel">
            <div><p className="eyebrow">Ampersand report</p><h2>What the engine did</h2></div>
            <ol>{summary?.decisions.map((decision) => <li key={decision}>{decision}</li>)}</ol>
            <details><summary>Beta limitations and warnings ({summary?.warnings.length || 0})</summary><ul>{summary?.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul></details>
            <p className="settings-proof">Resolved settings <code>{summary?.resolvedSettingsId}</code> · <code>{summary?.resolvedSettingsSha256.slice(0, 12)}…</code></p>
          </section>
        </>
      ) : (
        <section className="processing-layout">
          <div className="processing-hero">
            <div className="progress-ring" style={{ '--progress': `${production.progressPercent * 3.6}deg` } as React.CSSProperties}><span>{production.progressPercent}%</span></div>
            <p className="eyebrow">{production.status === 'queued' ? 'Waiting for the engine' : production.status === 'running' ? 'Processing independently' : 'Run stopped'}</p>
            <h2>{production.currentStep}</h2>
            <p>{production.status === 'running' || production.status === 'queued' ? 'This production is saved. You can close the tab and return.' : production.error?.message}</p>
            {(production.status === 'failed' || production.status === 'interrupted') && <button className="button button-primary" onClick={onRetry}>Retry without re-uploading</button>}
          </div>
          <ol className="step-list">
            {STEP_LABELS.map(([key, label], index) => {
              const done = completed.has(key);
              const active = production.currentStep === key;
              return <li key={key} className={done ? 'done' : active ? 'active' : ''}><span>{done ? '✓' : String(index + 1).padStart(2, '0')}</span><div><strong>{label}</strong><small>{done ? 'Complete' : active ? 'In progress' : 'Pending'}</small></div></li>;
            })}
          </ol>
        </section>
      )}
    </section>
  );
}

export default function App() {
  const [view, setView] = useState<View>('library');
  const [productions, setProductions] = useState<Production[]>([]);
  const [currentId, setCurrentId] = useState<string | null>(null);
  const [locked, setLocked] = useState(false);
  const [loading, setLoading] = useState(true);
  const [globalError, setGlobalError] = useState('');
  const current = productions.find((production) => production.id === currentId) || null;

  const refresh = async () => {
    const values = await listProductions();
    setProductions(values);
  };
  const bootstrap = async () => {
    setLoading(true);
    setGlobalError('');
    try {
      await openSession(savedToken());
      await refresh();
      setLocked(false);
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 401) setLocked(true);
      else setGlobalError(caught instanceof Error ? caught.message : 'Could not load the Studio.');
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => { void bootstrap(); }, []);
  useEffect(() => {
    if (!current || !['queued', 'running'].includes(current.status)) return;
    const timer = window.setInterval(() => {
      getProduction(current.id).then((updated) => {
        setProductions((items) => [updated, ...items.filter((item) => item.id !== updated.id)]);
      }).catch(() => {});
    }, 1500);
    return () => window.clearInterval(timer);
  }, [current]);

  const openProduction = (id: string) => { setCurrentId(id); setView('production'); window.scrollTo(0, 0); };
  const removeProduction = async (id: string) => {
    const production = productions.find((item) => item.id === id);
    if (!window.confirm(`Delete “${production?.title || 'this production'}” and its source and outputs?`)) return;
    try {
      await deleteProduction(id);
      setProductions((items) => items.filter((item) => item.id !== id));
      if (currentId === id) { setCurrentId(null); setView('library'); }
    } catch (caught) {
      setGlobalError(caught instanceof Error ? caught.message : 'Could not delete this production.');
    }
  };

  if (loading) return <main className="loading-shell"><BrandMark /><span>Opening Ampersand…</span></main>;
  if (locked) return <AccessGate onUnlock={() => void bootstrap()} />;
  return (
    <div className="app-shell">
      <header className="site-header">
        <button className="brand" onClick={() => setView('library')}><BrandMark /><span>Ampersand</span><small>Private beta</small></button>
        <nav aria-label="Main navigation">
          <button className={view === 'library' ? 'active' : ''} onClick={() => setView('library')}>Productions</button>
          <button className={view === 'new' ? 'active' : ''} onClick={() => setView('new')}>New master</button>
        </nav>
        <span className="engine-badge"><i />Independent engine</span>
      </header>
      {globalError && <div className="global-error" role="alert"><span>{globalError}</span><button onClick={() => setGlobalError('')}>×</button></div>}
      {view === 'library' && <LibraryView productions={productions} onOpen={openProduction} onNew={() => setView('new')} onDelete={(id) => void removeProduction(id)} />}
      {view === 'new' && <NewProductionView onCancel={() => setView('library')} onCreated={(production) => { setProductions((items) => [production, ...items]); openProduction(production.id); }} />}
      {view === 'production' && current && <ProductionView production={current} onBack={() => setView('library')} onDelete={() => void removeProduction(current.id)} onRetry={() => { retryProduction(current.id).then((updated) => setProductions((items) => [updated, ...items.filter((item) => item.id !== updated.id)])).catch((caught) => setGlobalError(caught.message)); }} />}
      {view === 'production' && !current && <LibraryView productions={productions} onOpen={openProduction} onNew={() => setView('new')} onDelete={(id) => void removeProduction(id)} />}
      <footer><span>Ampersand beta · deterministic mastering</span><span>Independent engine · no external API cost</span></footer>
    </div>
  );
}
