# Ampersand V2 Implementation Execution Plan

**Status:** Active engineering execution authority  
**Last verified:** 2026-08-18  
**Primary objective:** turn the Auphonic public research and independent technical direction into a working singletrack product

## Owner directive

Build the actual Ampersand engine and Studio now.

OpenAI Sites is now the active web/Studio and lightweight control-plane destination. Sites work and engine work proceed together behind versioned contracts; neither may become an excuse to postpone the other. FFmpeg, native DSP, GPU inference, long-running durable workflows, large temporary processing, and authoritative rendering remain externally deployable. Custom-domain/DNS cutover remains deferred until the product is strong.

## Product target for the first working release

A user can upload a spoken-word audio file, run a Smart Master recipe, and receive:

- immutable original preservation;
- technical media analysis;
- a zoomable waveform;
- speech/non-speech and optional speaker/transcript regions;
- conservative automatic cleanup;
- content-aware volume leveling;
- final loudness and true-peak mastering;
- Original/Master same-position comparison;
- an understandable processing report;
- WAV and MP3 downloads;
- a durable saved production that survives browser closure and process restart.

This is the first real product. Audiograms, social clips, advanced editing, multitrack mixing, and generative restoration expand from this foundation.

---

# Architecture derived from the Auphonic research

Auphonic's public material consistently points to a shared semantic-analysis layer feeding specialized processors, followed by internal leveling and final mastering.

Ampersand's independently engineered production graph should therefore be:

```text
SOURCE
  ↓
VALIDATE / PROBE / CANONICALIZE
  ├── waveform peaks
  ├── loudness / true-peak analysis
  ├── speech activity
  ├── optional ASR / alignment / diarization
  └── acoustic / defect analysis
            ↓
      SEMANTIC AUDIO MAP
            ↓
      PROCESSING ROUTER
      ├── no-op / protect
      ├── deterministic filtering
      ├── speech enhancement
      ├── optional dereverb
      └── optional region-specific processing
            ↓
     AMPERSAND ADAPTIVE LEVELER
            ↓
     CONSERVATIVE VOICE EQ / FILTERING
            ↓
     FINAL LOUDNESS + TRUE-PEAK MASTER
            ↓
     OUTPUT VALIDATION + REPORT
      ├── WAV
      ├── MP3
      ├── transcript/captions
      └── analysis/provenance artifacts
```

## What Ampersand owns

- Semantic Audio Map schema and fusion;
- Processing Router policy;
- Adaptive Leveler control law;
- speaker-aware conservative EQ decisions;
- processing recipes;
- quality-control and fallback policy;
- Studio UX and explanations;
- provenance and reproducibility.

## What dependencies execute

- FFmpeg: media I/O, deterministic filters, gain application, encoding, muxing;
- libebur128: loudness and true-peak measurement;
- Silero VAD or admitted equivalent: speech probabilities;
- DeepFilterNet or admitted equivalent: first neural denoise candidate;
- WhisperX / Parakeet / MOSS or admitted equivalent: transcription and timing;
- workflow/object-storage providers: durable execution and assets;
- WaveSurfer.js or selected equivalent: browser waveform presentation.

---

# Build lanes and issue ownership

Agents may work in parallel only where contracts are already stable. Every issue must preserve provider-neutral domain objects.

## Lane 1 — Repository and core contracts

### Goals

- refound the repository without extending the legacy architecture;
- create the V2 workspace structure;
- define typed/versioned schemas;
- create a local CLI and fixture-driven development path;
- establish model/dependency manifests.

### Issues

- #3 — preserve legacy and establish V2 workspace;
- #12 — dependency/model manifests, SBOM, notices, allowlist;
- #21 — core contracts and local pipeline.

### Required first schemas

- `AssetManifest`
- `MediaProbe`
- `Production`
- `ProductionRun`
- `JobStep`
- `RecipeVersion`
- `SemanticMap`
- `SemanticRegion`
- `ProcessingPlan`
- `ProcessingRegion`
- `GainEnvelope`
- `ProcessingReport`
- `OutputManifest`
- `ModelManifest`

