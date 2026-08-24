import { normalizeCuts } from "./edl.js";
import { sourceRangeToOutput } from "./timeline.js";
import { microseconds, nonEmptyId, rangeLength, timeRange } from "./time.js";
import {
  EDIT_COMMAND_KIND,
  EDIT_COMMAND_SCHEMA_VERSION,
  type AddCutsCommandV1,
  type EditDecisionListV1,
  type MappedTranscriptWord,
  type RawTranscript,
  type RawTranscriptWord,
} from "./types.js";

function validateWord(word: RawTranscriptWord, transcript: RawTranscript, index: number): void {
  nonEmptyId(word.id, `transcript.words[${index}].id`);
  if (typeof word.text !== "string") throw new TypeError(`transcript.words[${index}].text must be a string`);
  const range = timeRange(word.startUs, word.endUs, `transcript.words[${index}]`);
  if (range.endUs > transcript.source.durationUs) {
    throw new RangeError(`transcript.words[${index}] exceeds source duration`);
  }
  if (word.speakerId !== undefined) nonEmptyId(word.speakerId, `transcript.words[${index}].speakerId`);
}

export function validateTranscript(transcript: RawTranscript): void {
  nonEmptyId(transcript.transcriptId, "transcript.transcriptId");
  nonEmptyId(transcript.source.assetId, "transcript.source.assetId");
  microseconds(transcript.source.durationUs, "transcript.source.durationUs");
  if (!Array.isArray(transcript.words)) throw new TypeError("transcript.words must be an array");
  const ids = new Set<string>();
  transcript.words.forEach((word, index) => {
    validateWord(word, transcript, index);
    if (ids.has(word.id)) throw new TypeError(`duplicate transcript word id: ${word.id}`);
    ids.add(word.id);
  });
}

function assertSameSource(transcript: RawTranscript, edl: EditDecisionListV1): void {
  if (transcript.source.assetId !== edl.source.assetId || transcript.source.durationUs !== edl.source.durationUs) {
    throw new TypeError("transcript and EDL must identify the same immutable source");
  }
}

export interface DeleteWordsCommandInput {
  readonly commandId: string;
  readonly transcript: RawTranscript;
  readonly wordIds: readonly string[];
}

export function createDeleteWordsCommand(input: DeleteWordsCommandInput): AddCutsCommandV1 {
  validateTranscript(input.transcript);
  const requested = new Set(input.wordIds);
  if (requested.size === 0) throw new TypeError("wordIds must select at least one transcript word");
  const selected = input.transcript.words.filter((word) => requested.has(word.id));
  if (selected.length !== requested.size) {
    const known = new Set(selected.map((word) => word.id));
    const missing = [...requested].filter((id) => !known.has(id));
    throw new TypeError(`unknown transcript word ids: ${missing.join(", ")}`);
  }
  return {
    schemaVersion: EDIT_COMMAND_SCHEMA_VERSION,
    kind: EDIT_COMMAND_KIND,
    commandId: nonEmptyId(input.commandId, "commandId"),
    source: { assetId: input.transcript.source.assetId, durationUs: input.transcript.source.durationUs },
    cuts: normalizeCuts(selected.map((word) => ({ startUs: word.startUs, endUs: word.endUs })), input.transcript.source.durationUs),
    origin: {
      type: "transcript_words",
      transcriptId: input.transcript.transcriptId,
      wordIds: selected.map((word) => word.id),
    },
  };
}

export function mapTranscriptToOutput(
  edl: EditDecisionListV1,
  transcript: RawTranscript,
): readonly MappedTranscriptWord[] {
  validateTranscript(transcript);
  assertSameSource(transcript, edl);
  return transcript.words.map((word) => {
    const segments = sourceRangeToOutput(edl, word);
    const keptUs = segments.reduce((total, segment) => total + rangeLength(segment.source), 0);
    const wordUs = word.endUs - word.startUs;
    return {
      wordId: word.id,
      disposition: keptUs === 0 ? "removed" : keptUs === wordUs ? "kept" : "partial",
      segments,
    };
  });
}
