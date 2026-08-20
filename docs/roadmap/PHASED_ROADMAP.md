# Ampersand V2 Phased Roadmap

**Status:** Accepted program sequence; dates intentionally omitted until foundational spikes establish scope and throughput  
**Last verified:** 2026-08-18

## Roadmap principle

Phases are gated by evidence, not calendar optimism. A later phase may begin exploratory work, but it cannot become the main development focus until the prior phase's exit criteria are met.

The roadmap deliberately prioritizes:

1. legal/research boundaries;
2. audio-quality truth;
3. durable processing reliability;
4. customer-facing polish;
5. editing, video, automation, and multitrack expansion.

## Phase 0 — Planning authority and governance

### Goal

Make the project safe for multiple agents and contributors by establishing one durable source of truth.

### Deliverables

- master plan;
- target architecture;
- Auphonic research boundary;
- dependency/model license matrix;
- audio-quality evaluation plan;
- security/privacy requirements;
- legacy salvage matrix;
- ADR set;
- source register;
- issue-sized implementation backlog;
- draft planning pull request.

### Exit criteria

- documentation is internally consistent;
- Auphonic output benchmarking is explicitly prohibited absent written permission;
- current candidate versus selected dependency language is clear;
- first spikes have measurable exit criteria;
- legacy code is labeled and preserved;
- implementation issues link back to planning documents.

### Non-goals

- production code refactor;
- UI redesign implementation;
- model selection;
- cloud-provider lock-in.

---

## Phase 1 — Rights-cleared Audio Lab foundation

### Goal

Create the machinery that can tell us whether a processing idea actually improves audio.

### Deliverables

#### Corpus governance

- corpus manifest schema;
- rights/consent record schema;
- clean source partition;
- deterministic degradation manifest;
- development/validation/hidden-test partitions;
- access and retention rules;
- initial 10–20 clean clips and 5–10 real-world clips.

#### Experiment runner

- common `AudioProcessor` adapter;
- canonical input/output format handling;
- processor/model/container manifest capture;
- deterministic seed/provenance handling;
- batch experiment command;
- output hashing;
- loudness-matched listening assets;
- metric plugin contract.

#### Listening harness

- opaque randomized candidate IDs;
- MUSHRA-inspired comparison mode;
- P.835-style SIG/BAK/OVRL mode;
- pairwise preference mode;
- clean-preservation mode;
- comments/artifact taxonomy;
- listener/session integrity checks;
- report export.

#### Diagnostics

- current BS.1770/R128 loudness and true peak;
- clipping and channel validation;
- ViSQOL integration for applicable reference cases;
- SNR/SI-SDR or other approved full-reference diagnostics;
- runtime, memory, and cost telemetry.

### Exit criteria

- one command reproduces all outputs for a corpus version and experiment manifest;
- a listener can complete a blinded test without seeing processor names;
- loudness matching is verified;
- source, candidate, and report hashes are stored;
- no Auphonic service/output appears anywhere in the Lab;
- deletion removes a test item and its derivatives according to policy;
- a pilot reveals usable variance and informs promotion-test sample sizes.

### Non-goals

- declaring the best denoiser;
- customer accounts;
- polished Studio UX;
- production customer media.

---

## Phase 2 — Deterministic baseline and Ampersand Leveler V0

### Goal

Build an understandable baseline that does not require a large neural model and establishes the minimum quality every future candidate must beat or complement.

### Deliverables

- media probe and validation;
- canonical lossless working format;
- waveform/peak generation baseline;
- libebur128/validated loudness measurement;
- high-pass, hum/notch, and safe filtering baseline;
- conservative static/noise baseline where appropriate;
- two-pass final loudness normalization and true-peak validation;
- Silero VAD or approved equivalent spike;
- semantic distinction among speech, probable non-speech, and protected silence;
- Leveler V0:
  - target comfort region;
  - maximum boost/cut;
  - silence/noise protection;
  - attack/release smoothing;
  - transition/crossfade policy;
  - optional short-term compression;
  - gain-envelope artifact output;
- clean-preservation tests;
- processing report.

### Leveler V0 experiments

Test independently:

- one speaker with level steps;
- two speakers at different levels;
- noise-only gaps;
- breaths and quiet speech;
- speech over music;
- sudden laughter/applause;
- long-form gain drift;
- already mastered audio.

### Exit criteria

- baseline passes loudness/peak validation;
- Leveler does not boost classified silence/noise beyond defined safety limits;
- gain envelope is smooth and inspectable;
- clean-input preservation pilot passes;
- baseline is reproducible on CPU;
- processing report explains every gain/filter stage;
- baseline performance and cost per processed hour are recorded.

### Non-goals

- proprietary model parity;
- advanced AutoEQ;
- generative restoration;
- multitrack.

---

## Phase 3 — Candidate analysis and enhancement bake-offs

### Goal

