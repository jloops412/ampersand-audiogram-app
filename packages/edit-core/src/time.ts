import type { Microseconds, TimeRange } from "./types.js";

export const MICROSECONDS_PER_SECOND = 1_000_000;

export function microseconds(value: number, field = "microseconds"): Microseconds {
  if (!Number.isSafeInteger(value) || value < 0) {
    throw new RangeError(`${field} must be a non-negative safe integer`);
  }
  return value as Microseconds;
}

export function nonEmptyId(value: string, field: string): string {
  if (typeof value !== "string" || value.trim().length === 0) {
    throw new TypeError(`${field} must be a non-empty string`);
  }
  return value;
}

export function timeRange(startUs: number, endUs: number, field = "range"): TimeRange {
  const start = microseconds(startUs, `${field}.startUs`);
  const end = microseconds(endUs, `${field}.endUs`);
  if (end <= start) {
    throw new RangeError(`${field} must be a non-empty half-open interval`);
  }
  return { startUs: start, endUs: end };
}

export function rangeLength(range: TimeRange): Microseconds {
  return microseconds(range.endUs - range.startUs, "range length");
}

export function formatFfmpegSeconds(valueUs: number): string {
  const value = microseconds(valueUs);
  const seconds = Math.floor(value / MICROSECONDS_PER_SECOND);
  const fraction = value % MICROSECONDS_PER_SECOND;
  return `${seconds}.${fraction.toString().padStart(6, "0")}`;
}
