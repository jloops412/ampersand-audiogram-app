import type {
  ProductionIntent,
  ProductionSettings,
  SelectableTemplate,
  TemplateVersion,
  UserTemplate,
} from './types';

const STORAGE_KEY = 'ampersand-beta-templates-v1';
const INTENTS = new Set<ProductionIntent>(['podcast', 'natural_voice', 'broadcast', 'social_voice']);
const BITRATES = new Set([128, 160, 192, 256, 320]);
const OPAQUE_ID = /^[a-z0-9][a-z0-9._:-]{1,127}$/;

function isSettings(value: unknown): value is ProductionSettings {
  if (!value || typeof value !== 'object') return false;
  const candidate = value as Partial<ProductionSettings>;
  const cleanup = candidate.cleanup;
  const mastering = candidate.mastering;
  const metadata = candidate.metadata;
  const audiogram = candidate.audiogram;
  const delivery = candidate.export;
  return Boolean(
    cleanup &&
      ['smart', 'manual'].includes(cleanup.mode) &&
      ['off', 'light', 'balanced', 'strong'].includes(cleanup.noise_reduction) &&
      typeof cleanup.rumble_filter === 'boolean' &&
      ['off', '50hz', '60hz'].includes(cleanup.hum_reduction) &&
      typeof cleanup.declip === 'boolean' &&
      ['off', 'light', 'balanced'].includes(cleanup.noise_gate) &&
      ['off', 'light', 'balanced', 'strong'].includes(cleanup.deesser) &&
      ['off', 'natural', 'warm', 'presence'].includes(cleanup.voice_enhancement) &&
      ['off', 'gentle', 'balanced', 'firm'].includes(cleanup.compression) &&
    mastering &&
      delivery &&
      Number.isFinite(mastering.target_integrated_lufs) &&
      mastering.target_integrated_lufs >= -24 &&
      mastering.target_integrated_lufs <= -14 &&
      Number.isFinite(mastering.max_true_peak_dbtp) &&
      mastering.max_true_peak_dbtp >= -3 &&
      mastering.max_true_peak_dbtp <= -1 &&
      Number.isFinite(mastering.target_loudness_range_lu) &&
      mastering.target_loudness_range_lu >= 5 &&
      mastering.target_loudness_range_lu <= 30 &&
      metadata &&
      Object.values(metadata).every((item) => typeof item === 'string') &&
      audiogram &&
      ['1.0', '1.1'].includes(audiogram.spec_version) &&
      typeof audiogram.enabled === 'boolean' &&
      ['square', 'feed_portrait', 'portrait', 'landscape'].includes(audiogram.aspect_ratio) &&
      ['line', 'mirrored', 'bars', 'dots', 'spectrum', 'spectrum_dots'].includes(audiogram.waveform_style) &&
      ['linear', 'sqrt', 'cbrt', 'log'].includes(audiogram.waveform_scale) &&
      ['top', 'center', 'bottom'].includes(audiogram.waveform_position) &&
      audiogram.waveform_width_percent >= 40 && audiogram.waveform_width_percent <= 100 &&
      audiogram.waveform_height_percent >= 10 && audiogram.waveform_height_percent <= 60 &&
      audiogram.waveform_opacity >= 0.1 && audiogram.waveform_opacity <= 1 &&
      audiogram.waveform_glow >= 0 && audiogram.waveform_glow <= 1 &&
      ['none', 'glass', 'outline', 'accent'].includes(audiogram.waveform_frame) &&
      ['color', 'gradient', 'radial', 'artwork', 'video'].includes(audiogram.background_mode) &&
      ['cover', 'contain'].includes(audiogram.background_fit) &&
      audiogram.background_dim >= 0 && audiogram.background_dim <= 0.85 &&
      audiogram.background_blur >= 0 && audiogram.background_blur <= 30 &&
      audiogram.background_vignette >= 0 && audiogram.background_vignette <= 1 &&
      [audiogram.background_color, audiogram.accent_color, audiogram.waveform_color, audiogram.text_color].every((color) =>
        /^#[0-9a-f]{6}$/i.test(color),
      ) &&
      ['sans', 'serif', 'mono'].includes(audiogram.font_family) &&
      ['left', 'center', 'right'].includes(audiogram.text_align) &&
      ['top', 'center', 'bottom'].includes(audiogram.text_position) &&
      ['none', 'shadow', 'glass', 'accent'].includes(audiogram.text_panel) &&
      audiogram.headline_size_percent >= 2 && audiogram.headline_size_percent <= 10 &&
      audiogram.subtitle_size_percent >= 1 && audiogram.subtitle_size_percent <= 6 &&
      [24, 30, 60].includes(audiogram.frame_rate) &&
      ['draft', 'standard', 'high'].includes(audiogram.render_quality) &&
      typeof delivery.wav === 'boolean' &&
      typeof delivery.mp3 === 'boolean' &&
      (delivery.wav || delivery.mp3) &&
      BITRATES.has(delivery.mp3_bitrate_kbps),
  );
}

