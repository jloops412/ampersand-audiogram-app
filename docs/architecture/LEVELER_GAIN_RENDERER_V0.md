# Leveler Gain Renderer V0

**Status:** Implemented evaluation path; not production-approved

**Issue:** #6

**Renderer algorithm:** `0.1.0`

**Media worker:** `0.5.0`

**Contract package:** `0.7.0`

**Runtime/cost:** local CPU, bounded working memory, $0 external API cost

## Purpose

The renderer makes Adaptive Leveler envelopes audible without activating them in the normal master path. It converts a
validated `GainEnvelope` and its exact analysis source into a separate lossless candidate that can enter the blinded
listening harness.

This closes an implementation gap, not a quality gate. `ampersand-engine process` still renders the production
`master.wav`/`master.mp3` from the protected unity path plus final loudness mastering. The candidate is explicitly
`evaluation_only=true`, `production_approved=false`, and excluded from `OutputManifest`.

## Stage boundary

| Stage | V0 behavior |
|---|---|
| Semantic Map | Supplies protected/eligible content evidence to the Leveler planner |
| Adaptive Leveler | Produces the bounded linear-in-dB `GainEnvelope` |
| Evaluation renderer | Applies only that envelope to a new PCM24 WAV |
| Short-term compressor | Not implemented and not hidden inside this renderer |
| Final loudness/true peak | Not applied to the candidate; blinded preparation matches and validates playback loudness |
| Production master | Unchanged; continues to use the existing two-pass final-master path |

## Run

First run the ordinary local pipeline to produce a shadow envelope:

```bash
uv run --package ampersand-media-worker ampersand-engine process \
  /absolute/path/to/source.wav \
  --output /tmp/ampersand-production
```

Use the exact audio analyzed by that run: `artifacts/canonical.wav` when `canonical-manifest.json` exists; otherwise
use the immutable original source.

```bash
uv run --package ampersand-media-worker ampersand-engine render-leveler-candidate \
  /tmp/ampersand-production/artifacts/canonical.wav \
  /tmp/ampersand-production/gain-envelope.json \
  --output /tmp/ampersand-leveler-candidate
```

The output directory must not exist. It contains:

```text
candidate.wav
gain-render-manifest.json
gain-render-runtime.json
```

If the pipeline did not create canonical audio, substitute the original source path. Add `candidate.wav` and the
original/no-op/prior candidate to a versioned listening experiment, then use
[Blinded Listening and Regression Harness V0](../research/BLINDED_LISTENING_HARNESS_V0.md). Do not compare the raw
files at unmatched playback levels.

## Sample mapping

The renderer decodes the selected local source to interleaved 48 kHz float32 PCM through the restricted FFmpeg
file/pipe protocol. For decoded frame index `n`, it evaluates the envelope at the exact sample position

\[
t_n = \frac{n}{48000}
\]

and linearly interpolates gain in dB between adjacent envelope points. It converts that value to one channel-linked
linear multiplier

\[
a_n = 10^{g_n / 20}
\]

and applies `a_n` to every channel in the frame. The result is deterministically quantized to little-endian 24-bit PCM.
No per-channel auto-balance, compressor, limiter, EQ, denoise, or final loudness filter is added.

## Fail-closed validation

Rendering refuses and atomically removes partial output when:

- the envelope is not an `adaptive_leveler` envelope;
- the source is missing, empty, unreadable, or differs from envelope duration by more than 10 ms;
- decoded duration differs by more than two 48 kHz frames;
- the source has more than eight channels or the output changes channel count/sample rate;
- PCM contains non-finite values;
- applied gain would create any sample over full scale;
- adjacent rendered samples would change gain by more than 0.001 dB;
- the output path already exists;
- the source hash changes during rendering.

The 0.001 dB adjacent-sample ceiling corresponds to 48 dB/second at 48 kHz and remains above the planner's maximum
allowed slope while rejecting malformed step-like envelopes. It is a technical continuity gate, not proof that a
transition is inaudible.

## Deterministic manifest

`GainRenderManifest` records:

- source and envelope SHA-256 plus run/envelope IDs;
- renderer algorithm/build and exact FFmpeg build;
- candidate path/hash/size and PCM encoding;
- source/candidate duration, expected/rendered frames, sample rate, and channels;
- input/output sample peak, zero clipped samples, gain bounds, and maximum adjacent gain delta;
- channel-linked/sample-accurate behavior and the evaluation-only/non-production policy flags.

Its identity excludes wall-clock performance. The same source, envelope, worker/native build, and architecture produces
the same candidate bytes and deterministic manifest.

`GainRenderRuntimeReport` is separate because runtime is observational. It records wall time, audio seconds, real-time
factor, block size, peak accounted NumPy/PCM working-buffer memory, a non-hostname device summary, and zero external
cost. The buffer number is not total process RSS and must be labeled accordingly in performance evidence.

## Memory and privacy

The renderer decodes to a private temporary float32 file, processes fixed-size blocks, writes PCM24 incrementally, and
deletes the decoded temporary before atomic publication. Memory is O(block frames × channels), not O(program length).
The candidate remains local; no network, model, credential, transcript, or customer-training path is used.

Generated candidates and runtime reports may contain or describe private audio and stay outside Git. Real material still
requires the rights, consent, access, retention, encryption, and deletion controls in the data-governance plan.

## Current evidence and open gates

Automated tests prove byte determinism, source immutability, exact frame/channel preservation, channel-linked gain,
linear-in-dB sample interpolation, bounded working memory, CLI operation, manifest round trips, and failure cleanup for
duration mismatch, clipping, excessive gain velocity, wrong-purpose envelopes, and overwrite attempts.

Issue #6 remains open. Production activation still requires:

- rights-cleared stepped, multi-speaker, clean, protected music/ambience, events, whisper, and long-form candidate renders;
- loudness-matched blind preference and clean-preservation scores;
- human confirmation that boundaries contain no clicks, pumping, flattening, word damage, identity change, or fatigue;
- admitted music/protected-content evidence before active planning;
- representative one-hour real-time factor, total process memory, recovery, and disk evidence;
- a separately designed compressor if needed;
- explicit human approval and rollback to unity Leveler plus final loudness master.

Rollback is deletion of the evaluation output directory or removal of the standalone command. No production recipe,
processing plan, master, or historical run depends on the candidate artifact.
