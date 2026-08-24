import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdtempSync, readFileSync, readdirSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";

import {
  applyCommand,
  buildAudioRenderPlan,
  commitCommand,
  createAddCutsCommand,
  createDeleteWordsCommand,
  createEdl,
  createEditSession,
  deriveKeptRanges,
  formatFfmpegSeconds,
  mapTranscriptToOutput,
  microseconds,
  normalizeCuts,
  outputDurationUs,
  outputToSource,
  parseEdl,
  rangeLength,
  redo,
  replayCommands,
  serializeEdl,
  sourceRangeToOutput,
  sourceToOutput,
  timeRange,
  undo,
} from "../.test-dist/index.js";

test("safe integer microseconds and non-empty half-open ranges are enforced", () => {
  assert.equal(microseconds(0), 0);
  assert.equal(formatFfmpegSeconds(12_000_034), "12.000034");
  assert.deepEqual(timeRange(1, 2), { startUs: 1, endUs: 2 });
  assert.throws(() => microseconds(-1), /non-negative safe integer/);
  assert.throws(() => microseconds(0.5), /non-negative safe integer/);
  assert.throws(() => microseconds(Number.MAX_SAFE_INTEGER + 1), /non-negative safe integer/);
  assert.throws(() => timeRange(10, 10), /non-empty half-open interval/);
});

test("cuts normalize deterministically and kept ranges form the exact complement", () => {
  const cuts = normalizeCuts(
    [
      { startUs: 5_000_000, endUs: 7_000_000 },
      { startUs: 1_000_000, endUs: 2_000_000 },
      { startUs: 2_000_000, endUs: 3_000_000 },
      { startUs: 6_000_000, endUs: 8_000_000 },
    ],
    10_000_000,
  );
  assert.deepEqual(cuts, [
    { startUs: 1_000_000, endUs: 3_000_000 },
    { startUs: 5_000_000, endUs: 8_000_000 },
  ]);
  const edl = createEdl({ assetId: "asset-1", durationUs: 10_000_000, cuts });
  assert.deepEqual(deriveKeptRanges(edl), [
    { startUs: 0, endUs: 1_000_000 },
    { startUs: 3_000_000, endUs: 5_000_000 },
    { startUs: 8_000_000, endUs: 10_000_000 },
  ]);
  assert.equal(outputDurationUs(edl), 5_000_000);
});

test("source/output mapping exposes removed points and resolves seams explicitly", () => {
  const edl = createEdl({
    assetId: "asset-1",
    durationUs: 10_000_000,
    cuts: [
      { startUs: 0, endUs: 1_000_000 },
      { startUs: 3_000_000, endUs: 5_000_000 },
      { startUs: 9_000_000, endUs: 10_000_000 },
    ],
  });
  assert.deepEqual(sourceToOutput(edl, 500_000), {
    sourceUs: 500_000,
    outputUs: 0,
    disposition: "removed",
  });
  assert.deepEqual(sourceToOutput(edl, 6_000_000), {
    sourceUs: 6_000_000,
    outputUs: 3_000_000,
    disposition: "kept",
  });
  assert.equal(outputToSource(edl, 0, "left"), 0);
  assert.equal(outputToSource(edl, 0, "right"), 1_000_000);
  assert.equal(outputToSource(edl, 2_000_000, "left"), 3_000_000);
  assert.equal(outputToSource(edl, 2_000_000, "right"), 5_000_000);
  assert.equal(outputToSource(edl, 6_000_000, "left"), 9_000_000);
  assert.equal(outputToSource(edl, 6_000_000, "right"), 10_000_000);
});

test("source ranges split around cuts and retain exact output positions", () => {
  const edl = createEdl({
    assetId: "asset-1",
    durationUs: 8_000_000,
    cuts: [{ startUs: 2_000_000, endUs: 4_000_000 }],
  });
  assert.deepEqual(sourceRangeToOutput(edl, { startUs: 1_000_000, endUs: 5_000_000 }), [
    {
      source: { startUs: 1_000_000, endUs: 2_000_000 },
      output: { startUs: 1_000_000, endUs: 2_000_000 },
    },
    {
      source: { startUs: 4_000_000, endUs: 5_000_000 },
      output: { startUs: 2_000_000, endUs: 3_000_000 },
    },
  ]);
});