Select the first production-admissible analysis and enhancement components through independent evidence.

### Lane A — ASR, alignment, diarization

Candidates may include:

- WhisperX composition;
- MOSS-Transcribe-Diarize 0.9B;
- a simpler Whisper/faster-whisper plus separate VAD path;
- other fully verified alternatives.

Evaluate:

- WER/CER;
- word timing;
- diarization error;
- speaker-attributed WER;
- overlap behavior;
- language/accent coverage;
- CPU/GPU memory and real-time factor;
- long-file reliability;
- model/checkpoint terms.

Output is normalized into Ampersand's schema; no provider-native schema becomes the product model.

### Lane B — speech enhancement

High-priority candidates:

- DeepFilterNet;
- cleared ClearerVoice enhancement models;
- deterministic/no-op baseline;
- optional RNNoise baseline.

Evaluate by degradation/use case:

- stationary noise;
- dynamic noise;
- reverb;
- speech plus music;
- clean preservation;
- phone/narrow-band material;
- abrupt environment changes;
- long continuity.

### Lane C — restoration and super-resolution

Research-only candidates may include:

- ClearerVoice super-resolution;
- Resemble Enhance;
- VoiceRestore;
- newer open restoration research.

No restoration candidate becomes a V1 default merely because it can make dramatic demos. Voice identity, hallucinated detail, naturalness, and clean preservation are critical gates.

### Lane D — semantic events

Compare a lightweight semantic baseline such as PANNs with rules/VAD/transcript signals for:

- speech;
- music;
- applause;
- cough/respiratory sounds;
- crowd/traffic/noise;
- unsupported/non-speech safety routing.

### Exit criteria

For each promoted candidate:

- code and exact checkpoint admission record complete;
- hidden-test listening passes for a bounded use-case;
- clean-preservation passes;
- critical artifacts are below threshold;
- CPU/GPU profile and cost are viable;
- routing conditions and contraindications are documented;
- fallback/no-op path exists;
- promotion report and ADR merged.

A phase can exit with no promoted neural processor if the deterministic baseline is safer; the roadmap must not force adoption.

---

## Phase 4 — Durable platform and provider-selection spikes

### Goal

Prove that long media can be uploaded, processed, resumed, observed, and deleted reliably.

### Parallel spikes

#### Storage/Auth/Data

Compare a managed composition such as Supabase against other Postgres/S3-compatible options.

Test:

- direct resumable upload;
- checksums;
- workspace isolation/RLS;
- object authorization;
- lifecycle deletion;
- export/exit path;
- backup behavior;
- costs and egress;
- Replit/control-plane integration.

#### Workflow engine

Compare Hatchet, Temporal, and Prefect using the same media DAG.

Fault-injection scenarios:

- kill worker during an expensive step;
- kill orchestrator/control service;
- duplicate delivery/event;
- timeout and retry;
- cancel during upload/processing;
- corrupt or missing intermediate;
- workflow-engine restart after days of operation;
- large step count and long duration;
- concurrency/rate limiting;
- invalid credentials/model unavailable.

#### Waveform/timeline

Compare WaveSurfer and Peaks or a minimal custom approach.

Test:

- 1–3 hour sources;
- precomputed peaks;
- zoom and segment editing;
- sample/time alignment;
- multichannel display;
- keyboard and screen-reader behavior;
- mobile performance;
- license/bundle constraints.

### End-to-end architecture proof

Run one one-hour rights-cleared production through:

- resumable upload;
- immutable source manifest;
- probe;
- waveform;
- loudness;
- VAD/ASR;
- one approved enhancement;
- Leveler;
- final master;
- WAV and MP3 outputs;
- progress events;
- same-position A/B playback;
- deliberate failure and resume;
- complete deletion.

### Exit criteria

- provider ADRs accepted;
- no expensive completed step repeats after approved recovery test;
- idempotency and duplicate event tests pass;
- object isolation and deletion pass;
- one-hour run produces valid outputs;
- cost and resource profiles recorded;
- local/control-plane and worker deployment boundaries proven.

### Non-goals

- full customer Studio;
- broad scale;
- social-video rendering.

---

## Phase 5 — Singletrack Studio alpha

### Goal

Deliver a complete internal/customer-adjacent spoken-word mastering workflow around one or more approved recipes.

### Product surface

- authentication and workspace;
- production library;
- resumable upload;
- preset-first new-production flow;
- durable progress and step status;
- waveform/semantic timeline;
- transcript and speaker navigation where supported;
- same-position Original/Master A/B;
- processing report;
- contextual regional inspector;
- user bypass/strength controls approved by recipe;
- MP3/WAV outputs;
- retention/deletion controls;
- responsive accessible shell.

### Initial recipes

Candidates, subject to Lab approval:

