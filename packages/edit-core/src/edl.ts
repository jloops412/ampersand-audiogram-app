import {
  EDL_KIND,
  EDL_SCHEMA_VERSION,
  type EditDecisionListV1,
  type Microseconds,
  type SourceIdentity,
  type TimeRange,
} from "./types.js";
import { microseconds, nonEmptyId, rangeLength, timeRange } from "./time.js";

export interface CreateEdlInput {
  readonly assetId: string;
  readonly durationUs: number;
  readonly cuts?: readonly { readonly startUs: number; readonly endUs: number }[];
}

function sourceIdentity(assetId: string, durationUs: number): SourceIdentity {
  return {
    assetId: nonEmptyId(assetId, "source.assetId"),
    durationUs: microseconds(durationUs, "source.durationUs"),
  };
}

export function normalizeCuts(
  cuts: readonly { readonly startUs: number; readonly endUs: number }[],
  durationUs: number,
): readonly TimeRange[] {
  const duration = microseconds(durationUs, "source.durationUs");
  const ordered = cuts
    .map((range, index) => {
      const normalized = timeRange(range.startUs, range.endUs, `cuts[${index}]`);
      if (normalized.endUs > duration) throw new RangeError(`cuts[${index}] exceeds source duration`);
      return normalized;
    })
    .sort((left, right) => left.startUs - right.startUs || left.endUs - right.endUs);

  const merged: TimeRange[] = [];
  for (const current of ordered) {
    const previous = merged.at(-1);
    if (!previous || current.startUs > previous.endUs) {
      merged.push(current);
    } else {
      merged[merged.length - 1] = timeRange(
        previous.startUs,
        Math.max(previous.endUs, current.endUs),
        "merged cut",
      );
    }
  }
  return merged;
}

export function createEdl(input: CreateEdlInput): EditDecisionListV1 {
  const source = sourceIdentity(input.assetId, input.durationUs);
  return {
    schemaVersion: EDL_SCHEMA_VERSION,
    kind: EDL_KIND,
    timebase: "microseconds",
    intervalSemantics: "half-open",
    source,
    cuts: normalizeCuts(input.cuts ?? [], source.durationUs),
  };
}

export function deriveKeptRanges(edl: EditDecisionListV1): readonly TimeRange[] {
  const kept: TimeRange[] = [];
  let cursor = microseconds(0);
  for (const cut of edl.cuts) {
    if (cursor < cut.startUs) kept.push(timeRange(cursor, cut.startUs, "kept range"));
    cursor = cut.endUs;
  }
  if (cursor < edl.source.durationUs) kept.push(timeRange(cursor, edl.source.durationUs, "kept range"));
  return kept;
}

export function outputDurationUs(edl: EditDecisionListV1): Microseconds {
  const removedUs = edl.cuts.reduce((total, cut) => total + rangeLength(cut), 0);
  return microseconds(edl.source.durationUs - removedUs, "output duration");
}

export function addCuts(
  edl: EditDecisionListV1,
  cuts: readonly { readonly startUs: number; readonly endUs: number }[],
): EditDecisionListV1 {
  return createEdl({ assetId: edl.source.assetId, durationUs: edl.source.durationUs, cuts: [...edl.cuts, ...cuts] });
}

function assertPlainObject(value: unknown, field: string): asserts value is Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new TypeError(`${field} must be an object`);
  }
}

function assertExactKeys(value: Record<string, unknown>, keys: readonly string[], field: string): void {
  const actual = Object.keys(value).sort();
  const expected = [...keys].sort();
  if (actual.length !== expected.length || actual.some((key, index) => key !== expected[index])) {
    throw new TypeError(`${field} contains missing or unknown fields`);
  }
}

function sameRanges(
  left: readonly { readonly startUs: number; readonly endUs: number }[],
  right: readonly TimeRange[],
): boolean {
  return left.length === right.length && left.every((range, index) =>
    range.startUs === right[index]?.startUs && range.endUs === right[index]?.endUs);
}

