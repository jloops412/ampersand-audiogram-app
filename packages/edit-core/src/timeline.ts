import { deriveKeptRanges, outputDurationUs } from "./edl.js";
import { microseconds, rangeLength, timeRange } from "./time.js";
import type {
  EditDecisionListV1,
  MappedTranscriptSegment,
  Microseconds,
  SeamBias,
  SourcePointMapping,
  TimeRange,
} from "./types.js";

function sourcePosition(value: number, edl: EditDecisionListV1): Microseconds {
  const position = microseconds(value, "source position");
  if (position > edl.source.durationUs) throw new RangeError("source position exceeds source duration");
  return position;
}

function outputPosition(value: number, edl: EditDecisionListV1): Microseconds {
  const position = microseconds(value, "output position");
  if (position > outputDurationUs(edl)) throw new RangeError("output position exceeds output duration");
  return position;
}

export function sourceToOutput(edl: EditDecisionListV1, sourceUs: number): SourcePointMapping {
  const source = sourcePosition(sourceUs, edl);
  let removedBefore = 0;
  for (const cut of edl.cuts) {
    if (source < cut.startUs) break;
    if (source < cut.endUs) {
      return {
        sourceUs: source,
        outputUs: microseconds(cut.startUs - removedBefore, "output position"),
        disposition: "removed",
      };
    }
    removedBefore += rangeLength(cut);
  }
  return {
    sourceUs: source,
    outputUs: microseconds(source - removedBefore, "output position"),
    disposition: "kept",
  };
}

export function outputToSource(
  edl: EditDecisionListV1,
  outputUs: number,
  bias: SeamBias = "right",
): Microseconds {
  const output = outputPosition(outputUs, edl);
  let removedBefore = 0;
  for (const cut of edl.cuts) {
    const seam = cut.startUs - removedBefore;
    if (output === seam) return bias === "left" ? cut.startUs : cut.endUs;
    if (output < seam) break;
    removedBefore += rangeLength(cut);
  }
  return microseconds(output + removedBefore, "source position");
}

function intersection(left: TimeRange, right: TimeRange): TimeRange | null {
  const startUs = Math.max(left.startUs, right.startUs);
  const endUs = Math.min(left.endUs, right.endUs);
  return endUs > startUs ? timeRange(startUs, endUs, "intersection") : null;
}

export function sourceRangeToOutput(
  edl: EditDecisionListV1,
  sourceRange: { readonly startUs: number; readonly endUs: number },
): readonly MappedTranscriptSegment[] {
  const range = timeRange(sourceRange.startUs, sourceRange.endUs, "source range");
  if (range.endUs > edl.source.durationUs) throw new RangeError("source range exceeds source duration");
  return deriveKeptRanges(edl).flatMap((kept) => {
    const live = intersection(range, kept);
    if (!live) return [];
    const start = sourceToOutput(edl, live.startUs).outputUs;
    const end = sourceToOutput(edl, live.endUs).outputUs;
    return [{ source: live, output: timeRange(start, end, "mapped output range") }];
  });
}
