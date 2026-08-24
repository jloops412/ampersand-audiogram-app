export type ProductionIntent = 'podcast' | 'natural_voice' | 'broadcast' | 'social_voice';
export type ProductionStatus = 'queued' | 'running' | 'succeeded' | 'failed' | 'interrupted';

export interface MasteringSettings {
  target_integrated_lufs: number;
  max_true_peak_dbtp: number;
  target_loudness_range_lu: number;
}

export interface CleanupSettings {
  mode: 'smart' | 'manual';
  noise_reduction: 'off' | 'light' | 'balanced' | 'strong';
  rumble_filter: boolean;
  hum_reduction: 'off' | '50hz' | '60hz';
  declip: boolean;
  noise_gate: 'off' | 'light' | 'balanced';
  deesser: 'off' | 'light' | 'balanced' | 'strong';
  voice_enhancement: 'off' | 'natural' | 'warm' | 'presence';
  compression: 'off' | 'gentle' | 'balanced' | 'firm';
}

export interface OutputMetadataSettings {
  artist: string;
  album: string;
  genre: string;
  date: string;
  comment: string;
  copyright: string;
  track_number: string;
}

export interface AudiogramSettings {
  spec_version: '1.0';
  enabled: boolean;
  aspect_ratio: 'square' | 'feed_portrait' | 'portrait' | 'landscape';
  waveform_style: 'line' | 'mirrored' | 'bars' | 'dots';
  waveform_scale: 'linear' | 'sqrt' | 'cbrt' | 'log';
  waveform_position: 'top' | 'center' | 'bottom';
  waveform_width_percent: number;
  waveform_height_percent: number;
  waveform_opacity: number;
  background_mode: 'color' | 'artwork' | 'video';
  background_fit: 'cover' | 'contain';
  background_dim: number;
  background_color: string;
  waveform_color: string;
  text_color: string;
  text_align: 'left' | 'center' | 'right';
  headline_size_percent: number;
  subtitle_size_percent: number;
  headline: string;
  subtitle: string;
  frame_rate: 24 | 30 | 60;
  render_quality: 'draft' | 'standard' | 'high';
}

export interface ExportSettings {
  wav: boolean;
  mp3: boolean;
  mp3_bitrate_kbps: 128 | 160 | 192 | 256 | 320;
}

export interface ProductionSettings {
  cleanup: CleanupSettings;
  mastering: MasteringSettings;
  metadata: OutputMetadataSettings;
  audiogram: AudiogramSettings;
  export: ExportSettings;
}

export interface Capabilities {
  apiVersion: string;
  maxUploadBytes: number;
  maxArtworkBytes: number;
  directUpload: { enabled: boolean; maxBytes: number; chunkBytes: number };
  batch: { enabled: boolean; processingConcurrency: number };
  betaLimitations: string[];
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
  cleanupPlan: {
    id: string;
    sha256: string;
    mode: 'smart' | 'manual';
    decision: 'candidate' | 'manual' | 'protect' | 'no_op';
    productionAudioChanged: boolean;
    candidateStages: string[];
    appliedStages: string[];
    evidence: {
      musicEvidenceAvailable: boolean;
      stationaryNoiseEvidenceAvailable: boolean;
      protectedRegionCount: number;
      conflictCount: number;
      maximumMusicProbability: number | null;
      maximumNoiseProbability: number | null;
      maximumRumbleProbability: number | null;
      maximumHumProbability: number | null;
      maximumClippingProbability: number | null;
      resolvedHumFundamentalHz: 50 | 60 | null;
    };
    thresholds: {
      maximumMusicProbability: number;
      minimumNoiseProbability: number;
      minimumRumbleProbability: number;
      minimumHumProbability: number;
    };
  };
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
    audiogram: string | null;
    report: string;
    cleanupPlan: string | null;
    waveform: string;
  } | null;
}

export interface WaveformPeaks {
  schema_version: '1.0.0';
  waveform_id: string;
  source_asset_id: string;
  sample_rate_hz: number;
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