function isUserTemplate(value: unknown): value is UserTemplate {
  if (!value || typeof value !== 'object') return false;
  const candidate = value as Partial<UserTemplate>;
  if (
    typeof candidate.templateId !== 'string' ||
    !OPAQUE_ID.test(candidate.templateId) ||
    typeof candidate.name !== 'string' ||
    candidate.name.trim().length === 0 ||
    candidate.name.length > 120 ||
    !Array.isArray(candidate.versions) ||
    candidate.versions.length === 0
  ) return false;
  return candidate.versions.every((version) =>
    Boolean(
      version &&
        OPAQUE_ID.test(version.templateVersionId) &&
        Number.isInteger(version.version) &&
        version.version >= 1 &&
        typeof version.createdAt === 'string' &&
        INTENTS.has(version.intent) &&
        isSettings(version.settings),
    ),
  );
}

function settings(
  target: number,
  peak: number,
  range: number,
  mp3Bitrate: 128 | 160 | 192 | 256 | 320 = 192,
  cleanup: Partial<ProductionSettings['cleanup']> = {},
): ProductionSettings {
  const resolvedCleanup: ProductionSettings['cleanup'] = {
    mode: 'smart',
    noise_reduction: 'off',
    rumble_filter: false,
    hum_reduction: 'off',
    declip: false,
    noise_gate: 'off',
    deesser: 'off',
    voice_enhancement: 'off',
    compression: 'off',
    ...cleanup,
  };
  return {
    cleanup: resolvedCleanup,
    mastering: {
      target_integrated_lufs: target,
      max_true_peak_dbtp: peak,
      target_loudness_range_lu: range,
    },
    metadata: {
      artist: '',
      album: '',
      genre: 'Spoken Word',
      date: '',
      comment: '',
      copyright: '',
      track_number: '',
    },
    audiogram: {
      spec_version: '1.1',
      enabled: false,
      aspect_ratio: 'square',
      waveform_style: 'mirrored',
      waveform_scale: 'sqrt',
      waveform_position: 'center',
      waveform_width_percent: 84,
      waveform_height_percent: 30,
      waveform_opacity: 1,
      waveform_glow: 0.58,
      waveform_frame: 'glass',
      background_mode: 'gradient',
      background_fit: 'cover',
      background_dim: 0.08,
      background_blur: 0,
      background_vignette: 0.45,
      background_color: '#111718',
      accent_color: '#e1b977',
      waveform_color: '#f3cc8a',
      text_color: '#f8f4ec',
      font_family: 'sans',
      text_align: 'center',
      text_position: 'top',
      text_panel: 'shadow',
      headline_size_percent: 4.8,
      subtitle_size_percent: 2.7,
      headline: '',
      subtitle: '',
      frame_rate: 30,
      render_quality: 'standard',
    },
    export: { wav: true, mp3: true, mp3_bitrate_kbps: mp3Bitrate },
  };
}