export function serializeEdl(edl: EditDecisionListV1): string {
  const validated = validateInternalEdl(edl);
  return JSON.stringify({
    schema_version: validated.schemaVersion,
    kind: validated.kind,
    timebase: validated.timebase,
    interval_semantics: validated.intervalSemantics,
    source: {
      asset_id: validated.source.assetId,
      duration_us: validated.source.durationUs,
    },
    cuts: validated.cuts.map((cut) => ({ start_us: cut.startUs, end_us: cut.endUs })),
  });
}

function validateInternalEdl(raw: unknown): EditDecisionListV1 {
  assertPlainObject(raw, "EDL");
  assertExactKeys(raw, ["schemaVersion", "kind", "timebase", "intervalSemantics", "source", "cuts"], "EDL");
  if (raw.schemaVersion !== EDL_SCHEMA_VERSION) {
    throw new TypeError(`unsupported EDL schemaVersion: ${String(raw.schemaVersion)}`);
  }
  if (raw.kind !== EDL_KIND || raw.timebase !== "microseconds" || raw.intervalSemantics !== "half-open") {
    throw new TypeError("EDL identity, timebase, or interval semantics are invalid");
  }
  assertPlainObject(raw.source, "EDL.source");
  assertExactKeys(raw.source, ["assetId", "durationUs"], "EDL.source");
  if (!Array.isArray(raw.cuts)) throw new TypeError("EDL.cuts must be an array");
  const parsedCuts = raw.cuts.map((value, index) => {
    assertPlainObject(value, `EDL.cuts[${index}]`);
    assertExactKeys(value, ["startUs", "endUs"], `EDL.cuts[${index}]`);
    return { startUs: value.startUs as number, endUs: value.endUs as number };
  });
  const edl = createEdl({
    assetId: raw.source.assetId as string,
    durationUs: raw.source.durationUs as number,
    cuts: parsedCuts,
  });
  if (!sameRanges(parsedCuts, edl.cuts)) {
    throw new TypeError("EDL cuts must be sorted, disjoint, and non-adjacent");
  }
  return edl;
}

function parseWireEdl(raw: unknown): EditDecisionListV1 {
  assertPlainObject(raw, "EDL");
  assertExactKeys(raw, ["schema_version", "kind", "timebase", "interval_semantics", "source", "cuts"], "EDL");
  if (raw.schema_version !== EDL_SCHEMA_VERSION) {
    throw new TypeError(`unsupported EDL schema_version: ${String(raw.schema_version)}`);
  }
  if (raw.kind !== EDL_KIND || raw.timebase !== "microseconds" || raw.interval_semantics !== "half-open") {
    throw new TypeError("EDL identity, timebase, or interval semantics are invalid");
  }
  assertPlainObject(raw.source, "EDL.source");
  assertExactKeys(raw.source, ["asset_id", "duration_us"], "EDL.source");
  if (!Array.isArray(raw.cuts)) throw new TypeError("EDL.cuts must be an array");
  const parsedCuts = raw.cuts.map((value, index) => {
    assertPlainObject(value, `EDL.cuts[${index}]`);
    assertExactKeys(value, ["start_us", "end_us"], `EDL.cuts[${index}]`);
    return { startUs: value.start_us as number, endUs: value.end_us as number };
  });
  const edl = createEdl({
    assetId: raw.source.asset_id as string,
    durationUs: raw.source.duration_us as number,
    cuts: parsedCuts,
  });
  if (!sameRanges(parsedCuts, edl.cuts)) {
    throw new TypeError("EDL cuts must be sorted, disjoint, and non-adjacent");
  }
  return edl;
}

export function parseEdl(serialized: string): EditDecisionListV1 {
  let raw: unknown;
  try {
    raw = JSON.parse(serialized);
  } catch (error) {
    throw new SyntaxError(`EDL is not valid JSON: ${(error as Error).message}`);
  }
  return parseWireEdl(raw);
}
