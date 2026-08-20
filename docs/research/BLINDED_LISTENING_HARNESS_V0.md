# Blinded Listening and Regression Harness V0

**Status:** Implemented MVP; internal pilot evidence only

**Issue:** #5

**Contract package:** `0.5.0`

**Runtime/cost:** localhost, local CPU, FFmpeg/ffprobe, $0 external API cost

## Purpose

The harness turns immutable candidate masters into a reproducible, identity-hidden listening session. It exists to
catch audible damage and compare engine variants before an Adaptive Leveler, cleanup provider, router plan, recipe, or
transition renderer is considered for promotion.

Human scores remain the decision evidence. Integrated, momentary, and short-term loudness, LRA, true/sample peak,
clipping, duration, channels, SNR/SI-SDR, runtime, memory, device, and cost are diagnostic context only.

## Implemented boundary

| Boundary | V0 behavior |
|---|---|
| Candidate inputs | Existing local WAV/FLAC/MP3 files beneath the experiment directory; path and SHA-256 validated |
| Archived masters | Read-only inputs; hashes are rechecked after preparation |
| Listening copies | Metadata-stripped, 48 kHz, 24-bit WAV; linear two-pass loudness match; new opaque filenames |
| Presentation | Deterministic SHA-256 seed ordering; two-option clean preservation and two-or-more-option preference |
| Public state | Static UI, public session manifest, and whitelisted listening WAVs only |
| Private state | Experiment, identity map, diagnostics, scores, and mutable session state |
| Reveal | Processor, recipe, model, build, source fixture/hash/regions, and segment appear only after close |
| Report | Versioned canonical JSON, integrity hash, raw scores, descriptive means/counts, uncertainty, warnings |
| Network | Server rejects non-local bind addresses; no external assets, APIs, credentials, or model downloads |
| Promotion | Never automatic; V0 reports `descriptive_pilot_only` and `pilot_only`/`not_evaluated` |

## Experiment directory

Keep the manifest beside its private candidate tree so every path is portable and contained:

```text
experiment-root/
  experiment.json
  candidates/
    original.wav
    leveler-a.wav
    leveler-b.wav
```

`ListeningExperimentManifest` records:

- immutable experiment/corpus versions and randomization seed;
- target integrated loudness and true-peak ceiling;
- each candidate path, archived hash, role, source fixture, processor/model/recipe/build identity, and runtime/cost;
- each item mode, source hash, optional source-region IDs, candidate set, half-open segment, and neutral prompt;
- local-only, immutable-master, diagnostic-only, delayed-reveal, and prohibited-source policy flags.

Use the generated
[`listening-experiment-manifest.schema.json`](../../packages/contracts/schema/listening-experiment-manifest.schema.json)
as the authoring contract. Unknown fields, absolute/traversing paths, missing candidates, cross-source comparisons,
invalid clean-preservation roles, source-hash mismatch, duplicate IDs, and unused candidates fail closed.

## Prepare and run

Prerequisites are Python 3.12+, `uv`, FFmpeg, and ffprobe.

```bash
uv sync --all-packages --dev
uv run ampersand-listening prepare \
  /absolute/path/to/experiment-root/experiment.json \
  --output /tmp/ampersand-listening-session
uv run ampersand-listening serve /tmp/ampersand-listening-session
```

Open the printed `http://127.0.0.1:<port>` URL. The output directory must not exist; preparation publishes atomically
and never overwrites a prior session.

The UI requires an opaque listener pseudonym and captures:

- speech, background, and overall quality on 1–5 scales for every option;
- per-option and trial-level artifact flags;
- one preferred option or an explicit no-meaningful-preference result;
- confidence and optional private notes;
- audible degradation, voice/timbre change, naturalness, ambience/music change, and processing preference for clean
  preservation.

The preference mode supports Original/A/B or larger internal pilot sets. It is not a standards-conformant MUSHRA
implementation. Advanced panels, listener screening, anchors/references, cohort assignment, and formal power analysis
remain later work.

## Operator commands

```bash
uv run ampersand-listening status /tmp/ampersand-listening-session
uv run ampersand-listening close /tmp/ampersand-listening-session
uv run ampersand-listening report /tmp/ampersand-listening-session > report-copy.json
```

`close` is permanent for that workspace. It blocks further scores, writes `report.json`, stores its SHA-256 in private
state, and enables `/api/reveal`. Re-running `close` is idempotent. `report` refuses to reveal identities before close
or when the report fails its integrity hash.

For automation, `submit` accepts one score JSON matching
[`listening-score.schema.json`](../../packages/contracts/schema/listening-score.schema.json). The service assigns the
score ID, session ID, mode, and sequence; a listener pseudonym can score each trial only once.

## Diagnostics and interpretation

Every item/candidate receives:

- archived and listening-copy hashes;
- loudness before/after, including integrated LUFS, LRA, true peak, and measurement build;
- 100 ms momentary/short-term extrema and frame count;
- duration, sample rate, channels, sample peak, and clipped-sample count;
- centered SNR and SI-SDR when an aligned original/reference exists;
- candidate runtime, peak memory, device summary, and external cost.

The loudness preparation gate is ±0.35 LU from target and true peak no more than 0.20 dB above the configured ceiling.
These measurements prevent invalid comparisons and help diagnose failures. They are not combined into a quality score,
cannot approve a candidate, and should not overrule missing words, identity change, musical noise, pumping, clicks, or
other listener findings.

## Reproducibility and privacy

- Experiment, trial, option, preparation, score, and report IDs derive from canonical inputs and SHA-256.
- Repeating preparation with the same manifest and admitted native build produces identical manifests and WAV bytes.
- The public manifest contains opaque trial/option/source tokens, listening hashes, technical playback metadata, and
  neutral prompts—not candidate, processor, recipe, model, build, source-fixture, region, or filename identities.
- The HTTP server serves only `/`, `/session.json`, explicit opaque WAV paths, status, score, close, and delayed reveal.
- Requests are bounded, path traversal is rejected, responses are `no-store`, and no request/media identifiers are
  logged.
- Real recordings require the separate rights, consent, access, retention, and deletion controls in the quality and
  data-governance plans. The current automated test uses mathematical controls only.

## Immediate use

The harness can accept archived WAV outputs from #6, #7, #23, or #24 today. A valid internal pilot should include the
original/no-op control, exact candidate build and settings identity, clean material, known degradations, challenging
transitions, and per-candidate runtime. Do not tune against withheld material or treat repeated listening by one
developer as independent listener evidence.

## Open promotion work

Issue #5 remains open after the MVP foundation because product promotion still requires:

- rights-cleared human speech, music-under-speech, and representative real-world items;
- an actual multi-listener pilot and variance/power analysis;
- listener-screening and session-integrity policy for formal panels;
- access-controlled storage and tested deletion for restricted corpus/session data;
- long-form continuity listening and representative runtime/memory evidence;
- protocol expansion where formal MUSHRA/P.835 methodology is appropriate;
- explicit human reviewers and a separate approved/rejected promotion record.

Rollback is deletion of the generated session directory. Archived candidates and source files remain unchanged.
