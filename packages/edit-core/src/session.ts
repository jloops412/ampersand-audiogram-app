import { applyCommand, replayCommands } from "./commands.js";
import type { EditCommandV1, EditDecisionListV1, EditSession } from "./types.js";

export function createEditSession(baseEdl: EditDecisionListV1): EditSession {
  return { baseEdl, appliedCommands: [], redoCommands: [], edl: baseEdl };
}

export function commitCommand(session: EditSession, command: EditCommandV1): EditSession {
  if ([...session.appliedCommands, ...session.redoCommands].some(
    (existing) => existing.commandId === command.commandId)) {
    throw new TypeError(`duplicate edit command id: ${command.commandId}`);
  }
  return {
    baseEdl: session.baseEdl,
    appliedCommands: [...session.appliedCommands, command],
    redoCommands: [],
    edl: applyCommand(session.edl, command),
  };
}

export function undo(session: EditSession): EditSession {
  const command = session.appliedCommands.at(-1);
  if (!command) return session;
  const appliedCommands = session.appliedCommands.slice(0, -1);
  return {
    baseEdl: session.baseEdl,
    appliedCommands,
    redoCommands: [command, ...session.redoCommands],
    edl: replayCommands(session.baseEdl, appliedCommands),
  };
}

export function redo(session: EditSession): EditSession {
  const command = session.redoCommands[0];
  if (!command) return session;
  const appliedCommands = [...session.appliedCommands, command];
  return {
    baseEdl: session.baseEdl,
    appliedCommands,
    redoCommands: session.redoCommands.slice(1),
    edl: replayCommands(session.baseEdl, appliedCommands),
  };
}
