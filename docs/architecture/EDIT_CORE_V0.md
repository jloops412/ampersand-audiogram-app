# Deterministic Edit Core V0

**Status:** Issue #11 Lane B implementation checkpoint; Studio and rich-track integration remain open  
**Last verified:** 2026-08-24  
**Decision:** ADR-0014  
**Package:** `packages/edit-core` 0.1.0

## Outcome

Ampersand now owns a dependency-free TypeScript edit core for deterministic single-source spoken-word cuts. The core
uses non-negative safe-integer microseconds, non-empty half-open intervals, canonical cut lists, derived kept ranges,
immutable commands, command replay, undo/redo, strict versioned EDL JSON, transcript↔output mapping, and a deterministic
FFmpeg audio-filter plan.

This is a domain and render-planning checkpoint, not a new Studio editing surface. WaveSurfer remains a replaceable
presentation adapter. No WaveSurfer region, DOM state, provider payload, filesystem path, or raw transcript text enters
the EDL or render plan.

## V0 contract

Canonical EDL JSON has one source identity and a minimal cut list:

```json
{"schema_version":"1.0.0","kind":"ampersand.edl","timebase":"microseconds","interval_semantics":"half-open","source":{"asset_id":"asset-1","duration_us":4000000},"cuts":[{"start_us":1000000,"end_us":2000000}]}
```

Readers reject unsupported versions, missing/unknown fields, unsafe or negative numbers, empty ranges, out-of-duration
ranges, and non-canonical cut order. Writers emit keys in one fixed order without generated timestamps or random IDs.
The wire format follows the repository's snake-case contract convention while the TypeScript API uses idiomatic
camel-case properties. The source uses an immutable asset ID rather than a local path or signed URL.

V0 cuts obey these invariants:

1. every time value is a non-negative JavaScript safe integer in microseconds;
2. every range is non-empty and half-open: `[startUs, endUs)`;
3. canonical cuts are ordered, disjoint, and non-adjacent because touching/overlapping inputs merge;
4. derived kept ranges and cuts partition `[0, source.durationUs)` exactly once;
5. output duration equals source duration minus the exact sum of canonical cut lengths;
6. output segments are gapless and start at zero;
7. save → parse → save is byte-stable for the same logical EDL.

## Time mapping

`sourceToOutput` collapses removed spans and returns `kept` or `removed` explicitly. A cut interior is never silently
treated as playable. `outputToSource` accepts `left` or `right` bias because one output seam corresponds to both sides
of a removed source span. This includes cuts at time zero, at source end, and a fully removed source.

Source ranges are intersected with kept ranges and can produce zero, one, or multiple output segments. Transcript word
mapping is derived through that same function:

- `kept`: the whole word interval survives;
- `removed`: no word interval survives;
- `partial`: an arbitrary cut intersects part of the word.

The mapping preserves source intervals and their exact collapsed output intervals; it does not rewrite raw word timing.

## Transcript and command boundary

The core accepts a normalized read-only transcript containing a transcript ID, matching source identity, and word
records. Provider-native JSON, confidence payloads, and text are not copied into an EDL. A delete-words command resolves
the selected word IDs to source cut ranges once and records only the command's source binding, canonical ranges, and
word-selection provenance.

Commands have caller-supplied stable IDs and are pure add-cut operations in V0. Applying a command creates a new EDL.
Undo moves the last command to the redo stack and deterministically replays all remaining commands from the immutable
base EDL; redo replays it again. A new command after undo clears the redo branch. Duplicate command IDs and commands for
another source fail closed.

The command history is runtime editing state, while the EDL is the authoritative saved edit state. Reopening an EDL
does not promise to restore pre-save undo history; persisted history, if later required, needs its own versioned contract.

## Render-plan boundary

`buildAudioRenderPlan` converts kept source ranges to contiguous output segments and exact six-decimal FFmpeg times.
The plan emits only an audio `atrim`/`asetpts`/`concat` filter graph and output label; it does not choose input paths,
storage credentials, codecs, containers, loudness policy, or process execution.