No React state object or third-party model response becomes the permanent project format.

---

## Lane 2 — Deterministic media baseline

### Goals

Build a complete CPU-only processing baseline before neural-model selection.

### Components

- FFprobe validation;
- canonical working audio;
- waveform peak pyramid;
- libebur128 analysis;
- channel/sample-rate handling;
- high-pass and hum treatment;
- clipping and silence diagnostics;
- two-pass final loudness normalization;
- true-peak validation;
- WAV and MP3 outputs;
- deterministic processing report.

### Issues

- #6 — deterministic DSP and Adaptive Leveler V0;
- #21 — local engine foundation;
- #24 — durable singletrack processing vertical slice.

### Exit artifact

A CLI command can process a fixture without any neural model and produce:

```text
source manifest
probe.json
waveform peaks
loudness-before.json
semantic-map-v0.json
processing-plan.json
gain-envelope.json
master.wav
master.mp3
loudness-after.json
processing-report.json
```

---

## Lane 3 — Semantic Audio Map V0

### Goals

Create the durable shared analysis layer that every intelligent processor uses.

### V0 observations

- speech probability;
- silence/non-speech;
- momentary and short-term loudness;
- sample and true-peak risk;
- active speaker when available;
- transcript word/segment when available;
- probable music/protected content;
- noise/defect flags;
- provider and confidence;
- half-open integer-microsecond regions.

### Fusion rules

- preserve raw provider result separately;
- normalize into Ampersand schema;
- represent conflicting evidence rather than silently choosing;
- allow absent transcript/diarization;
- keep mastering functional when ASR fails;
- derive processing eligibility from confidence thresholds;
- make no-op/protected regions explicit.

### Issues

- #8 — ASR/alignment/diarization/semantics providers;
- #22 — Semantic Audio Map V0 implementation.

---

## Lane 4 — Adaptive Leveler V0/V1

### Goals

Build the original Ampersand feature most responsible for automatic-mix quality.

### Inputs

- speech probability;
- active speaker;
- momentary loudness;
- short-term loudness;
- music/noise/silence confidence;
- overlap confidence;
- peak risk;
- recipe limits.

### Control behavior

- estimate robust per-speaker speech level;
- establish a comfort band rather than chase one exact value;
- clamp maximum boost and attenuation;
- freeze or return toward unity during silence/noise/uncertainty;
- protect music and emotional pauses;
- smooth gain velocity and acceleration;
- crossfade region transitions;
- keep short-term compression separate;
- save the sample-accurate gain envelope;
- explain significant corrections in the report.

### Test fixtures

- level-stepped single speaker;
- quiet/loud multiple speakers;
- breath and silence gaps;
- HVAC under speech;
- speech over music;
- applause/laughter;
- already mastered clean source;
- one-hour long-form drift.

### Issue

- #6 — deterministic mastering and Adaptive Leveler V0.

---

## Lane 5 — Enhancement and router

### Goals

Add specialized processors without creating a universal “enhance everything” switch.

### First admitted candidate

DeepFilterNet should be the first neural-denoise adapter attempted after exact checkpoint/license verification.

### Challenger candidates

- selected ClearerVoice enhancement models;
- RNNoise baseline;
- nara_wpe dereverb in bounded far-field/multichannel cases;
- generative restoration only in the Lab.

### Router V0 decisions

```text
clean / uncertain / protected
→ no-op

speech + ordinary changing background noise
→ admitted speech enhancer at conservative strength

stationary hum / rumble
→ deterministic filters

music or speech-over-music
→ protect or use explicitly approved preservation path

low-bandwidth speech
→ clean first; optional Lab-only super-resolution

unsupported content
→ bypass with warning
```

### Issues

- #7 — enhancement adapters and first admitted denoise path;
- #23 — Processing Router V0.

---

## Lane 6 — Durable singletrack engine

### Goals

Convert the local processing graph into a production service.

### Requirements

