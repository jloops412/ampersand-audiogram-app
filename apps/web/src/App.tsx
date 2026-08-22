import { FormEvent, useEffect, useMemo, useRef, useState } from 'react';

import {
  ApiError,
  createProduction,
  deleteProduction,
  getCapabilities,
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
  Capabilities,
  Production,
  ProductionIntent,
  ProductionSettings,
  SelectableTemplate,
  UserTemplate,
  WaveformPeaks,
} from './types';
import { Waveform } from './Waveform';
import { AudiogramPreview } from './AudiogramPreview';

type View = 'library' | 'new' | 'production';

const STEP_LABELS = [
  ['validate/probe', 'Validate source'],
  ['canonicalize if needed', 'Prepare working audio'],
  ['measure, build waveform, and analyze semantics', 'Analyze audio'],
  ['build Processing Router V0 shadow plan', 'Plan safe processing'],
  ['plan Adaptive Leveler shadow candidate', 'Analyze leveling'],
  ['apply deterministic cleanup and compression', 'Clean noise and even dynamics'],
  ['render deterministic WAV and MP3', 'Master and encode'],
  ['render audiogram MP4', 'Render audiogram'],
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
  onCreated: (productions: Production[]) => void;
  onCancel: () => void;
}) {
  const [sources, setSources] = useState<File[]>([]);
  const [title, setTitle] = useState('');
  const [artwork, setArtwork] = useState<File | null>(null);
  const [capabilities, setCapabilities] = useState<Capabilities | null>(null);
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
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadPhase, setUploadPhase] = useState('');
  const [error, setError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const artworkInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    getCapabilities().then(setCapabilities).catch((caught) => {
      setError(caught instanceof Error ? caught.message : 'Could not read upload capabilities.');
    });
  }, []);

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
  const acceptFiles = (files: FileList | File[]) => {
    const selectedFiles = Array.from(files);
    if (!selectedFiles.length) return;
    const maximum = capabilities?.directUpload.enabled
      ? capabilities.directUpload.maxBytes
      : capabilities?.maxUploadBytes || 30 * 1024 * 1024;
    const tooLarge = selectedFiles.find((file) => file.size > maximum);
    if (tooLarge) {
      setError(`${tooLarge.name} is larger than this revision's ${formatBytes(maximum)} upload limit.`);
      return;
    }
    setSources(selectedFiles);
    if (!title && selectedFiles.length === 1) setTitle(selectedFiles[0].name.replace(/\.[^.]+$/, ''));
    setError('');
  };
  const submit = async () => {
    if (!sources.length || !capabilities) {
      setError(capabilities ? 'Choose at least one audio file first.' : 'Upload capabilities are still loading.');
      return;
    }
    if (settings.audiogram.enabled && ['artwork', 'video'].includes(settings.audiogram.background_mode) && !artwork) {
      setError('Choose background media for the audiogram.');
      return;
    }
    if (artwork && artwork.size > capabilities.maxArtworkBytes) {
      setError(`${artwork.name} is larger than this revision's ${formatBytes(capabilities.maxArtworkBytes)} background-media limit.`);
      return;
    }
    setBusy(true);
    setError('');
    try {
      const created: Production[] = [];
      for (let index = 0; index < sources.length; index += 1) {
        const source = sources[index];
        const production = await createProduction({
          source,
          artwork:
            settings.audiogram.enabled && ['artwork', 'video'].includes(settings.audiogram.background_mode)
              ? artwork
              : null,
          title: sources.length === 1 ? title.trim() || source.name : source.name.replace(/\.[^.]+$/, ''),
          intent,
          templateVersionId: dirty ? null : selected.templateVersionId,
          settings,
          capabilities,
          onProgress: (progress, phase) => {
            setUploadProgress(((index + progress / 100) / sources.length) * 100);
            setUploadPhase(`${phase} · file ${index + 1} of ${sources.length}`);
          },
        });
        created.push(production);
      }
      onCreated(created);
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
              <div className="section-heading"><div><h2>Add your audio</h2><p>Choose one file or a batch. Large WAV, MP3, M4A, FLAC, OGG, Opus, and other FFmpeg-readable formats upload directly to private storage.</p></div><span className="live-chip">Resumable</span></div>
              <div
                className={`drop-zone ${dragging ? 'is-dragging' : ''} ${sources.length ? 'has-file' : ''}`}
                onDragEnter={(event) => { event.preventDefault(); setDragging(true); }}
                onDragOver={(event) => event.preventDefault()}
                onDragLeave={() => setDragging(false)}
                onDrop={(event) => { event.preventDefault(); setDragging(false); acceptFiles(event.dataTransfer.files); }}
                onClick={() => fileInputRef.current?.click()}
                role="button"
                tabIndex={0}
                onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') fileInputRef.current?.click(); }}
              >
                <input ref={fileInputRef} type="file" accept="audio/*,.wav,.mp3,.m4a,.flac,.ogg,.opus,.aac,.aiff,.wma,.caf,.ac3,.alac,.amr,.ape,.mka,.webm,.mp4,.mov,.3gp" multiple onChange={(event) => { if (event.target.files) acceptFiles(event.target.files); }} hidden />
                <span className="upload-glyph" aria-hidden="true">↑</span>
                {sources.length ? <><strong>{sources.length === 1 ? sources[0].name : `${sources.length} files selected`}</strong><span>{formatBytes(sources.reduce((total, file) => total + file.size, 0))} · click to replace</span></> : <><strong>Drop audio here</strong><span>or choose one or many files from your device</span></>}
              </div>
              {sources.length > 1 && <div className="batch-list">{sources.map((file, index) => <div key={`${file.name}-${file.size}-${index}`}><span>{String(index + 1).padStart(2, '0')}</span><strong>{file.name}</strong><small>{formatBytes(file.size)}</small></div>)}</div>}
              {sources.length <= 1 && <><label className="field-label" htmlFor="production-title">Production title</label><input id="production-title" className="text-input" value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Episode, ceremony, interview…" /></>}
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
              <div className="section-heading"><div><h2>Cleanup &amp; mastering</h2><p>The selected starting point already chooses a sensible delivery level. Adjust only when you have a reason.</p></div><span className="live-chip">Executable</span></div>
              <div className="guided-banner"><span>✓</span><div><strong>Recommended target selected: {settings.mastering.target_integrated_lufs.toFixed(1)} LUFS</strong><p>{INTENT_COPY[intent].description} Ampersand will measure, normalize, and verify it automatically.</p></div></div>
              <div className="cleanup-grid">
                <label className="select-card"><span>Background noise</span><select value={settings.cleanup.noise_reduction} onChange={(event) => updateSettings((next) => { next.cleanup.noise_reduction = event.target.value as ProductionSettings['cleanup']['noise_reduction']; return next; })}><option value="off">Off</option><option value="light">Light · safest</option><option value="balanced">Balanced · recommended</option><option value="strong">Strong · review carefully</option></select><small>Reduces steady room, fan, and broadband noise. This is not music separation.</small></label>
                <label className="select-card"><span>Voice compression</span><select value={settings.cleanup.compression} onChange={(event) => updateSettings((next) => { next.cleanup.compression = event.target.value as ProductionSettings['cleanup']['compression']; return next; })}><option value="off">Off</option><option value="gentle">Gentle</option><option value="balanced">Balanced · recommended</option><option value="firm">Firm · voice-forward</option></select><small>Evens broad dynamics before the final measured loudness pass.</small></label>
                <label className={`toggle-card ${settings.cleanup.rumble_filter ? 'selected' : ''}`}><input type="checkbox" checked={settings.cleanup.rumble_filter} onChange={(event) => updateSettings((next) => { next.cleanup.rumble_filter = event.target.checked; return next; })} /><div><strong>Remove low rumble</strong><small>Filters handling noise and energy below typical speech fundamentals.</small></div></label>
              </div>
              <details className="advanced-controls">
                <summary>Advanced loudness controls</summary>
                <p>Use these when a publisher or broadcaster gives you a specific delivery standard.</p>
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
              </details>

              <div className="engine-boundaries">
                <article><span className="boundary-icon">◎</span><div><strong>Semantic analysis</strong><p>Waveform, loudness, speech probability, and safe routing report included.</p></div><em>On</em></article>
                <article><span className="boundary-icon">≈</span><div><strong>Adaptive Leveler</strong><p>Analyzed and reported, but not yet applied until listening approval.</p></div><em>Shadow</em></article>
                <article><span className="boundary-icon">✦</span><div><strong>Music separation &amp; dereverb</strong><p>These need qualified restoration models; the current beta does not mislabel basic filtering as either feature.</p></div><em>Next</em></article>
              </div>
            </div>
          </section>

          <section className="studio-section">
            <div className="section-number">04</div>
            <div className="section-content">
              <div className="section-heading"><div><h2>Output metadata</h2><p>The production title becomes the file title tag. Add reusable creator and series details here.</p></div><span className="live-chip">Embedded</span></div>
              <div className="metadata-grid">
                <label><span>Artist / creator</span><input className="text-input" value={settings.metadata.artist} onChange={(event) => updateSettings((next) => { next.metadata.artist = event.target.value; return next; })} placeholder="Creator or organization" /></label>
                <label><span>Album / series</span><input className="text-input" value={settings.metadata.album} onChange={(event) => updateSettings((next) => { next.metadata.album = event.target.value; return next; })} placeholder="Podcast or collection" /></label>
                <label><span>Genre</span><input className="text-input" value={settings.metadata.genre} onChange={(event) => updateSettings((next) => { next.metadata.genre = event.target.value; return next; })} placeholder="Spoken Word" /></label>
                <label><span>Date</span><input className="text-input" value={settings.metadata.date} onChange={(event) => updateSettings((next) => { next.metadata.date = event.target.value; return next; })} placeholder="2026-08-20" /></label>
                <label><span>Track number</span><input className="text-input" value={settings.metadata.track_number} onChange={(event) => updateSettings((next) => { next.metadata.track_number = event.target.value; return next; })} placeholder="12" /></label>
                <label><span>Copyright</span><input className="text-input" value={settings.metadata.copyright} onChange={(event) => updateSettings((next) => { next.metadata.copyright = event.target.value; return next; })} placeholder="© Owner" /></label>
                <label className="wide"><span>Comment</span><input className="text-input" value={settings.metadata.comment} onChange={(event) => updateSettings((next) => { next.metadata.comment = event.target.value; return next; })} placeholder="Optional delivery note" /></label>
              </div>
            </div>
          </section>

          <section className="studio-section">
            <div className="section-number">05</div>
            <div className="section-content">
              <div className="section-heading"><div><h2>Audiogram Studio</h2><p>Design a full-duration H.264 MP4 with a rich image, looping video, or color background. Every saved control is executed by the server renderer.</p></div><span className="live-chip">Render spec 1.0</span></div>
              <label className={`toggle-card hero-toggle ${settings.audiogram.enabled ? 'selected' : ''}`}><input type="checkbox" checked={settings.audiogram.enabled} onChange={(event) => updateSettings((next) => { next.audiogram.enabled = event.target.checked; return next; })} /><div><strong>Create an audiogram MP4</strong><small>Uses the mastered audio; no browser recording and no third-party renderer.</small></div></label>
              {settings.audiogram.enabled && <div className="audiogram-controls">
                <AudiogramPreview settings={settings.audiogram} media={artwork} title={title || sources[0]?.name.replace(/\.[^.]+$/, '') || ''} />
                <div className="three-up">
                  <label className="select-card"><span>Canvas</span><select value={settings.audiogram.aspect_ratio} onChange={(event) => updateSettings((next) => { next.audiogram.aspect_ratio = event.target.value as ProductionSettings['audiogram']['aspect_ratio']; return next; })}><option value="square">Square · 1:1 · 1080×1080</option><option value="feed_portrait">Feed portrait · 4:5 · 1080×1350</option><option value="portrait">Story / reel · 9:16 · 1080×1920</option><option value="landscape">Landscape · 16:9 · 1920×1080</option></select></label>
                  <label className="select-card"><span>Waveform style</span><select value={settings.audiogram.waveform_style} onChange={(event) => updateSettings((next) => { next.audiogram.waveform_style = event.target.value as ProductionSettings['audiogram']['waveform_style']; return next; })}><option value="line">Flowing line</option><option value="mirrored">Mirrored center</option><option value="bars">Audio bars</option><option value="dots">Particle dots</option></select></label>
                  <label className="select-card"><span>Background</span><select value={settings.audiogram.background_mode} onChange={(event) => { setArtwork(null); updateSettings((next) => { next.audiogram.background_mode = event.target.value as ProductionSettings['audiogram']['background_mode']; return next; }); }}><option value="color">Solid color</option><option value="artwork">Image artwork</option><option value="video">Looping video</option></select></label>
                </div>
                {settings.audiogram.background_mode !== 'color' && <div className="artwork-picker"><input ref={artworkInputRef} type="file" accept={settings.audiogram.background_mode === 'video' ? 'video/mp4,video/quicktime,video/webm,.m4v' : 'image/jpeg,image/png,image/webp'} hidden onChange={(event) => setArtwork(event.target.files?.[0] || null)} /><button className="button button-secondary" onClick={() => artworkInputRef.current?.click()}>{artwork ? 'Replace background' : `Choose background ${settings.audiogram.background_mode === 'video' ? 'video' : 'image'}`}</button><span>{artwork ? `${artwork.name} · ${formatBytes(artwork.size)}` : `${settings.audiogram.background_mode === 'video' ? 'MP4, MOV, M4V, or WebM' : 'JPG, PNG, or WebP'} · up to ${formatBytes(capabilities?.maxArtworkBytes || 512 * 1024 * 1024)}`}</span></div>}
                <div className="color-row"><label><span>Background</span><input type="color" value={settings.audiogram.background_color} onChange={(event) => updateSettings((next) => { next.audiogram.background_color = event.target.value; return next; })} /></label><label><span>Waveform</span><input type="color" value={settings.audiogram.waveform_color} onChange={(event) => updateSettings((next) => { next.audiogram.waveform_color = event.target.value; return next; })} /></label><label><span>Text</span><input type="color" value={settings.audiogram.text_color} onChange={(event) => updateSettings((next) => { next.audiogram.text_color = event.target.value; return next; })} /></label></div>
                <div className="metadata-grid"><label><span>Headline override</span><input className="text-input" value={settings.audiogram.headline} onChange={(event) => updateSettings((next) => { next.audiogram.headline = event.target.value; return next; })} placeholder="Uses production title when blank" /></label><label><span>Subtitle</span><input className="text-input" value={settings.audiogram.subtitle} onChange={(event) => updateSettings((next) => { next.audiogram.subtitle = event.target.value; return next; })} placeholder="Show, speaker, or call to action" /></label></div>
                <details className="advanced-controls audiogram-advanced" open>
                  <summary>Waveform, layout &amp; render controls</summary>
                  <div className="three-up compact-selects">
                    <label className="select-card"><span>Amplitude response</span><select value={settings.audiogram.waveform_scale} onChange={(event) => updateSettings((next) => { next.audiogram.waveform_scale = event.target.value as ProductionSettings['audiogram']['waveform_scale']; return next; })}><option value="linear">Linear · literal</option><option value="sqrt">Square root · balanced</option><option value="cbrt">Cube root · fuller</option><option value="log">Logarithmic · energetic</option></select></label>
                    <label className="select-card"><span>Waveform position</span><select value={settings.audiogram.waveform_position} onChange={(event) => updateSettings((next) => { next.audiogram.waveform_position = event.target.value as ProductionSettings['audiogram']['waveform_position']; return next; })}><option value="top">Upper</option><option value="center">Center</option><option value="bottom">Lower</option></select></label>
                    <label className="select-card"><span>Text alignment</span><select value={settings.audiogram.text_align} onChange={(event) => updateSettings((next) => { next.audiogram.text_align = event.target.value as ProductionSettings['audiogram']['text_align']; return next; })}><option value="left">Left</option><option value="center">Center</option><option value="right">Right</option></select></label>
                    <label className="select-card"><span>Background fit</span><select value={settings.audiogram.background_fit} onChange={(event) => updateSettings((next) => { next.audiogram.background_fit = event.target.value as ProductionSettings['audiogram']['background_fit']; return next; })}><option value="cover">Cover · fill canvas</option><option value="contain">Contain · show all</option></select></label>
                    <label className="select-card"><span>Frame rate</span><select value={settings.audiogram.frame_rate} onChange={(event) => updateSettings((next) => { next.audiogram.frame_rate = Number(event.target.value) as 24 | 30 | 60; return next; })}><option value="24">24 fps · cinematic</option><option value="30">30 fps · standard</option><option value="60">60 fps · smooth / large</option></select></label>
                    <label className="select-card"><span>Render quality</span><select value={settings.audiogram.render_quality} onChange={(event) => updateSettings((next) => { next.audiogram.render_quality = event.target.value as ProductionSettings['audiogram']['render_quality']; return next; })}><option value="draft">Draft · quick review</option><option value="standard">Standard · recommended</option><option value="high">High · slower / larger</option></select></label>
                  </div>
                  <div className="control-stack">
                    <label className="range-control"><span><strong>Waveform width</strong><small>Percentage of canvas width</small></span><input type="range" min="40" max="100" step="1" value={settings.audiogram.waveform_width_percent} onChange={(event) => updateSettings((next) => { next.audiogram.waveform_width_percent = Number(event.target.value); return next; })} /><output>{settings.audiogram.waveform_width_percent}%</output></label>
                    <label className="range-control"><span><strong>Waveform height</strong><small>Percentage of canvas height</small></span><input type="range" min="10" max="60" step="1" value={settings.audiogram.waveform_height_percent} onChange={(event) => updateSettings((next) => { next.audiogram.waveform_height_percent = Number(event.target.value); return next; })} /><output>{settings.audiogram.waveform_height_percent}%</output></label>
                    <label className="range-control"><span><strong>Waveform opacity</strong><small>Blend the animation with artwork</small></span><input type="range" min="0.1" max="1" step="0.05" value={settings.audiogram.waveform_opacity} onChange={(event) => updateSettings((next) => { next.audiogram.waveform_opacity = Number(event.target.value); return next; })} /><output>{Math.round(settings.audiogram.waveform_opacity * 100)}%</output></label>
                    <label className="range-control"><span><strong>Background dim</strong><small>Improves waveform and text contrast</small></span><input type="range" min="0" max="0.85" step="0.05" value={settings.audiogram.background_dim} onChange={(event) => updateSettings((next) => { next.audiogram.background_dim = Number(event.target.value); return next; })} /><output>{Math.round(settings.audiogram.background_dim * 100)}%</output></label>
                    <label className="range-control"><span><strong>Headline size</strong><small>Percentage of canvas width</small></span><input type="range" min="2" max="10" step="0.1" value={settings.audiogram.headline_size_percent} onChange={(event) => updateSettings((next) => { next.audiogram.headline_size_percent = Number(event.target.value); return next; })} /><output>{settings.audiogram.headline_size_percent.toFixed(1)}%</output></label>
                    <label className="range-control"><span><strong>Subtitle size</strong><small>Percentage of canvas width</small></span><input type="range" min="1" max="6" step="0.1" value={settings.audiogram.subtitle_size_percent} onChange={(event) => updateSettings((next) => { next.audiogram.subtitle_size_percent = Number(event.target.value); return next; })} /><output>{settings.audiogram.subtitle_size_percent.toFixed(1)}%</output></label>
                  </div>
                </details>
              </div>}
            </div>
          </section>

          <section className="studio-section">
            <div className="section-number">06</div>
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
            <h2>{sources.length > 1 ? `${sources.length}-file batch` : title || sources[0]?.name.replace(/\.[^.]+$/, '') || 'Untitled production'}</h2>
            <dl className="summary-list">
              <div><dt>Starting point</dt><dd>{selected.name}{dirty ? ' · modified' : ` · v${selected.version}`}</dd></div>
              <div><dt>Cleanup</dt><dd>{settings.cleanup.noise_reduction} noise · {settings.cleanup.compression} compression</dd></div>
              <div><dt>Loudness</dt><dd>{settings.mastering.target_integrated_lufs.toFixed(1)} LUFS</dd></div>
              <div><dt>Peak ceiling</dt><dd>{settings.mastering.max_true_peak_dbtp.toFixed(1)} dBTP</dd></div>
              <div><dt>Outputs</dt><dd>{[settings.export.wav && 'WAV', settings.export.mp3 && 'MP3', settings.audiogram.enabled && 'MP4'].filter(Boolean).join(' + ')}</dd></div>
            </dl>
            <div className="privacy-note"><span>⌾</span><p><strong>Private by design</strong> No hosted audio processor, no external processing API, no training use.</p></div>
            {error && <p className="form-error" role="alert">{error}</p>}
            {busy && <div className="upload-progress"><span style={{ width: `${uploadProgress}%` }} /><small>{uploadPhase || 'Preparing uploads'}</small></div>}
            <button className="button button-primary button-block" onClick={submit} disabled={busy || !sources.length || !capabilities}>{busy ? `Uploading ${Math.round(uploadProgress)}%` : sources.length > 1 ? `Queue ${sources.length} productions` : 'Create master'}</button>
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

          {production.outputs.audiogram && <section className="audiogram-result"><div><p className="eyebrow">Audiogram preview</p><h2>Ready for video delivery.</h2><p>{production.settings.audiogram.aspect_ratio} · {production.settings.audiogram.waveform_style} waveform</p></div><video src={production.outputs.audiogram} controls preload="metadata" /></section>}

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
                {production.outputs.audiogram && <a href={production.outputs.audiogram} download><span>MP4</span><div><strong>Audiogram video</strong><small>H.264 video with mastered audio</small></div><b>↓</b></a>}
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
  const hasActiveProductions = productions.some((production) => ['queued', 'running'].includes(production.status));

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
  useEffect(() => {
    if (view !== 'library' || !hasActiveProductions) return;
    const timer = window.setInterval(() => {
      listProductions().then(setProductions).catch(() => {});
    }, 2000);
    return () => window.clearInterval(timer);
  }, [view, hasActiveProductions]);

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
      {view === 'new' && <NewProductionView onCancel={() => setView('library')} onCreated={(created) => { setProductions((items) => [...created, ...items.filter((item) => !created.some((production) => production.id === item.id))]); if (created.length === 1) openProduction(created[0].id); else setView('library'); }} />}
      {view === 'production' && current && <ProductionView production={current} onBack={() => setView('library')} onDelete={() => void removeProduction(current.id)} onRetry={() => { retryProduction(current.id).then((updated) => setProductions((items) => [updated, ...items.filter((item) => item.id !== updated.id)])).catch((caught) => setGlobalError(caught.message)); }} />}
      {view === 'production' && !current && <LibraryView productions={productions} onOpen={openProduction} onNew={() => setView('new')} onDelete={(id) => void removeProduction(id)} />}
      <footer><span>Ampersand beta · deterministic mastering</span><span>Independent engine · no external API cost</span></footer>
    </div>
  );
}