function fixtureTranscript() {
  return {
    transcriptId: "transcript-raw-7",
    source: { assetId: "asset-1", durationUs: 8_000_000 },
    words: [
      { id: "w1", text: "keep", startUs: 0, endUs: 1_000_000 },
      { id: "w2", text: "remove", startUs: 1_000_000, endUs: 2_000_000 },
      { id: "w3", text: "also remove", startUs: 2_500_000, endUs: 3_500_000 },
      { id: "w4", text: "partly clipped", startUs: 3_500_000, endUs: 5_500_000 },
    ],
  };
}

test("delete words, undo, redo, save, reopen, and render-plan replay are identical", () => {
  const transcript = fixtureTranscript();
  const base = createEdl({ assetId: "asset-1", durationUs: 8_000_000 });
  const command = createDeleteWordsCommand({
    commandId: "delete-w2-w3",
    transcript,
    wordIds: ["w3", "w2", "w3"],
  });
  assert.deepEqual(command.origin.wordIds, ["w2", "w3"]);
  assert.deepEqual(command.cuts, [
    { startUs: 1_000_000, endUs: 2_000_000 },
    { startUs: 2_500_000, endUs: 3_500_000 },
  ]);

  const applied = commitCommand(createEditSession(base), command);
  assert.deepEqual(applied.edl.source, base.source);
  assert.equal(outputDurationUs(applied.edl), 6_000_000);

  const undone = undo(applied);
  const reopenedUndo = parseEdl(serializeEdl(undone.edl));
  assert.equal(serializeEdl(reopenedUndo), serializeEdl(base));
  assert.deepEqual(buildAudioRenderPlan(reopenedUndo), buildAudioRenderPlan(base));

  const redone = redo(undone);
  const saved = serializeEdl(redone.edl);
  const reopened = parseEdl(saved);
  assert.equal(serializeEdl(reopened), saved);
  assert.deepEqual(buildAudioRenderPlan(reopened), buildAudioRenderPlan(redone.edl));
  assert.deepEqual(replayCommands(base, [command]), redone.edl);
  assert.ok(!saved.includes("transcript-raw-7"));
  assert.ok(!saved.includes("remove"));
});

test("transcript mapping is derived without mutating or persisting the raw transcript", () => {
  const transcript = fixtureTranscript();
  const before = structuredClone(transcript);
  const edl = createEdl({
    assetId: "asset-1",
    durationUs: 8_000_000,
    cuts: [
      { startUs: 1_000_000, endUs: 2_000_000 },
      { startUs: 4_000_000, endUs: 4_500_000 },
    ],
  });
  const mapped = mapTranscriptToOutput(edl, transcript);
  assert.deepEqual(
    mapped.map(({ wordId, disposition }) => ({ wordId, disposition })),
    [
      { wordId: "w1", disposition: "kept" },
      { wordId: "w2", disposition: "removed" },
      { wordId: "w3", disposition: "kept" },
      { wordId: "w4", disposition: "partial" },
    ],
  );
  assert.deepEqual(transcript, before);
});

test("canonical EDL JSON is stable and strict readers reject ambiguous documents", () => {
  const edl = createEdl({
    assetId: "asset-1",
    durationUs: 4_000_000,
    cuts: [{ startUs: 1_000_000, endUs: 2_000_000 }],
  });
  const serialized = serializeEdl(edl);
  assert.equal(
    serialized,
    '{"schemaVersion":"1.0.0","kind":"ampersand.edl","timebase":"microseconds","intervalSemantics":"half-open","source":{"assetId":"asset-1","durationUs":4000000},"cuts":[{"startUs":1000000,"endUs":2000000}]}',
  );
  assert.equal(serializeEdl(parseEdl(serialized)), serialized);
  assert.throws(
    () => parseEdl(serialized.replace('"cuts":', '"unknown":true,"cuts":')),
    /missing or unknown fields/,
  );
  assert.throws(
    () =>
      parseEdl(
        serialized.replace(
          '[{"startUs":1000000,"endUs":2000000}]',
          '[{"startUs":2000000,"endUs":3000000},{"startUs":1000000,"endUs":2000000}]',
        ),
      ),
    /sorted, disjoint, and non-adjacent/,
  );
  assert.throws(
    () => serializeEdl({ ...edl, waveSurferRegion: { start: 1, end: 2 } }),
    /missing or unknown fields/,
  );
});