The real-media test generates a deterministic 48 kHz PCM fixture, removes two exact one-second ranges, renders twice,
asserts a 3.000000-second output, and compares SHA-256 hashes. That proves repeatability for this pinned local/CI PCM
path. Bit identity across different FFmpeg builds, codecs, CPU architectures, or encoder settings is not claimed; those
belong to the media-worker build fingerprint and renderer acceptance suite.

## Verification

`npm run edit-core:test` compiles the strict TypeScript package and runs 12 Node tests, including:

- time/range validation and exact FFmpeg decimal formatting;
- cut normalization and kept/cut complement coverage;
- source/output mapping and left/right seam behavior;
- word deletion → undo → save/reopen → render-plan equality → redo/replay equality;
- raw transcript immutability and absence from serialized EDL JSON;
- strict schema and unknown-field rejection;
- a source-boundary scan preventing UI, provider, and Node runtime imports;
- source-bound command and redo-branch behavior;
- a fixed-seed (`0xa11ce5ed`) 1,000-case invariant run;
- two real FFmpeg PCM renders with exact duration and equal output hashes.

The root GitHub workflow runs this test after installing Node 20 and FFmpeg and before the production web build and
Cloud Run image build.

## Dawn-Cut audit and provenance

ADR-0014 records the audit of Dawn-Cut at commit `7de68fce41505d8092ec227806b8d4bea4127675`. Its public MIT repository validates
the architectural value of a pure TypeScript core, integer microseconds, half-open intervals, invariants, transcript
mapping, EDL generation, and undo/redo. The audited core is nevertheless an unpublished/private workspace package with
a Zod runtime dependency and a much broader video-first clip, frame-rate, speed, effects, path, project, and UI domain.

Ampersand therefore implemented this V0 independently. No Dawn-Cut source, tests, names, schemas, or project format were
copied or adapted, and Dawn-Cut does not enter Ampersand's runtime, dependency manifest, notices, or supply chain.

## Open gates

Issue #11 remains open for:

- Studio edit interactions and accessible WaveSurfer-to-command translation;
- save/reopen API and durable Production/Asset integration;
- caption, chapter, overlay, clip-export, and later multitrack versioned tracks;
- video render-plan and preview/export parity;
- real long-form and VBR source/output timing measurements;
- browser/mobile/assistive-technology gates from Lane A.

Captions, chapters, and overlays must use output/program-time contracts derived from the EDL and must define their
behavior when earlier cuts change. They will not be inserted as unvalidated optional blobs into EDL V1.

## Rollback and production impact

Rollback is removal of `packages/edit-core`, its root test command, workflow step, and these documentation changes. V0
is not imported by the deployed Studio or media worker, creates no schema/database migration, and mutates no production.
Existing Auphonic systems remain entirely outside this path.

## Primary sources

- [Dawn-Cut repository at the audited commit](https://github.com/kwakseongjae/dawn-cut/tree/7de68fce41505d8092ec227806b8d4bea4127675)
- [Dawn-Cut core package manifest](https://github.com/kwakseongjae/dawn-cut/blob/7de68fce41505d8092ec227806b8d4bea4127675/packages/core/package.json)
- [Dawn-Cut time utilities](https://github.com/kwakseongjae/dawn-cut/blob/7de68fce41505d8092ec227806b8d4bea4127675/packages/core/src/time.ts)
- [Dawn-Cut timeline invariants](https://github.com/kwakseongjae/dawn-cut/blob/7de68fce41505d8092ec227806b8d4bea4127675/packages/core/src/timeline.ts)
- [Dawn-Cut synchronization invariants](https://github.com/kwakseongjae/dawn-cut/blob/7de68fce41505d8092ec227806b8d4bea4127675/packages/core/src/sync.ts)
- [Dawn-Cut EDL implementation](https://github.com/kwakseongjae/dawn-cut/blob/7de68fce41505d8092ec227806b8d4bea4127675/packages/core/src/edl.ts)
- [Dawn-Cut history implementation](https://github.com/kwakseongjae/dawn-cut/blob/7de68fce41505d8092ec227806b8d4bea4127675/packages/core/src/history.ts)
- [Dawn-Cut MIT license](https://github.com/kwakseongjae/dawn-cut/blob/7de68fce41505d8092ec227806b8d4bea4127675/LICENSE)
