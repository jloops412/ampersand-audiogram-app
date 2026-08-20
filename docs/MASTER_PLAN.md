# Ampersand V2 Master Plan

**Status:** Accepted planning baseline  
**Last verified:** 2026-08-18  
**Planning horizon:** research foundation through production-ready singletrack V1

## Executive decision

Ampersand should be **refounded in the existing repository**, preserving history and reusable audiogram concepts while replacing the current application architecture.

The project is not planned as an exact clone or reverse-engineered reproduction of Auphonic. It is planned as an independent product that pursues the same broad customer outcome—excellent automatic spoken-word audio—through public standards, permissively usable components, rights-cleared evaluation material, original orchestration, original control logic, and a substantially better user experience.

Development is divided into two cooperating products:

1. **Ampersand Audio Lab** — a reproducible research and evaluation system for audio analysis, candidate processors, recipes, metrics, listening tests, provenance, and quality decisions.
2. **Ampersand Studio** — the customer-facing upload, processing, comparison, editing, export, automation, and content-repurposing experience.

The Lab proves processing choices. The Studio may expose only processors and recipes that have passed the applicable Lab gates.

## Why the existing architecture is not the V2 foundation

The current repository is a useful prototype, but its architecture is not suitable for a durable audio-production platform:

- the Express backend primarily proxies uploads and results to Auphonic;
- one server-wide Auphonic credential pair controls the integration;
- productions, projects, users, recipes, jobs, outputs, and processing steps are not durably modeled;
- the browser decodes source media and renders audiograms by playing the audio in real time, capturing a canvas stream, and recording VP9 WebM;
- browser closure, codec differences, memory limits, and real-time duration constrain export reliability;
- the preview and export renderers contain duplicated drawing behavior;
- the user interface is a fixed sidebar of low-level controls rather than a production-oriented workflow;
- the output canvas is globally fixed at 1080×1080;
- there is no test corpus, objective quality harness, listening-test system, dependency governance, or reproducibility contract.

These observations are documented in [Legacy Salvage Matrix](./research/LEGACY_SALVAGE_MATRIX.md).

## Product thesis

Ampersand should become:

> **One-click automatic mastering when the user wants it; an understandable visual studio when the user needs it.**

Its defensible value should not be a collection of commodity models. It should be the intelligence and product layer that determines:

- what is in the audio;
- who is speaking;
- what defects are present;
- where those defects occur;
- which processor is safest for each region;
- how aggressive processing should be;
- whether processing improved or harmed the material;
- how to let a user understand, compare, override, edit, and reuse the result.

## Target users and initial use cases

The singletrack V1 should prioritize long-form spoken-word recordings such as:

- podcasts and interviews;
- wedding ceremonies and speeches;
- event recordings;
- narration, sermons, and educational content;
- meetings and voice memos;
- phone, voicemail, and audio-guestbook recordings;
- dialogue extracted from simple videos.

These use cases align with Ampersand's practical access to real recordings while creating a broader commercial product than a wedding-specific utility.

## V1 product promise

A user can upload a spoken-word audio or simple video file and receive a reproducible production containing:

- immutable source preservation;
- technical media analysis;
- waveform and semantic timeline data;
- speech activity, speakers, and transcript where supported;
- conservative automatic noise cleanup;
- content-aware voice leveling;
- standards-based final loudness and true-peak mastering;
- original/master A/B playback at the same position;
- MP3 and WAV outputs;
- a processing report explaining material decisions;
- editable regional overrides for approved controls;
- durable progress, retry, and recovery if a worker fails;
- explicit deletion and retention controls.

## Explicit V1 non-goals

The following are deferred until the singletrack foundation has passed its quality and reliability gates:

- exact Auphonic feature parity;
- generative Studio Voice parity;
- full automatic multitrack mixing;
- production mic-bleed removal;
- a general-purpose DAW;
- a CapCut-class video editor;
- broad social publishing integrations;
- mobile-native applications;
- training large foundation models;
- using Auphonic outputs as references, quality targets, evaluation material, or training material without written permission.

## Core product capabilities

### 1. Semantic Audio Map

A versioned timeline that represents, with confidence and provenance:

- speech, music, silence, ambience, and noise;
- speaker identity or anonymous speaker labels;
- loudness measurements and peaks;
- detected events such as coughs or applause where reliable;
- noise, reverberation, clipping, bandwidth, and tonal characteristics;
- transcript words and timing;
- suggested processing regions and edit regions.

