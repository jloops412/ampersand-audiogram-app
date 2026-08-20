export type ProductionIntent = 'podcast' | 'natural_voice' | 'broadcast' | 'social_voice';
export type ProductionStatus = 'queued' | 'running' | 'succeeded' | 'failed' | 'interrupted';

export interface MasteringSettings {
  target_integrated_lufs: number;
  max_true_peak_dbtp: number;
  target_loudness_range_lu: number;
}

export interface ExportSettings {
  wav: boolean;
  mp3: boolean;
  mp3_bitrate_kbps: 128 | 160 | 192 | 256 | 320;
}

export interface ProductionSettings {
  mastering: MasteringSettings;
  export: ExportSettings;
}

export interface LoudnessMeasurement {
  integrated_lufs: number;
  true_peak_dbtp: number;
  loudness_range_lu: number;
}

export interface ProductionSummary {
  durationUs: number;
  channels: number;
  sampleRateHz: number;
  formatName: string;
  loudnessBefore: LoudnessMeasurement;
  loudnessAfter: LoudnessMeasurement;
  resolvedSettingsId: string;
  resolvedSettingsSha256: string;
  decisions: string[];
  warnings: string[];
  artifacts: Array<{ kind: string; sizeBytes: number; mimeType: string }>;
  externalApiCostUsd: number;
}

export interface Production {
  id: string;
  requestId: string;
  title: string;
  status: ProductionStatus;
  intent: ProductionIntent;
  templateVersionId: string | null;
  settings: ProductionSettings;
  source: { filename: string; sizeBytes: number };
  createdAt: string;
  updatedAt: string;
  startedAt: string | null;
  completedAt: string | null;
  currentStep: string;
  completedSteps: string[];
  progressPercent: number;
  attempt: number;
  error: { code: string; message: string } | null;
  summary: ProductionSummary | null;
  outputs: {
    original: string;
    wav: string | null;
    mp3: string | null;
    report: string;
    waveform: string;
  } | null;
}

export interface WaveformPeaks {
  duration_us: number;
  channels: number;
  levels: Array<{
    samples_per_window: number;
    windows: Array<Array<[number, number]>>;
  }>;
}

export interface TemplateVersion {
  templateVersionId: string;
  version: number;
  createdAt: string;
  intent: ProductionIntent;
  settings: ProductionSettings;
}

export interface UserTemplate {
  templateId: string;
  name: string;
  versions: TemplateVersion[];
}

export interface SelectableTemplate {
  key: string;
  templateId: string;
  templateVersionId: string;
  name: string;
  version: number;
  intent: ProductionIntent;
  settings: ProductionSettings;
  builtIn: boolean;
}
