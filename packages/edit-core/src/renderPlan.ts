import { deriveKeptRanges, outputDurationUs } from "./edl.js";
import { formatFfmpegSeconds, microseconds, rangeLength, timeRange } from "./time.js";
import {
  AUDIO_RENDER_PLAN_KIND,
  AUDIO_RENDER_PLAN_SCHEMA_VERSION,
  type AudioRenderPlanV1,
  type EditDecisionListV1,
  type RenderSegment,
} from "./types.js";

const OUTPUT_LABEL = "[ampersand_audio_out]" as const;

function renderSegments(edl: EditDecisionListV1): readonly RenderSegment[] {
  let outputCursor = microseconds(0);
  return deriveKeptRanges(edl).map((source) => {
    const outputEnd = microseconds(outputCursor + rangeLength(source), "segment output end");
    const segment = { source, output: timeRange(outputCursor, outputEnd, "segment output") };
    outputCursor = outputEnd;
    return segment;
  });
}

function trimFilter(startUs: number, endUs: number, outputLabel: string): string {
  return `[0:a]atrim=start=${formatFfmpegSeconds(startUs)}:end=${formatFfmpegSeconds(endUs)},asetpts=PTS-STARTPTS${outputLabel}`;
}

export function buildAudioRenderPlan(edl: EditDecisionListV1): AudioRenderPlanV1 {
  const segments = renderSegments(edl);
  let filterComplex: string;
  if (segments.length === 0) {
    filterComplex = trimFilter(0, 0, OUTPUT_LABEL);
  } else if (segments.length === 1) {
    filterComplex = trimFilter(segments[0]!.source.startUs, segments[0]!.source.endUs, OUTPUT_LABEL);
  } else {
    const trims = segments.map((segment, index) =>
      trimFilter(segment.source.startUs, segment.source.endUs, `[ampersand_a${index}]`));
    const inputs = segments.map((_, index) => `[ampersand_a${index}]`).join("");
    filterComplex = `${trims.join(";")};${inputs}concat=n=${segments.length}:v=0:a=1${OUTPUT_LABEL}`;
  }
  return {
    schemaVersion: AUDIO_RENDER_PLAN_SCHEMA_VERSION,
    kind: AUDIO_RENDER_PLAN_KIND,
    source: edl.source,
    outputDurationUs: outputDurationUs(edl),
    segments,
    filterComplex,
    outputLabel: OUTPUT_LABEL,
  };
}

export function ffmpegAudioFilterArgs(plan: AudioRenderPlanV1): readonly string[] {
  return ["-filter_complex", plan.filterComplex, "-map", plan.outputLabel];
}
