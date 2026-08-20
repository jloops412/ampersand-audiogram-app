# Semantic Audio Map V0

**Issue:** #22  
**Map version:** `0.1.0`  
**Contract schema:** `1.1.0`  
**Runtime:** local CPU, FFmpeg 6+, NumPy  
**External API cost:** $0

## Purpose

The Semantic Audio Map is Ampersand's durable content-awareness layer. It lets the Leveler, Processing Router, transcript tools, reports, and Studio consume one provider-neutral timeline instead of embedding a VAD, ASR, diarization, or model vendor's schema into product behavior.

Every region uses a half-open integer-microsecond interval `[start_us, end_us)`. Regions are ordered, contiguous, non-empty, begin at zero, and cover the complete source duration. Raw observations may overlap and disagree.

## V0 evidence paths

### Deterministic loudness and peak adapter

FFmpeg's `ebur128` filter emits 100 ms momentary loudness, short-term loudness, and per-frame true-peak measurements. Ampersand parses only metric frames, excludes command lines and local paths, preserves the parsed provider payload separately, and maps measurements into Ampersand observation kinds.

### Ampersand energy/spectral VAD

The first-party V0 detector decodes a 16 kHz mono analysis stream and calculates 100 ms RMS, sample peak, speech-band energy, rumble energy, spectral flatness, and zero-crossing rate. It estimates a bounded noise floor, derives soft activity/speech/silence probabilities, smooths adjacent probabilities, and retains hysteresis state without collapsing evidence into edit cuts.

This detector has no model, checkpoint, runtime download, hosted request, or license dependency. Its confidence is deliberately bounded because energy/spectral features alone cannot reliably distinguish speech from music. It can unlock conservative Leveler development; it cannot authorize destructive editing or unprotected music processing.

### Optional understanding adapters

Provider-neutral transcript and active-speaker adapters map fixture or admitted-provider segments onto the same timeline. Their absence is recorded in `unavailable_adapters` and never prevents map creation or final mastering. A future Silero/ONNX, ASR, diarization, or semantic classifier must retain its native output separately and enter through the same adapter boundary.

## Contract layout

- `provenance_sources`: deduplicated provider, adapter, model, version, determinism, and native-artifact references;
- `observations`: normalized typed evidence with interval, confidence, value, unit, attributes, and provenance reference;
- `conflicts`: explicit same-kind disagreement, mutually exclusive high-probability evidence, and speaker-label overlap;
- `regions`: fixed-hop fused views containing probabilities, measurements, speaker evidence, evidence/conflict IDs, provider references, and processing eligibility;
- `provider_native_artifact_ids`: audit references to separately checksummed provider output;
- `unavailable_adapters` and `warnings`: partial-availability and safety context.

Provenance is stored once and referenced by ID from observations. This reduced the synthetic six-second fixture map from about 262 KB to 158 KB before transport compression; gzip reduces that fixture to about 21 KB. Production storage should keep semantic artifacts in private object storage with content compression, never in D1 rows or workflow event payloads.

## Fusion and safety policy

V0 uses a deterministic 100 ms grid and a sweep-line fusion pass. It retains every normalized observation, then calculates confidence-weighted regional probabilities and measurement summaries.

- reliable same-kind probability evidence differing by at least `0.55` creates a conflict;
- simultaneous high speech/silence or speech/music evidence creates a conflict;
- multiple reliable active-speaker labels create a conflict;
- conflicts produce `mixed` + `protect` rather than a forced winner;
- confident speech may be marked `eligible` for a later Leveler;
- confident silence is `no_op`;
- music, noise, ambience, unknown, unsupported, and uncertain regions remain `protect`;
- this issue does not activate regional processing—the current Processing Plan protects the full program until #6 and #23 consume the map.

These thresholds are versioned policy, not claims of final classifier quality. Listening and rights-cleared evaluation remain required before promotion.

## Artifacts

The local engine now emits:

```text
semantic-map-v0.json
semantic-map-debug.html
provider-native/ffmpeg-ebur128.json
provider-native/ffmpeg-ebur128.manifest.json
provider-native/ampersand-energy-vad-v0.json
provider-native/ampersand-energy-vad-v0.manifest.json
steps/semantic-map-v0.json
```

The debug HTML visualizes content coverage, providers, observation kinds, eligibility, and conflicts. It intentionally omits transcript text and local paths.

## Compatibility and migration

Issue #21 emitted a protected placeholder using Semantic Map schema `1.0.0`. `read_semantic_map()` explicitly upgrades that placeholder to `1.1.0`, records a migration warning, preserves its protected region, and adds empty provenance/observation/conflict collections. Unsupported schema versions fail closed.

## Privacy, security, and rollback

- analysis is local and uses only `file`/`pipe` FFmpeg protocols;
- raw artifacts contain numeric frames, exact provider versions, and redaction notes—not source paths, credentials, or transcript text;
- source bytes remain immutable;
- temporary artifacts disappear on failure;
- the current VAD uses no customer-media training path and no network;
- rollback is removal of the Semantic Map V0 stage and continued use of the explicit `1.0.0` protected placeholder reader; no source or master media migration is required.

## Next dependency

Issue #6 can now build the Adaptive Leveler against soft speech/silence probabilities, momentary/short-term loudness, peak risk, protection, conflicts, and optional speaker evidence. Issue #23 will later own regional processor selection and fallback policy. An admitted checkpoint-backed VAD remains a swappable challenger, not a replacement for Ampersand's schema or fusion rules.
