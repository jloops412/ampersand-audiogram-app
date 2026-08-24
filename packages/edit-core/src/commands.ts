import { addCuts, normalizeCuts } from "./edl.js";
import { microseconds, nonEmptyId } from "./time.js";
import {
  EDIT_COMMAND_KIND,
  EDIT_COMMAND_SCHEMA_VERSION,
  type AddCutsCommandV1,
  type EditCommandV1,
  type EditDecisionListV1,
} from "./types.js";

export interface AddRangeCommandInput {
  readonly commandId: string;
  readonly source: { readonly assetId: string; readonly durationUs: number };
  readonly cuts: readonly { readonly startUs: number; readonly endUs: number }[];
}

export function createAddCutsCommand(input: AddRangeCommandInput): AddCutsCommandV1 {
  if (input.cuts.length === 0) throw new TypeError("cuts must contain at least one range");
  const durationUs = microseconds(input.source.durationUs, "command.source.durationUs");
  return {
    schemaVersion: EDIT_COMMAND_SCHEMA_VERSION,
    kind: EDIT_COMMAND_KIND,
    commandId: nonEmptyId(input.commandId, "commandId"),
    source: { assetId: nonEmptyId(input.source.assetId, "command.source.assetId"), durationUs },
    cuts: normalizeCuts(input.cuts, durationUs),
    origin: { type: "range" },
  };
}

function validateCommand(command: EditCommandV1, edl: EditDecisionListV1): void {
  if (command.schemaVersion !== EDIT_COMMAND_SCHEMA_VERSION || command.kind !== EDIT_COMMAND_KIND) {
    throw new TypeError("unsupported edit command");
  }
  nonEmptyId(command.commandId, "commandId");
  if (command.source.assetId !== edl.source.assetId || command.source.durationUs !== edl.source.durationUs) {
    throw new TypeError("edit command and EDL must identify the same immutable source");
  }
  const canonicalCuts = normalizeCuts(command.cuts, edl.source.durationUs);
  if (canonicalCuts.length !== command.cuts.length || canonicalCuts.some((cut, index) =>
    cut.startUs !== command.cuts[index]?.startUs || cut.endUs !== command.cuts[index]?.endUs)) {
    throw new TypeError("edit command cuts must be canonical");
  }
  if (command.origin.type === "transcript_words") {
    nonEmptyId(command.origin.transcriptId, "command.origin.transcriptId");
    if (command.origin.wordIds.length === 0 || new Set(command.origin.wordIds).size !== command.origin.wordIds.length) {
      throw new TypeError("transcript word command must contain unique word ids");
    }
    command.origin.wordIds.forEach((id, index) => nonEmptyId(id, `command.origin.wordIds[${index}]`));
  }
}

export function applyCommand(edl: EditDecisionListV1, command: EditCommandV1): EditDecisionListV1 {
  validateCommand(command, edl);
  return addCuts(edl, command.cuts);
}

export function replayCommands(baseEdl: EditDecisionListV1, commands: readonly EditCommandV1[]): EditDecisionListV1 {
  const ids = new Set<string>();
  return commands.reduce((edl, command) => {
    if (ids.has(command.commandId)) throw new TypeError(`duplicate edit command id: ${command.commandId}`);
    ids.add(command.commandId);
    return applyCommand(edl, command);
  }, baseEdl);
}