- immutable source upload;
- object-addressed artifacts;
- versioned recipe;
- independently retryable steps;
- idempotency keys;
- cancellation;
- progress events;
- worker restart/recovery;
- no repeat of completed expensive steps;
- CPU baseline and optional GPU capability;
- exact engine/model/dependency provenance;
- output and deletion lifecycle.

### Issues

- #9 — workflow-engine selection and implementation;
- #10 — upload/storage/isolation/deletion;
- #24 — durable singletrack engine vertical slice;
- #13 — one-hour end-to-end proof.

The workflow/provider may remain simple initially, but the product must work. Do not spend weeks comparing platforms before the local graph and step contracts exist.

---

## Lane 7 — Ampersand Studio MVP

### Goals

Put the real engine into an approachable customer workflow.

### Required pages/states

#### Library

- productions;
- title/source/duration;
- recipe;
- status and failure state;
- created/completed dates;
- delete/download actions.

#### New Production

- large upload/drop area;
- preset-first recipe selection;
- concise controls:
  - level voices;
  - clean noise;
  - normalize loudness;
  - transcribe;
- advanced settings hidden by default.

#### Processing

- durable step list;
- progress and elapsed time;
- safe browser closure/reopen message;
- actionable failure and retry.

#### Production Studio

- waveform;
- semantic regions;
- transcript/speakers when available;
- Original/Master same-position toggle;
- processing summary;
- regional bypass/strength controls;
- output downloads.

### Issues

- #11 — waveform and edit-core contracts;
- #25 — Studio MVP;
- #26 — A/B comparison and processing report.

---

## Lane 8 — Deterministic audiogram migration

### Goals

Preserve the useful legacy waveform/audiogram product value without keeping browser real-time rendering.

### V1 rendering

- shared render specification;
- arbitrary aspect ratio;
- background image/color;
- migrated waveform styles;
- word/cue captions;
- brand presets;
- browser preview;
- deterministic server rendering;
- H.264 MP4 plus approved outputs;
- FFmpeg/libass caption burn-in;
- output independent of tab lifetime.

### Issue

- #27 — deterministic audiogram renderer and legacy style migration.

This follows the working mastering Studio. It does not precede the engine.

---

# Execution order

## Immediate start

Agents should begin these in parallel where dependencies permit:

1. **#3** V2 workspace/refoundation;
2. **#17** Sites product/control-plane foundation;
3. **#18** durable D1/R2/external-worker boundary;
4. **#12** dependency/model manifest gate;
5. **#21** core engine contracts and local CLI;
6. **#22** Semantic Audio Map V0 schema/fusion;
7. **#6** deterministic mastering and Leveler V0 using fixture inputs;
8. **#4/#5** minimum fixture corpus and listening/regression harness.

## Next integration wave

7. **#7** enhancement candidate adapters and tests;
8. **#8** ASR/diarization candidate normalization;
9. **#23** Processing Router V0;
10. **#9/#10** durable workflow and storage lifecycle;
11. **#24** durable singletrack engine vertical slice;
12. **#25/#26** Studio MVP, A/B, and report;
13. **#13** one-hour end-to-end product proof.

## After the real product works

14. **#27** deterministic audiogram migration;
15. transcript-driven edits and automatic cut suggestions;
16. publishing automation;
17. custom-domain connection and retirement of the legacy Google-hosted surface;
18. multitrack and advanced restoration research.

---

# Definition of the first publishable Ampersand build

The build is ready for user testing when all are true:

- an upload becomes a durable Production;
- one Smart Spoken Word recipe completes end to end;
- source remains immutable;
- waveform and basic semantic regions display;
- Leveler gain envelope is applied and inspectable;
- admitted cleanup is conservative and bypassable;
- final output meets loudness/true-peak target;
- Original/Master same-position comparison works;
- WAV and MP3 download;
- report identifies processing steps and versions;
- browser closure does not lose the job;
- failure and retry are understandable;
- one-hour fixture completes successfully;
- clean-input preservation passes;
- no legacy Auphonic dependency is involved.

## Deployment note

The Sites product/control plane is established during implementation. Connect the domain and retire the legacy Google-hosted surface only after the release-readiness criteria above are satisfied.
