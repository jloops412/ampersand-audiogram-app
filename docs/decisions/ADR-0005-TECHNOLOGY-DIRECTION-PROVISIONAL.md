# ADR-0005: Provisional Technology and Algorithm Direction

- **Status:** Provisional
- **Date:** 2026-08-18
- **Decision owners:** Ampersand product, audio, and platform engineering

## Context

The planning baseline intentionally left most providers open. A deeper expert review of current primary-source documentation, repository maturity, licensing, algorithm behavior, and Ampersand's specific long-form spoken-word workload now supports a narrower technical direction without prematurely declaring every component production-approved.

## Decision

Adopt the following as the **implementation direction for spikes and first promotion attempts**:

### Core deterministic foundation

- controlled FFmpeg build for media execution;
- libebur128 for independent loudness/true-peak analysis and validation;
- controlled libsoxr-enabled resampling when justified;
- independent multiresolution waveform peak generator;
- custom versioned Semantic Map, Processing Router, gain envelope, recipe, and artifact manifests;
- original Ampersand Adaptive Leveler;
- final two-pass loudness master and independent validation.

### First production-candidate lane

- Silero VAD through ONNX Runtime;
- DeepFilterNet3 as the first speech-enhancement candidate;
- WaveSurfer.js as the current waveform/timeline UI lead;
- shared render spec with @napi-rs/canvas/Skia + FFmpeg and libass.

These remain subject to the dependency/model and Audio Lab promotion gates.

### Audio Lab challenger lane

- ClearerVoice enhancement, separation, and super-resolution;
- WhisperX as mature ASR/alignment/diarization composition baseline;
- NVIDIA Parakeet-TDT 0.6B v3 as fast timestamped ASR challenger;
- MOSS-Transcribe-Diarize 0.9B as experimental joint challenger;
- nara_wpe as dereverberation baseline;
- Resemble Enhance and other generative restoration only as opt-in research candidates;
- PANNs or another verified semantic-event baseline.

### Workflow ranking

- Temporal is the current technical lead for customer-facing durable productions;
- Prefect is the preferred Audio Lab workflow candidate;
- Hatchet remains a production challenger and must pass multi-day/database/fault-injection testing;
- ADR-0004 remains formally open until issue #9 completes.

### Editing and interchange

- use an Ampersand-owned deterministic edit model;
- audit Dawn-Cut's bounded MIT core concepts/code before deciding whether to vendor/adapt anything;
- use OpenTimelineIO only at the professional interchange boundary;
- do not fork a complete editor application into the V1 foundation.

## Algorithm direction

### Leveler

The Leveler will be an original, standards-measured, content-aware gain-control system using:

- speech and speaker masks;
- momentary/short-term loudness histories;
- robust per-speaker statistics;
- a comfort band rather than point chasing;
- bounded boost/cut;
- silence/noise/music protection;
- regularized smooth gain trajectories with slope and acceleration limits;
- optional conservative micro-dynamics compression after leveling;
- final independent loudness mastering.

### Denoise routing

- no-op is the default for clean or uncertain material;
- deterministic spectral/wavelet methods provide baselines for stationary noise;
- DeepFilterNet is the first dynamic-speech candidate;
- ClearerVoice challenges difficult cases and super-resolution;
- generative restoration remains regional, opt-in, and Lab-only until identity/naturalness safety is proven;
- speech-plus-music is protected by default.

### AutoEQ

Begin with a conservative speaker-aware long-term spectral-balancing system derived from Ampersand's rights-cleared clean corpus. Use broad low-order corrections, small default limits, separate de-essing/plosive handling, and bypass under low confidence. Do not begin with a generative or opaque EQ model.

## Rejected foundation approaches

- FFmpeg `dynaudnorm` or `speechnorm` as the finished Adaptive Leveler;
- browser AudioContext/MediaRecorder as long-form analysis/export authority;
- universal neural denoise;
- generative restoration by default;
- GPL audiowaveform as a required V1 component when a small independent peak generator is feasible;
- large binary payloads in workflow history;
- provider-native ASR schemas as product-domain contracts;
- ComfyUI or a general editor fork as production architecture;
- dedicated model-serving infrastructure before measured need.

## Consequences

### Positive

- narrows implementation toward the most defensible and attainable stack;
- retains replaceability and evidence gates;
- focuses original engineering on the Leveler/router/semantic/quality layer;
- reduces licensing and integration debt;
- separates stable production candidates from exciting but immature research;
- aligns platform choices with actual failure modes.

### Negative

- requires maintaining separate Lab and production orchestration concerns;
- Temporal may have greater operational/cost complexity than simpler challengers;
- a custom peak generator and Leveler require original engineering;
- model/provider bake-offs remain substantial work;
- provisional leads may still be rejected after fault/listening tests.

## Required follow-up

- use [Technology and Algorithm Direction](../architecture/TECHNOLOGY_AND_ALGORITHM_DIRECTION.md) as detailed authority;
- execute issues #6–#12 under this direction;
- amend issue #9 scoring to treat Temporal as current lead, not selected winner;
- create dedicated promotion ADRs for DeepFilterNet, ASR/diarization, workflow, waveform UI, and rendering after tests;
- update this ADR or supersede it when the first production stack is approved.

## Review triggers

- a candidate fails clean-preservation or fault tests;
- checkpoint/license terms change;
- managed workflow/storage economics are not viable;
- CPU baseline cannot meet product performance goals;
- a newer model materially changes the ASR/enhancement comparison;
- multitrack becomes an active program rather than deferred research.