- Smart Spoken Word;
- Clean Podcast/Interview;
- Wedding Ceremony/Speeches;
- Phone/Voicemail/Guestbook;
- Loudness Only;
- Dialogue Cleanup.

Each recipe has a support matrix and safe fallback.

### Exit criteria

- internal users can process representative full-length material without engineering intervention;
- every default recipe has a promotion report;
- errors identify failed steps and next actions;
- source/master/output provenance is downloadable or inspectable;
- A/B controls are understandable to non-experts;
- accessibility smoke test passes;
- security/privacy release checklist passes for alpha scope;
- no legacy Auphonic path or browser real-time renderer is used.

---

## Phase 6 — Singletrack private beta and production hardening

### Goal

Validate the product with real users and production-like volume while preserving audio-quality discipline.

### Deliverables

- onboarding and first-run guidance;
- user feedback tied to recipe/model versions;
- optional user artifact reports;
- operational dashboards and alerts;
- quota, abuse, and cost controls;
- model cache/cold-start optimization;
- output naming/metadata/chapters;
- API/webhook foundation where justified;
- support workflow with explicit content-access permission;
- backup/restore and incident-response exercises;
- release SBOM and third-party notices;
- recipe rollback.

### Exit criteria

- reliability service-level objective achieved over defined beta window;
- quality regressions remain within threshold;
- cost per processed hour supports business model;
- support can diagnose failures without routine access to private media;
- deletion/retention behavior verified in production-like environment;
- legal/privacy/security launch review complete;
- public claims are evidence-backed and do not reference prohibited Auphonic comparisons.

---

## Phase 7 — Deterministic editing, captions, and audiograms

### Goal

Turn mastered/transcribed content into editable and reusable outputs without becoming a general-purpose DAW/video editor.

### Deliverables

- deterministic edit-core decision;
- transcript-driven cuts;
- silence/filler/cough suggestions with reversible confirmation;
- word/timeline round-trip tests;
- chapters and caption exports;
- render specification shared by browser preview and server export;
- migrated waveform styles from the legacy prototype;
- 1:1, 4:5, 9:16, 16:9, and custom output specs;
- H.264 MP4 and approved alternatives;
- brand templates;
- clip creation from selected transcript ranges;
- professional timeline export via OpenTimelineIO where reliable.

### Exit criteria

- save/reopen/undo/render are deterministic;
- transcript and render remain synchronized;
- preview/export visual parity passes;
- long-form render is faster than or independent of real-time playback where practical;
- captions meet accessibility/readability tests;
- output codecs play on target platforms;
- legacy browser MediaRecorder renderer can be removed.

---

## Phase 8 — Automation, publishing, and ecosystem

### Goal

Make Ampersand programmable and operationally useful beyond one-off web uploads.

Potential deliverables:

- stable production API;
- webhooks;
- batch processing;
- watch folders;
- generic file destinations through an approved rclone or provider abstraction;
- cloud-drive imports;
- reusable brand kits and organization presets;
- external transcript/EDL import/export;
- customer portal/embed workflows.

Each integration requires separate credential, provider-term, privacy, and maintenance review.

---

## Phase 9 — Multitrack and advanced audio R&D

### Goal

Extend proven singletrack intelligence to joint-track analysis and mixing.

Research areas:

- per-track VAD and speaker ownership;
- cross-track alignment/drift;
- automatic track/speaker leveling;
- adaptive gating/expansion;
- foreground/background/music classification;
- ducking;
- per-track pan/gain;
- stem export;
- mic bleed/crosstalk removal;
- dereverberation;
- advanced speaker-aware AutoEQ;
- generative voice restoration.

### Entry criteria

- singletrack product is reliable and economically viable;
- multitrack corpus and consent are available;
- editing/domain model supports tracks without rewrite;
- GPU costs and model terms are understood;
- multitrack work does not delay critical singletrack quality or support work.

### Exit criteria

Defined later through a dedicated multitrack research plan. No assumption of Auphonic parity is made.

## Cross-phase engineering standards

Every phase follows:

- typed/versioned schemas;
- immutable manifests and hashes;
- tests before migration of legacy behavior;
- dependency/model admission gates;
- no production user data in development or Lab;
- least-privilege media access;
- documented CPU/GPU/cost profile;
- quality and clean-preservation regression;
- accessible UI requirements;
- ADRs for material decisions;
- source register updates.

## Stop/reassess conditions

Pause or narrow the project if:

- no candidate including deterministic baselines can pass meaningful listening tests;
- processing cost cannot support a viable service;
- commercially admissible model options disappear;
- privacy/provider terms conflict with expected customer trust;
- workflow reliability cannot be proven without disproportionate operations;
- integration debt starts exceeding the value of adopted components;
- customer research indicates mastering alone does not solve a valuable problem.

A reassessment may produce a narrower product—such as a private event-audio processor, a desktop/local tool, or an audiogram/content-repurposing product—rather than forcing the original scope.