export const BUILT_IN_TEMPLATES: SelectableTemplate[] = [
  {
    key: 'builtin:podcast',
    templateId: 'template:builtin:podcast',
    templateVersionId: 'template-version:builtin:podcast:3',
    name: 'Podcast polish',
    version: 3,
    intent: 'podcast',
    settings: settings(-16, -1, 11),
    builtIn: true,
  },
  {
    key: 'builtin:natural-voice',
    templateId: 'template:builtin:natural-voice',
    templateVersionId: 'template-version:builtin:natural-voice:3',
    name: 'Natural voice',
    version: 3,
    intent: 'natural_voice',
    settings: settings(-18, -1.5, 14),
    builtIn: true,
  },
  {
    key: 'builtin:broadcast',
    templateId: 'template:builtin:broadcast',
    templateVersionId: 'template-version:builtin:broadcast:3',
    name: 'Broadcast delivery',
    version: 3,
    intent: 'broadcast',
    settings: settings(-23, -1, 7, 256),
    builtIn: true,
  },
  {
    key: 'builtin:social-voice',
    templateId: 'template:builtin:social-voice',
    templateVersionId: 'template-version:builtin:social-voice:3',
    name: 'Social voice',
    version: 3,
    intent: 'social_voice',
    settings: settings(-14, -1, 8),
    builtIn: true,
  },
];

export function cloneSettings(value: ProductionSettings): ProductionSettings {
  return structuredClone(value);
}

function migrateSettings(value: unknown): unknown {
  if (!value || typeof value !== 'object') return value;
  const candidate = value as Partial<ProductionSettings>;
  const fallback = settings(-16, -1, 11);
  const cleanup: Partial<ProductionSettings['cleanup']> = candidate.cleanup || {};
  return {
    cleanup: { ...fallback.cleanup, ...cleanup, mode: cleanup.mode || 'manual' },
    mastering: candidate.mastering,
    metadata: { ...fallback.metadata, ...(candidate.metadata || {}) },
    audiogram: { ...fallback.audiogram, ...(candidate.audiogram || {}), spec_version: '1.1' },
    export: candidate.export,
  };
}

export function loadUserTemplates(): UserTemplate[] {
  try {
    const value = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]') as unknown;
    if (!Array.isArray(value)) return [];
    return value
      .map((entry) => {
        if (!entry || typeof entry !== 'object') return entry;
        const candidate = entry as Partial<UserTemplate>;
        return {
          ...candidate,
          versions: Array.isArray(candidate.versions)
            ? candidate.versions.map((version) => ({ ...version, settings: migrateSettings(version?.settings) }))
            : candidate.versions,
        };
      })
      .filter(isUserTemplate)
      .map((template) => structuredClone(template));
  } catch {
    return [];
  }
}

export function saveUserTemplates(templates: UserTemplate[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(templates));
}

export function flattenUserTemplates(templates: UserTemplate[]): SelectableTemplate[] {
  return templates.flatMap((template) =>
    template.versions.map((version) => ({
      key: `${template.templateId}:${version.version}`,
      templateId: template.templateId,
      templateVersionId: version.templateVersionId,
      name: template.name,
      version: version.version,
      intent: version.intent,
      settings: version.settings,
      builtIn: false,
    })),
  );
}

export function createOrVersionTemplate(
  templates: UserTemplate[],
  name: string,
  intent: ProductionIntent,
  selectedTemplateId: string | null,
  value: ProductionSettings,
): { templates: UserTemplate[]; selected: SelectableTemplate } {
  const existingIndex = templates.findIndex((template) => template.templateId === selectedTemplateId);
  const templateId = existingIndex >= 0 ? templates[existingIndex].templateId : `template:local:${crypto.randomUUID()}`;
  const existing = existingIndex >= 0 ? templates[existingIndex] : null;
  const version = (existing?.versions.at(-1)?.version || 0) + 1;
  const templateVersion: TemplateVersion = {
    templateVersionId: `template-version:local:${crypto.randomUUID()}:${version}`,
    version,
    createdAt: new Date().toISOString(),
    intent,
    settings: cloneSettings(value),
  };
  const nextTemplate: UserTemplate = {
    templateId,
    name: name.trim().slice(0, 120),
    versions: [...(existing?.versions || []), templateVersion],
  };
  const next = [...templates];
  if (existingIndex >= 0) next[existingIndex] = nextTemplate;
  else next.push(nextTemplate);
  return {
    templates: next,
    selected: {
      key: `${templateId}:${version}`,
      templateId,
      templateVersionId: templateVersion.templateVersionId,
      name: nextTemplate.name,
      version,
      intent,
      settings: templateVersion.settings,
      builtIn: false,
    },
  };
}