The semantic map is persisted and inspectable. It is not discarded as temporary model output.

### 2. Processing Router

A policy engine that chooses an approved processor, strength, and ordering for each applicable region. The router must support:

- no-processing decisions;
- conservative defaults;
- processor compatibility rules;
- model/device availability;
- recipe constraints;
- per-region overrides;
- automatic fallback;
- auditable reasons for decisions.

### 3. Adaptive Leveler

An original Ampersand control system built on standards-based loudness measurements, semantic classification, bounded gain, silence/noise protection, speaker awareness, and smoothed gain envelopes.

Its purpose is to reduce distracting loudness differences without treating silence, breaths, room tone, and music as quiet speech that should be amplified.

### 4. Adaptive Voice EQ

Initially a conservative, interpretable, speaker-aware spectral-balancing system. Learned restoration or EQ models may be evaluated later, but V1 should favor predictable correction and safe limits.

### 5. Quality Controller

A system that records measurements, processor versions, listening-test outcomes, known failure modes, and confidence. It may reject, reduce, or roll back an enhancement when evidence indicates likely harm.

## Program workstreams

### Workstream A — Governance and legal admissibility

Deliverables:

- public-source capability inventory;
- Auphonic research boundary;
- dependency and model license matrix;
- third-party notices process;
- security and privacy requirements;
- release admission checklist.

### Workstream B — Audio quality laboratory

Deliverables:

- rights-cleared reference corpus;
- synthetic degradation generator;
- standardized recipe runner;
- processor plugin contract;
- loudness-matched blinded listening interface;
- objective metrics and reports;
- experiment registry and reproducibility manifest;
- promotion/rejection decisions for candidate processors.

### Workstream C — Semantic analysis

Deliverables:

- media probe and canonical working format;
- speech activity detection;
- transcription, alignment, and diarization evaluation;
- semantic sound classification baseline;
- technical defect analysis;
- semantic map schema and confidence model.

### Workstream D — Audio processing

Deliverables:

- classic deterministic DSP baseline;
- candidate speech enhancement adapters;
- Ampersand Leveler V0/V1;
- adaptive high-pass and hum handling;
- conservative voice EQ;
- final loudness and true-peak mastering;
- processor routing and regional execution.

### Workstream E — Durable media platform

Deliverables:

- resumable direct-to-object-storage upload;
- production, source, recipe, job, step, output, and provenance models;
- durable workflow orchestration;
- idempotent workers and checkpoints;
- progress events;
- cancellation, retry, and failure recovery;
- secure media access and lifecycle deletion.

### Workstream F — Studio experience

Deliverables:

- library and production views;
- waveform and semantic timeline;
- same-position Original/Master comparison;
- transcript and speaker navigation;
- processing report;
- regional override inspector;
- output configuration;
- accessible responsive UX.

### Workstream G — Editing and content reuse

After the mastering foundation:

- deterministic edit-decision model;
- transcript-driven cuts;
- silence/filler/cough suggestions with human confirmation;
- captions and chapters;
- social clip creation;
- server-side deterministic video rendering;
- professional timeline interchange.

## Success criteria

### Audio-quality gate

For each production recipe and supported use-case class:

- listening tests show a statistically and practically meaningful preference over the unprocessed source or approved baseline;
- no critical artifact category exceeds the agreed failure threshold;
- loudness, true peak, clipping, channel behavior, and output validation pass;
- the recipe has documented known limitations and contraindications;
- a clean-input preservation test confirms the recipe does not unnecessarily damage already-good audio.

No single metric may promote a processor automatically. See [Audio Quality Evaluation Plan](./research/AUDIO_QUALITY_EVALUATION_PLAN.md).

### Reliability gate

A one-hour production must:

- upload resumably;
- survive browser closure;
- survive deliberate worker termination after a completed step;
- resume without repeating completed expensive work;
- produce deterministic outputs from the same source, recipe, and engine versions within defined tolerances;
- preserve source immutability;
- expose understandable step-level failures;
- delete source and derived assets according to policy.

### Product gate

A non-expert user must be able to:

- start a production with a sensible preset without understanding LUFS, denoise models, or compressor settings;
- hear Original/Master at the same timeline position;
- understand the major actions Ampersand took;
- reduce, disable, or regionally override approved processing;
- export common outputs;
- recover from failure without re-uploading unnecessarily.

### Commercial-admission gate

Every shipped dependency or model requires:

