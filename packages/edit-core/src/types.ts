export const EDL_SCHEMA_VERSION = "1.0.0" as const;
export const EDL_KIND = "ampersand.edl" as const;
export const EDIT_COMMAND_SCHEMA_VERSION = "1.0.0" as const;
export const EDIT_COMMAND_KIND = "ampersand.edit-command.add-cuts" as const;
export const AUDIO_RENDER_PLAN_SCHEMA_VERSION = "1.0.0" as const;
export const AUDIO_RENDER_PLAN_KIND = "ampersand.audio-render-plan" as const;

declare const microsecondsBrand: unique symbol;

export type Microseconds = number & { readonly [microsecondsBrand]: true };

export interface TimeRange {
  readonly startUs: Microseconds;
  readonly endUs: Microseconds;
}

export interface SourceIdentity {
  readonly assetId: string;
  readonly durationUs: Microseconds;
}

export interface EditDecisionListV1 {
  readonly schemaVersion: typeof EDL_SCHEMA_VERSION;
  readonly kind: typeof EDL_KIND;
  readonly timebase: "microseconds";
  readonly intervalSemantics: "half-open";
  readonly source: SourceIdentity;
  readonly cuts: readonly TimeRange[];
}

export interface RangeCommandOrigin {
  readonly type: "range";
}

export interface TranscriptWordsCommandOrigin {
  readonly type: "transcript_words";
  readonly transcriptId: string;
  readonly wordIds: readonly string[];
}

export interface AddCutsCommandV1 {
  readonly schemaVersion: typeof EDIT_COMMAND_SCHEMA_VERSION;
  readonly kind: typeof EDIT_COMMAND_KIND;
  readonly commandId: string;
  readonly source: SourceIdentity;
  readonly cuts: readonly TimeRange[];
  readonly origin: RangeCommandOrigin | TranscriptWordsCommandOrigin;
}

export type EditCommandV1 = AddCutsCommandV1;

export interface RawTranscriptWord {
  readonly id: string;
  readonly text: string;
  readonly startUs: Microseconds;
  readonly endUs: Microseconds;
  readonly speakerId?: string;
}

export interface RawTranscript {
  readonly transcriptId: string;
  readonly source: SourceIdentity;
  readonly words: readonly RawTranscriptWord[];
}

export interface OutputRange {
  readonly startUs: Microseconds;
  readonly endUs: Microseconds;
}

export interface MappedTranscriptSegment {
  readonly source: TimeRange;
  readonly output: OutputRange;
}

export interface MappedTranscriptWord {
  readonly wordId: string;
  readonly disposition: "kept" | "partial" | "removed";
  readonly segments: readonly MappedTranscriptSegment[];
}

export interface SourcePointMapping {
  readonly sourceUs: Microseconds;
  readonly outputUs: Microseconds;
  readonly disposition: "kept" | "removed";
}

export type SeamBias = "left" | "right";

export interface RenderSegment {
  readonly source: TimeRange;
  readonly output: OutputRange;
}

export interface AudioRenderPlanV1 {
  readonly schemaVersion: typeof AUDIO_RENDER_PLAN_SCHEMA_VERSION;
  readonly kind: typeof AUDIO_RENDER_PLAN_KIND;
  readonly source: SourceIdentity;
  readonly outputDurationUs: Microseconds;
  readonly segments: readonly RenderSegment[];
  readonly filterComplex: string;
  readonly outputLabel: "[ampersand_audio_out]";
}

export interface EditSession {
  readonly baseEdl: EditDecisionListV1;
  readonly appliedCommands: readonly EditCommandV1[];
  readonly redoCommands: readonly EditCommandV1[];
  readonly edl: EditDecisionListV1;
}
