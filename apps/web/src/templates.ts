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
      ['off', 'light', 'balanced', 'strong'].includes(cleanup.noise_reduction) &&
      typeof cleanup.rumble_filter === 'boolean' &&
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
      typeof audiogram.enabled === 'boolean' &&
      ['square', 'portrait', 'landscape'].includes(audiogram.aspect_ratio) &&
      ['line', 'mirrored', 'bars'].includes(audiogram.waveform_style) &&
      ['color', 'artwork'].includes(audiogram.background_mode) &&
      [audiogram.background_color, audiogram.waveform_color, audiogram.text_color].every((color) =>
        /^#[0-9a-f]{6}$/i.test(color),
      ) &&
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
  cleanup: ProductionSettings['cleanup'] = {
    noise_reduction: 'balanced',
    rumble_filter: true,
    compression: 'balanced',
  },
): ProductionSettings {
  return {
    cleanup,
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
      enabled: false,
      aspect_ratio: 'square',
      waveform_style: 'mirrored',
      background_mode: 'color',
      background_color: '#111718',
      waveform_color: '#e1b977',
      text_color: '#f4f1ea',
      headline: '',
      subtitle: '',
    },
    export: { wav: true, mp3: true, mp3_bitrate_kbps: mp3Bitrate },
  };
}

export const BUILT_IN_TEMPLATES: SelectableTemplate[] = [
  {
    key: 'builtin:podcast',
    templateId: 'template:builtin:podcast',
    templateVersionId: 'template-version:builtin:podcast:1',
    name: 'Podcast polish',
    version: 1,
    intent: 'podcast',
    settings: settings(-16, -1, 11, 192),
    builtIn: true,
  },
  {
    key: 'builtin:natural-voice',
    templateId: 'template:builtin:natural-voice',
    templateVersionId: 'template-version:builtin:natural-voice:1',
    name: 'Natural voice',
    version: 1,
    intent: 'natural_voice',
    settings: settings(-18, -1.5, 14, 192, {
      noise_reduction: 'light',
      rumble_filter: true,
      compression: 'gentle',
    }),
    builtIn: true,
  },
  {
    key: 'builtin:broadcast',
    templateId: 'template:builtin:broadcast',
    templateVersionId: 'template-version:builtin:broadcast:1',
    name: 'Broadcast delivery',
    version: 1,
    intent: 'broadcast',
    settings: settings(-23, -1, 7, 256, {
      noise_reduction: 'balanced',
      rumble_filter: true,
      compression: 'firm',
    }),
    builtIn: true,
  },
  {
    key: 'builtin:social-voice',
    templateId: 'template:builtin:social-voice',
    templateVersionId: 'template-version:builtin:social-voice:1',
    name: 'Social voice',
    version: 1,
    intent: 'social_voice',
    settings: settings(-14, -1, 8, 192, {
      noise_reduction: 'balanced',
      rumble_filter: true,
      compression: 'firm',
    }),
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
  return {
    cleanup: candidate.cleanup || fallback.cleanup,
    mastering: candidate.mastering,
    metadata: { ...fallback.metadata, ...(candidate.metadata || {}) },
    audiogram: { ...fallback.audiogram, ...(candidate.audiogram || {}) },
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