- verified code license;
- verified checkpoint/model license;
- documented source and version pin;
- attribution and notice requirements;
- redistribution and hosted-use analysis;
- security review;
- maintenance and rollback plan;
- data-use and privacy review;
- a reproducible container or build artifact.

## Architecture principles

1. **Immutable source, derived artifacts only.**
2. **Every production is recipe-driven and reproducible.**
3. **Every expensive step is independently checkpointed and idempotent.**
4. **Browser preview and server export share a render specification, not duplicated ad hoc behavior.**
5. **Analysis is separated from processing.**
6. **The semantic timeline is a durable domain object.**
7. **Providers are replaceable behind narrow interfaces.**
8. **CPU operation must remain possible for the core baseline; GPU acceleration is optional and capability-detected.**
9. **Replit may host or assist the web/control-plane workflow, but heavy media and model workers remain independently deployable.**
10. **Observability includes quality and provenance, not only uptime.**

See [Target Architecture](./architecture/TARGET_ARCHITECTURE.md).

## Current decision state

| Decision | Status |
|---|---|
| Preserve repository history and refound in place | Accepted |
| Audio Lab before major Studio polish | Accepted |
| Independent evaluation; no Auphonic output benchmarking without permission | Accepted |
| Singletrack-first product scope | Accepted |
| Open-source/managed infrastructure before custom infrastructure | Accepted principle |
| Exact storage/auth provider | Open |
| Exact durable workflow engine | Open; fault-injection spike required |
| Primary ASR/diarization stack | Open; comparative spike required |
| Primary denoiser/restoration stack | Open; listening-test bake-off required |
| Waveform UI library | Open; licensing and long-file spike required |
| Deterministic edit core reuse versus original implementation | Open; code audit required |
| Multitrack and social editor substrates | Deferred |

## Principal risks and mitigations

| Risk | Consequence | Mitigation |
|---|---|---|
| Attractive models sound bad on real recordings | Product fails its central promise | Lab-first blind listening; clean-input preservation; regional routing; easy bypass |
| “Open source” checkpoint is commercially restricted | Legal or release blockage | Separate code/model/data license gates; version pinning; legal review |
| Auphonic research violates service terms | Contractual and ethical exposure | Public documentation only; no outputs/derived learnings without written permission |
| Integration sprawl creates a fragile Frankenstein system | High maintenance and debugging cost | One substrate per responsibility; narrow provider contracts; staged adoption |
| Workflow engine loses or repeats expensive work | Cost, delay, user distrust | Three-way fault-injection spike; idempotency keys; step manifests; recovery tests |
| GPU assumptions make the product inaccessible or costly | Deployment failure | CPU baseline; optional GPU profiles; benchmark cost per processed hour |
| Private event audio is mishandled | Severe trust/privacy harm | Explicit consent, isolation, encryption, retention, deletion, no-training policy |
| Clean audio is overprocessed | Audible degradation | No-op option; classifier confidence thresholds; preservation tests; A/B comparison |
| UI polish outruns engine truth | False sense of progress | Quality and reliability phase gates before large UI investment |

## Immediate execution sequence

1. Merge the planning baseline and create implementation issues from the phased roadmap.
2. Create the dependency manifest format and complete checkpoint-level license verification for the first spike candidates.
3. Establish a small rights-cleared corpus with clean references and real-world recordings that may legally be used for development.
4. Build the Audio Lab runner and blinded comparison page without any Auphonic outputs.
5. Implement a deterministic DSP baseline and Ampersand Leveler V0.
6. Run enhancement bake-offs for approved candidates such as DeepFilterNet and ClearerVoice.
7. Run ASR/diarization bake-offs, including CPU and optional managed-GPU profiles.
8. Run the workflow-engine fault-injection spike.
9. Implement one end-to-end cloud production only after the above contracts are stable.
10. Begin the full Studio UI after the first recipe passes audio-quality and reliability gates.

## Definition of planning completeness

Planning is considered sufficient to begin foundation implementation when:

- the capability scope and non-goals are explicit;
- the Auphonic research boundary is accepted;
- the first corpus sources are lawful and documented;
- dependency candidates have code and model license status;
- the quality protocol and promotion thresholds are approved;
- the target architecture identifies durable domain contracts;
- open provider choices have bounded spikes and exit criteria;
- the phased roadmap has issue-sized deliverables;
- security, retention, deletion, and no-training requirements are defined;
- the first implementation phase cannot accidentally lock the product to an unverified model or vendor.

This document is the high-level authority. Detailed implementation decisions belong in the linked research, architecture, roadmap, and ADR documents.