# Smart Cleanup Guardrails V0.3

**Status:** Production protect-only planner; Manual deterministic cleanup remains executable

**Issue:** [#43](https://github.com/jloops412/ampersand-audiogram-app/issues/43)

**Last verified:** 2026-08-24

## Decision

Smart Cleanup is an Ampersand-owned policy layer between the Semantic Audio Map and the existing global FFmpeg cleanup
renderer. It resolves and persists a complete `cleanup-plan.json` before mastering.

V0.3 is deliberately **protect-only** in Smart mode. It may record bounded candidate stages, but it does not apply them
to production audio. Manual mode preserves and executes the operator's requested deterministic settings exactly.

This is the truthful behavior for the current evidence boundary: the production Semantic Map does not yet include an
admitted full-coverage music classifier or normalized stationary-noise, hum, rumble, and clipping detectors. Automatic
activation also lacks the required rights-cleared clean-preservation and listening evidence.

## Contract

Every plan records:

- the Semantic Map ID and SHA-256;
- the exact requested and resolved cleanup settings plus hashes;
- the embedded, versioned planner policy and hash;
- measured maxima for music, noise, rumble, hum, and clipping probabilities;
- music/stationary-noise evidence availability, protected-region count, conflict count, and resolved hum fundamental;
- one typed disposition for every cleanup stage;
- protect-only candidates, applied stages, reason codes, warnings, and whether production audio changed.

The plan ID derives from the run, Semantic Map hash, requested-settings hash, and planner-policy hash. Its manifest hash is
referenced by `ProductionRun`, the Smart Cleanup `JobStep`, and the final processing report.

## Policy snapshot

The candidate thresholds reuse the already-versioned Processing Router V0 values; they are not new activation claims:

| Evidence | Candidate boundary | Additional condition |
|---|---:|---|
| Music | protect above `0.35` | full-coverage music evidence is required |
| Stationary noise | `0.65` | normalized observation must declare `noise_class=stationary` |
| Rumble | `0.75` | normalized rumble probability |
| Hum | `0.80` | one consistent measured 50 Hz or 60 Hz fundamental |
| Clipping | none | automatic declipping remains disabled |

Gate, de-essing, voice EQ, compression, and declipping are manual-only. Candidate thresholds are shadow evidence until a
future issue promotes a detector and exact parameter set through model/dependency admission, hidden tests, clean-input
preservation, human listening, runtime, and rollback gates.

## Runtime behavior

1. Build the full-coverage Semantic Map and existing Router/Leveler shadow artifacts.
2. Resolve `cleanup-plan.json`.
3. In Smart mode, fail closed on missing music evidence, conflicts, music above the ceiling, or any protected region.
4. Otherwise record matching candidates and still bypass cleanup under the protect-only activation policy.
5. In Manual mode, execute only the exact requested global deterministic stages.
6. Run the measured two-pass loudness master and output validation in either mode.

Smart no-op is not a failed run. Final mastering, metadata, encoding, and audiogram rendering still execute.

## Non-claims

Smart Cleanup V0.3 is not neural restoration, music/source separation, dereverberation, de-echo, transcription, or an
active regional Router. A generic noise probability is not treated as stationary noise. Sample peak alone is not treated
as a clipping detector. No candidate is described as admitted or production-active.

## Verification and rollback

Required gates cover deterministic plan identity, exact Manual preservation, legacy missing-mode migration to Manual,
clean/music/uncertain protection, threshold-boundary candidate tests, unsupported clipping/generic-noise rejection, an
end-to-end Smart no-op run, an end-to-end Manual renderer run, schemas, types, media hashes, and output validation.

Rollback is a normal Cloud Run traffic rollback to the previous revision. Source media and historical run artifacts are
immutable; do not rewrite existing plans or settings snapshots.