test("edit-core source stays free of UI, provider, and Node runtime imports", () => {
  const sourceDirectory = new URL("../src/", import.meta.url);
  const source = readdirSync(sourceDirectory)
    .filter((name) => name.endsWith(".ts"))
    .map((name) => readFileSync(new URL(name, sourceDirectory), "utf8"))
    .join("\n");
  assert.doesNotMatch(source, /from\s+["'](?:node:|react|wavesurfer\.js|@google-cloud|express)/);
  assert.doesNotMatch(source, /\b(?:WaveSurfer|HTMLElement|mediaPath|signedUrl)\b/);
});

test("commands are source-bound, immutable in effect, and branch-safe", () => {
  const base = createEdl({ assetId: "asset-1", durationUs: 5_000_000 });
  const command = createAddCutsCommand({
    commandId: "cut-1",
    source: base.source,
    cuts: [{ startUs: 1_000_000, endUs: 2_000_000 }],
  });
  const snapshot = structuredClone(base);
  const after = applyCommand(base, command);
  assert.deepEqual(base, snapshot);
  assert.notEqual(after, base);

  const undone = undo(commitCommand(createEditSession(base), command));
  assert.throws(() => commitCommand(undone, command), /duplicate edit command id/);
  const replacement = createAddCutsCommand({
    commandId: "cut-2",
    source: base.source,
    cuts: [{ startUs: 3_000_000, endUs: 4_000_000 }],
  });
  assert.equal(commitCommand(undone, replacement).redoCommands.length, 0);

  const wrongSource = createAddCutsCommand({
    commandId: "wrong-source",
    source: { assetId: "asset-2", durationUs: 5_000_000 },
    cuts: [{ startUs: 1, endUs: 2 }],
  });
  assert.throws(() => applyCommand(base, wrongSource), /same immutable source/);
});

test("audio render plans use exact decimal times and contiguous output segments", () => {
  const edl = createEdl({
    assetId: "asset-1",
    durationUs: 5_000_000,
    cuts: [
      { startUs: 1_000_000, endUs: 2_000_000 },
      { startUs: 3_000_000, endUs: 4_000_000 },
    ],
  });
  const plan = buildAudioRenderPlan(edl);
  assert.equal(plan.outputDurationUs, 3_000_000);
  assert.deepEqual(plan.segments, [
    {
      source: { startUs: 0, endUs: 1_000_000 },
      output: { startUs: 0, endUs: 1_000_000 },
    },
    {
      source: { startUs: 2_000_000, endUs: 3_000_000 },
      output: { startUs: 1_000_000, endUs: 2_000_000 },
    },
    {
      source: { startUs: 4_000_000, endUs: 5_000_000 },
      output: { startUs: 2_000_000, endUs: 3_000_000 },
    },
  ]);
  assert.equal(
    plan.filterComplex,
    "[0:a]atrim=start=0.000000:end=1.000000,asetpts=PTS-STARTPTS[ampersand_a0];" +
      "[0:a]atrim=start=2.000000:end=3.000000,asetpts=PTS-STARTPTS[ampersand_a1];" +
      "[0:a]atrim=start=4.000000:end=5.000000,asetpts=PTS-STARTPTS[ampersand_a2];" +
      "[ampersand_a0][ampersand_a1][ampersand_a2]concat=n=3:v=0:a=1[ampersand_audio_out]",
  );
});

function seededRandom(seed) {
  let value = seed >>> 0;
  return () => {
    value ^= value << 13;
    value ^= value >>> 17;
    value ^= value << 5;
    return value >>> 0;
  };
}

test("1,000 seeded generated EDLs preserve coverage, ordering, mapping, and serialization", () => {
  const random = seededRandom(0xa11ce5ed);
  for (let run = 0; run < 1_000; run += 1) {
    const durationUs = 1 + (random() % 50_000_000);
    const requested = [];
    const count = random() % 20;
    for (let index = 0; index < count; index += 1) {
      const startUs = random() % durationUs;
      const endUs = startUs + 1 + (random() % (durationUs - startUs));
      requested.push({ startUs, endUs });
    }
    const edl = createEdl({ assetId: `generated-${run}`, durationUs, cuts: requested });
    const kept = deriveKeptRanges(edl);

    for (let index = 0; index < edl.cuts.length; index += 1) {
      const cut = edl.cuts[index];
      assert.ok(cut.endUs > cut.startUs);
      assert.ok(cut.endUs <= durationUs);
      if (index > 0) assert.ok(edl.cuts[index - 1].endUs < cut.startUs);
    }

    const coverage = [...edl.cuts, ...kept].sort(
      (left, right) => left.startUs - right.startUs || left.endUs - right.endUs,
    );
    let cursor = 0;
    for (const range of coverage) {
      assert.equal(range.startUs, cursor);
      cursor = range.endUs;
    }
    assert.equal(cursor, durationUs);
    assert.equal(
      kept.reduce((total, range) => total + rangeLength(range), 0),
      outputDurationUs(edl),
    );

    for (const range of kept) {
      const points = new Set([
        range.startUs,
        range.endUs - 1,
        range.startUs + Math.floor((range.endUs - range.startUs) / 2),
      ]);
      for (const sourceUs of points) {
        const mapped = sourceToOutput(edl, sourceUs);
        assert.equal(mapped.disposition, "kept");
        assert.equal(outputToSource(edl, mapped.outputUs, "right"), sourceUs);
      }
    }
    const serialized = serializeEdl(edl);
    assert.equal(serializeEdl(parseEdl(serialized)), serialized);
    assert.deepEqual(buildAudioRenderPlan(parseEdl(serialized)), buildAudioRenderPlan(edl));
  }
});

const ffmpegAvailable = spawnSync("ffmpeg", ["-version"], { encoding: "utf8" }).status === 0;
const ffprobeAvailable = spawnSync("ffprobe", ["-version"], { encoding: "utf8" }).status === 0;

test(
  "FFmpeg renders the same PCM bytes and exact planned duration twice",
  { skip: !(ffmpegAvailable && ffprobeAvailable) },
  () => {
    const directory = mkdtempSync(join(tmpdir(), "ampersand-edit-core-"));
    try {
      const input = join(directory, "input.wav");
      const outputA = join(directory, "output-a.wav");
      const outputB = join(directory, "output-b.wav");
      const fixture = spawnSync(
        "ffmpeg",
        [
          "-v",
          "error",
          "-y",
          "-f",
          "lavfi",
          "-i",
          "sine=frequency=440:sample_rate=48000:duration=5",
          "-c:a",
          "pcm_s16le",
          input,
        ],
        { encoding: "utf8" },
      );
      assert.equal(fixture.status, 0, fixture.stderr);

      const plan = buildAudioRenderPlan(
        createEdl({
          assetId: "fixture",
          durationUs: 5_000_000,
          cuts: [
            { startUs: 1_000_000, endUs: 2_000_000 },
            { startUs: 3_000_000, endUs: 4_000_000 },
          ],
        }),
      );
      for (const output of [outputA, outputB]) {
        const render = spawnSync(
          "ffmpeg",
          [
            "-v",
            "error",
            "-y",
            "-i",
            input,
            "-filter_complex",
            plan.filterComplex,
            "-map",
            plan.outputLabel,
            "-c:a",
            "pcm_s16le",
            output,
          ],
          { encoding: "utf8" },
        );
        assert.equal(render.status, 0, render.stderr);
      }
      const probe = spawnSync(
        "ffprobe",
        ["-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", outputA],
        { encoding: "utf8" },
      );
      assert.equal(probe.status, 0, probe.stderr);
      assert.equal(probe.stdout.trim(), "3.000000");
      const digest = (path) => createHash("sha256").update(readFileSync(path)).digest("hex");
      assert.equal(digest(outputA), digest(outputB));
    } finally {
      rmSync(directory, { recursive: true, force: true });
    }
  },
);
