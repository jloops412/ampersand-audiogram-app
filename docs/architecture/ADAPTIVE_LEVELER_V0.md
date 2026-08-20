# Ampersand Adaptive Leveler V0

**Status:** Deterministic shadow candidate; not authorized for production audio rendering

**Issue:** #6

**Algorithm version:** `0.1.0`

**Contract package:** `0.4.0`

**Runtime/cost:** local CPU, linear memory, $0 external API cost

## Purpose

The Adaptive Leveler reduces distracting speech-level differences without treating silence, room tone, noise, music, overlap, clipping, uncertainty, or already-comfortable speech as material that must be made louder. It is an Ampersand-owned control law over the provider-neutral Semantic Audio Map.

V0 is intentionally shadow-only in the runnable pipeline. It emits the candidate envelope and full reasoning/statistics while the audible master continues to use only the separate standards-based final loudness/true-peak stage. This gives the quality harness real proposed decisions to evaluate without silently shipping an unlistened processor.

## Stage separation

| Stage | V0 behavior |
|---|---|
| Semantic analysis | Supplies speech/silence/content confidence, speaker evidence, momentary/short-term loudness, and peak risk |
| Adaptive Leveler | Plans slow content-aware gain and reports corrections |
| Short-term compressor | Not implemented and never folded into Leveler settings/statistics |
| Final loudness/true peak | Existing independent two-pass master remains active |

## Eligible evidence

A region contributes only when it is:

- labeled speech and explicitly `eligible`;
- unprotected and conflict-free;
- above speech and region-confidence thresholds;
- below silence, overlap, and clipping-risk thresholds;
- backed by finite momentary loudness in the supported range.

Missing or low-confidence speaker labels use a global speech profile. Music, silence, noise, ambience, unknown, mixed/conflicted, clipping-risk, and unsupported content is forced to unity.

## Control law

1. Blend momentary loudness with a bounded contribution from short-term loudness. Short-term evidence is limited to ±8 LU around the momentary observation before applying the configurable weight, which reduces lag/startup influence.
2. Calculate a duration/confidence-weighted median across reliable speech and clamp it to the recipe's target range.
3. Calculate per-speaker robust levels when enough reliable duration exists; otherwise use the global fallback.
4. Create a comfort band around the target. Speech already within the band receives no raw local correction.
5. Clamp per-speaker offsets, maximum boost/cut, and positive gain against the most conservative sample/true-peak headroom.
6. Smooth each contiguous eligible run in both directions and taper protected boundaries.
7. Project the full timeline onto configured gain-slope and gain-acceleration constraints while fixing protected points at unity. Corrections may only move toward zero during projection.
8. Serialize deterministic microsecond gain points with linear interpolation for a future sample-accurate renderer.

The settings are strict contract inputs, not hidden constants. They include comfort/target ranges, boost/cut/speaker caps, smoothing/taper, momentary-versus-short-term balance, speech/silence/overlap/clipping gates, peak ceiling, significant-correction threshold, velocity, and acceleration. These are suitable for later schema-driven Advanced Studio controls and immutable template/run snapshots.

## Artifacts

The local pipeline writes:

```text
loudness-before.json
semantic-map-v0.json
leveler-settings.json
gain-envelope.json
leveler-statistics.json
steps/adaptive-leveler-shadow.json
artifacts/master.wav
artifacts/master.mp3
loudness-after.json
processing-report.json
```

`LevelerStatistics` records the settings hash, target/comfort band, eligible/changed duration, eligible/protected/changed counts, min/mean/max gain, measured maximum slope/acceleration, peak-limited count, speaker profiles, significant correction intervals, reasoning, warnings, and activation mode. The processing report references the envelope/statistics IDs and hashes.

## Determinism and complexity

Envelope identity derives from Semantic Map hash, complete Leveler settings hash, run ID, and algorithm version. Repeated runs with identical inputs serialize byte-identical artifacts.

For `n` Semantic Map regions and a small number of speakers, V0 uses O(n) timeline memory and bounded deterministic projection passes. The automated fixture includes a one-hour/3,600-region timeline so long-form indexing, bounds, and determinism run in CI without recorded media or an external service.

## Current verification

Automated coverage includes:

- quiet/comfortable/loud speech behavior;
- silence, music, noise, unknown, clipping-risk, and conflicted protection;
- clean-input unity/no-op;
- sample/true-peak boost clamping;
- multi-speaker relative profiles and short-speaker fallback;
- velocity/acceleration bounds;
- settings hashing and repeated-run identity;
- active-mode failure when music/protected-content evidence is unavailable;
- one-hour timeline behavior;
- full pipeline artifacts, step metrics, report references, loudness target, true peak, and source immutability.

## Promotion gates still open

V0 must not become active merely because its unit tests pass. Issue #6 remains open until the applicable evidence exists:

- rights-cleared stepped, whisper, multi-speaker, HVAC, speech-over-music, laughter/applause, transient, clean-master, and long-form audio fixtures;
- sample-accurate offline gain rendering with stereo preservation and measured click-free transitions;
- loudness-matched human listening against original/no-op and prior admitted baselines;
- clean-input preservation and emotional-pause/music protection;
- checkpoint-backed or otherwise admitted music/protected-content evidence;
- runtime/memory evidence on representative one-hour audio, not only a synthetic map;
- separate short-term compressor design/evaluation if later required;
- documented rollback to the unity envelope plus final loudness master.

Until then, the pipeline reports the proposed envelope but renders unity at the Leveler stage.
