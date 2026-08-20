# Technology and Algorithm Direction

**Status:** Expert technical recommendation; selections marked provisional remain subject to the documented spikes and admission gates  
**Last verified:** 2026-08-18

## Executive recommendation

Ampersand should **not** attempt to invent a codec stack, audio editor, workflow platform, transcription foundation model, general denoiser, or GPU-serving framework.

It should own five tightly defined capabilities:

1. **Semantic Audio Map** — a normalized, inspectable timeline of speech, speakers, music, noise, silence, loudness, defects, transcript, and confidence.
2. **Processing Router** — independently developed policy that decides what should be processed, by which admitted processor, at what strength, and when the safest decision is no processing.
3. **Adaptive Leveler** — Ampersand's original content-aware gain-control system.
4. **Conservative Speaker-Aware EQ** — broad, interpretable tonal correction built from rights-cleared reference statistics.
5. **Quality Controller** — clean-input preservation, artifact detection, listening-test evidence, provenance, and rollback.

Everything else should be built from standards, controlled native tools, narrow provider interfaces, and carefully admitted open-source components.

## Recommended stack by responsibility

| Responsibility | Current technical direction | Status |
|---|---|---|
| Media probe, decode, encode, filtering, muxing | Controlled **FFmpeg** build | **Core recommendation** |
| Loudness and true-peak measurement | **libebur128** plus cross-check against FFmpeg/standards fixtures | **Core recommendation** |
| Sample-rate conversion | FFmpeg `aresample` with a controlled **libsoxr** build when quality/profile justifies it | **Provisional** |
| Speech activity | **Silero VAD through ONNX Runtime** | **First production candidate** |
| Initial speech denoise | **DeepFilterNet3** adapter | **First production candidate; Lab promotion required** |
| Difficult enhancement, separation, super-resolution | **ClearerVoice-Studio** models | **High-priority Lab challengers** |
| Stable transcription/alignment composition | **WhisperX + approved diarization pipeline** | **Mature baseline candidate** |
| Fast timestamp-focused ASR | **NVIDIA Parakeet-TDT 0.6B v3** plus separate diarization | **High-priority challenger** |
| Joint ASR/diarization/events | **MOSS-Transcribe-Diarize 0.9B** | **Experimental challenger** |
| Dereverberation baseline | **nara_wpe** | **Lab only; especially multichannel/far-field** |
| Production durable workflows | **Temporal** currently leads | **Provisional lead; ADR remains open** |
| Audio Lab experiment orchestration | **Prefect** | **Preferred Lab candidate** |
| Simpler workflow challenger | **Hatchet** | **Challenger; long-run fault test mandatory** |
| Durable data | Postgres-compatible database | **Accepted interface** |
| Media objects | S3-compatible private object storage | **Accepted interface** |
| Resumable uploads | TUS-compatible direct upload with a mature UI client such as Uppy | **Accepted direction; provider open** |
| Browser waveform/timeline | **WaveSurfer.js** with server-precomputed multiresolution peaks | **Current lead; spike required** |
| Server visual rendering | Shared render spec + **@napi-rs/canvas/Skia** frames + FFmpeg | **Provisional recommendation** |
| Final caption burn-in | FFmpeg with **libass** | **Strong recommendation** |
| Professional timeline interchange | **OpenTimelineIO** at the export boundary | **Deferred recommendation** |
| Deterministic edit-domain reference | Audit **Dawn-Cut** core concepts; adapt only a bounded verified core if justified | **Architecture/reference candidate** |

## 1. Media and deterministic DSP foundation

### FFmpeg is the executor, not the intelligence

Use FFmpeg for:

- probing and validating containers/codecs;
- decoding to canonical working PCM;
- channel mapping;
- resampling;
- deterministic filters;
- gain-envelope application;
- final loudness processing;
- output encoding/muxing;
- audio/video rendering;
- subtitles through libass.

Official filter documentation exposes useful primitives including:

- `loudnorm`;
- `afftdn` and `afwtdn`;
- `anlmdn`;
- `arnndn`;
- `adeclip`;
- `deesser`;
- `adrc`;
- `adynamicequalizer`;
- compressors, limiters, gates, silence detection, and sidechain processors.

Primary source:

- [FFmpeg Audio Filters](https://ffmpeg.org/ffmpeg-filters.html)

### Do not use FFmpeg's automatic level filters as Ampersand's main Leveler

`dynaudnorm` and `speechnorm` are useful deterministic comparison baselines. They are not semantic, speaker-aware automatic mixing systems.

- `dynaudnorm` creates section-based peak/gain normalization while retaining dynamics inside each section.
- `speechnorm` operates on half-cycles and peak/RMS targets.

They do not inherently understand speakers, music, silence, breaths, room tone, uncertain regions, or content ownership.

Ampersand may include them in Audio Lab baselines, but the production Leveler must be original.

### Final mastering order

The recommended final stage is:

```text
processed mix
  ↓
program loudness measurement
  ↓
two-pass loudness target calculation/application
  ↓
true-peak limit/validation
  ↓
independent libebur128 and output validation
```

`loudnorm` is appropriate for final global mastering, not for replacing internal speaker/content leveling.

### Measurement

Use `libebur128` as an independent standards-oriented measurement library for:

- momentary loudness;
- short-term loudness;
- integrated loudness;
- loudness range;
- true peak;
- real-time history/window measurements.

Primary source:

- [libebur128](https://github.com/jiixyj/libebur128)

Cross-check against:

- current [ITU-R BS.1770](https://www.itu.int/rec/R-REC-BS.1770/en);
- [EBU R128](https://tech.ebu.ch/publications/r128);
- FFmpeg outputs;
- controlled test vectors.

Do not make Ampersand's Leveler dependent on one library's undocumented edge behavior.

## 2. Canonical audio representation

### Source preservation

- Preserve original uploaded bytes and checksum.
- Never overwrite the source.
- Store probe metadata and validation results separately.

### Working format

For algorithmic work, use a documented canonical representation such as:

- floating-point PCM;
- stable internal sample rate selected by processor capability, commonly 48 kHz for full-band production;
- original channel layout preserved until an explicit mixdown step;
- integer microsecond or rational timeline positions;
- half-open time intervals `[start, end)`.

Do not repeatedly encode/decode lossy intermediates.

### Resampling

Use one controlled resampling path per recipe. `libsoxr` is a strong high-quality configurable resampler, but it is LGPL and must be included in the approved FFmpeg/native-build manifest.

Primary source:

- [libsoxr](https://github.com/chirlu/soxr)

## 3. Ampersand Semantic Audio Map

The Semantic Map is more important than any single model.

It should normalize observations from multiple providers into versioned records:

```text
[start_us, end_us)
  content:
    speech_probability
    music_probability
    ambience_probability
    silence_probability
  speaker:
    anonymous_id
    confidence
  acoustics:
    loudness_m
    loudness_s
    peak
    noise_class
    reverb_estimate
    bandwidth_estimate
    clipping_probability
    tonal_features
  transcript:
    words
    timing
    confidence
  provenance:
    provider
    model_hash
    code_version
```

Provider-native outputs remain available for audit, but product behavior consumes Ampersand's schema.

### Confidence and conflict

The map must allow:

- overlapping observations;
- contradictory providers;
- unknown/uncertain regions;
- partial availability when transcription or diarization fails;
- speaker overlap;
- no-op routing under low confidence.

Do not flatten uncertainty into one false categorical label.

## 4. Speech activity, ASR, and diarization

### Silero VAD — recommended baseline

Silero VAD is small, CPU-friendly, supports ONNX/JIT deployment, and is well suited to an inexpensive first-pass speech mask.

Primary source:

- [Silero VAD](https://github.com/snakers4/silero-vad)

Recommended use:

- run early on a downsampled mono analysis stream;
- preserve original timing through an explicit sample/time transform;
- use hysteresis and minimum speech/gap durations;
- retain probabilities, not only binary intervals;
- do not let VAD alone decide whether quiet material should be deleted.

### Three-way ASR/diarization bake-off

#### Candidate A — WhisperX composition

Strengths:

- established integration;
- batched faster-whisper transcription;
- VAD preprocessing;
- wav2vec2 forced alignment;
- word-level timestamps;
- pyannote diarization integration.

Risks:

- multiple independently versioned model/dependency contracts;
- forced-alignment model/language coverage;
- gated diarization and attribution terms;
- overlap errors;
- GPU/runtime complexity.

Primary source:

- [WhisperX](https://github.com/m-bain/whisperX)

#### Candidate B — NVIDIA Parakeet-TDT 0.6B v3

Strengths:

- fast ASR architecture;
- built-in word/segment timestamps;
- punctuation/capitalization;
- long-form handling;
- permissive CC BY 4.0 model terms reported by the official model card.

Limitations:

- ASR rather than a complete diarization solution;
- 16 kHz mono input expectation;
- primarily European-language scope;
- GPU-optimized runtime.

Primary source:

- [Parakeet-TDT 0.6B v3 model card](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3)

#### Candidate C — MOSS-Transcribe-Diarize 0.9B

Strengths:

- joint transcription, speaker diarization, timestamps, and acoustic-event awareness;
- 50+ languages reported;
- potentially simpler unified inference/output.

Risks:

- very new release;
- less operational evidence;
- checkpoint/runtime maturity must be proven;
- long-form, overlap, and CPU behavior require independent testing.

Primary source:

- [MOSS-Transcribe-Diarize](https://github.com/OpenMOSS/MOSS-Transcribe-Diarize)

### Selection rule

Do not select one stack globally.

The likely V1 outcome may be:

- one stable default;
- one fast GPU profile;
- one CPU/degraded fallback;
- mastering continues even when transcript/diarization fails.

Score separately:

- WER/CER;
- word timing error;
- diarization error rate;
- speaker-attributed WER;
- overlap-specific errors;
- confidence calibration;
- long-file stability;
- CPU/GPU real-time factor and cost.

## 5. Speech enhancement and restoration

### Production-first candidate — DeepFilterNet3

DeepFilterNet is the first model Ampersand should attempt to promote for dynamic speech noise because it is designed for full-band 48 kHz enhancement with relatively low computational complexity and a permissive code license.

Primary source:

- [DeepFilterNet](https://github.com/Rikorose/DeepFilterNet)

Required controls around the model:

- exact checkpoint hash/license;
- attenuation/strength cap;
- wet/dry mixing;
- speech-only routing;
- crossfades at region boundaries;
- clean-input bypass;
- removed-noise or residual audit output where technically feasible;
- long-form chunk overlap/state tests;
- CPU real-time factor.

DeepFilterNet must not be applied universally to music or already-clean material.

### High-priority challenger — ClearerVoice-Studio

ClearerVoice provides candidates for:

- 16/48 kHz enhancement;
- speech separation;
- speech super-resolution to 48 kHz;
- target-speaker extraction.

Primary source:

- [ClearerVoice-Studio](https://github.com/modelscope/ClearerVoice-Studio)

Recommended Lab use:

- compare 48 kHz enhancement against DeepFilterNet by noise class;
- evaluate super-resolution only after cleanup, not before;
- test speech-plus-music and difficult noise separately;
- inspect target-speaker extraction for future multitrack/mic ownership research;
- admit checkpoints one by one.

Do not treat the Apache repository license as proof of every model artifact's commercial terms.

### Dereverberation — nara_wpe

Weighted Prediction Error is a valuable classical dereverberation baseline, particularly for multichannel/far-field material.

Primary source:

- [nara_wpe](https://github.com/fgnt/nara_wpe)

Recommended disposition:

- Audio Lab first;
- strongest emphasis on multichannel material;
- compare dereverb strength against speech naturalness and ambience preservation;
- never make aggressive dereverb a default for music or emotionally important room sound;
- crossfade and regionalize any accepted use.

### Generative restoration

Resemble Enhance is a legitimate research candidate because its enhancer targets distortion restoration and bandwidth extension rather than only noise subtraction.

Primary source:

- [Resemble Enhance](https://github.com/resemble-ai/resemble-enhance)

Disposition:

- Lab only;
- region-specific;
- explicit user opt-in if it ever ships;
- test voice-identity, emotion, pronunciation, and hallucinated spectral detail;
- never use as the V1 default;
- retain the unprocessed and conventionally processed alternatives.

## 6. Processing Router

The router should implement a conservative policy graph rather than a single “Enhance” switch.

### Initial decision policy

```text
clean + confident
  → no denoise

stationary broadband noise
  → deterministic afftdn/afwtdn baseline OR approved model at low strength

dynamic speech noise
  → DeepFilterNet candidate

severe/difficult speech noise
  → ClearerVoice challenger if approved

narrow-band/telephone speech
  → cleanup first
  → optional approved super-resolution second

speech + foreground music
  → protect/no-op by default
  → separation only when explicitly requested and approved

strong reverb
  → warning
  → Lab-approved regional dereverb only

generative restoration
  → explicit opt-in, selected regions only

low confidence
  → no-op or deterministic minimal processing
```

### Router inputs

- content probabilities;
- VAD/speaker regions;
- noise stationarity and SNR estimate;
- reverb estimate;
- clipping/bandwidth estimates;
- music overlap;
- processor admission and hardware availability;
- recipe constraints;
- previous step warnings;
- user overrides.

### Router output

Every region decision includes:

- processor/model manifest;
- parameters;
- wet/dry and attenuation caps;
- reason;
- confidence;
- transition policy;
- fallback;
- whether it was automatic or user-selected.

[Processing Router V0](./PROCESSING_ROUTER_V0.md) now implements this output as a deterministic shadow plan with strict
settings, safe protect/bypass overrides, full-coverage validation, and fail-closed processor/recipe admission. Active
regional sample processing and processor promotion remain separate gates.

## 7. Ampersand Adaptive Leveler

### Objective

Reduce distracting loudness differences among meaningful speech regions while preserving natural dynamics and refusing to amplify silence, breaths, room tone, uncertainty, and protected music as though they were quiet speakers.

### Analysis windows

Use standards-based K-weighted loudness measurements with at least:

- approximately 100 ms analysis hop;
- 400 ms momentary loudness;
- 3 s short-term loudness;
- integrated program measurements;
- speech/speaker/content masks.

Exact hop/window and smoothing settings are Ampersand research decisions, not copied from another service.

### Per-speaker target model

For each reliable speaker/content group:

1. collect speech-only loudness observations;
2. exclude silence, overlap, clipping, music-heavy, and low-confidence regions;
3. compute robust statistics such as trimmed median/percentiles;
4. choose a recipe-wide target or relative speaker target;
5. define a **comfort band**, not a single point;
6. preserve regions already inside that band.

### Raw desired gain

Conceptually:

```text
g_raw(t) = clamp(target_speaker(t) - measured_speech_loudness(t), min_gain, max_gain)
```

But set `g_raw(t)` to hold, decay, or zero under:

- non-speech;
- uncertain speech;
- protected music;
- breaths/noise;
- short transients;
- unsafe noise-floor conditions.

### Smooth constrained envelope

Solve or approximate a regularized gain trajectory:

```text
minimize
  Σ w(t) · (g(t) - g_raw(t))²
  + λ1 Σ (Δg(t))²
  + λ2 Σ (Δ²g(t))²

subject to
  min_gain ≤ g(t) ≤ max_gain
  |Δg(t)| ≤ slope_limit
  |Δ²g(t)| ≤ acceleration_limit
```

This formalizes:

- faithfulness to desired correction;
- smooth gain movement;
- limited rate/acceleration;
- content-aware confidence weighting.

The first implementation may use forward/backward smoothing and bounded ramps rather than a general optimizer, but it should preserve the same constraints and produce a testable gain envelope.

### Application

- apply sample-accurate interpolated gain;
- use look-ahead where allowed by offline processing;
- crossfade speaker/content boundaries;
- preserve stereo image unless explicit mixdown;
- avoid changing gain rapidly around plosives/transients;
- record the envelope as a reusable artifact.

### Short-term dynamics

After leveling, optionally apply a conservative soft-knee compressor for micro-dynamics. Do not ask one compressor to solve both speaker differences and peaks.

### Validation

- synthetic level steps;
- two-speaker differences;
- silence/noise gaps;
- speech over music;
- laughter/applause;
- whisper/quiet speech;
- already mastered speech;
- one-hour gain drift;
- clean-input preservation.

## 8. Conservative speaker-aware AutoEQ

Do not begin with a black-box generative EQ model.

### AutoEQ V0/V1

For each reliable speaker:

1. select speech-only, low-noise regions;
2. compute long-term average spectrum in perceptual bands;
3. normalize for loudness;
4. compare against a target distribution derived from Ampersand's rights-cleared clean corpus;
5. estimate confidence and microphone/environment consistency;
6. derive broad shelves/bells only;
7. smooth changes across time;
8. bypass on low confidence.

### Safety limits

Initial limits should be conservative, for example:

- broad corrections;
- approximately ±3 dB maximum default correction;
- no narrow boosts;
- narrow cuts only for confidently identified hum/resonance;
- speaker-specific curves;
- user-visible before/after curve and confidence;
- no correction to protected music.

FFmpeg `adynamicequalizer`, `adrc`, biquads, and filters may execute the curve. They are not the decision engine.

### De-essing

Use a separate high-band detector and dynamic attenuation rather than permanent global treble reduction.

### Plosives

Detect short low-frequency transients near speech onsets and apply a localized low-band attenuation/filter envelope. Do not globally high-pass the entire speaker to solve occasional plosives.

### Breaths

Treat breath removal as attenuation, not deletion, by default. Candidate reductions should be conservative and preserve natural phrasing.

## 9. Clipping, coughs, fillers, silence, and edits

### Clipping

Use FFmpeg `adeclip` as a deterministic mild-clipping baseline. Severe clipping may require restoration research and must be reported rather than silently “fixed.”

### Coughs and filler words

Detection should initially create reversible suggestions:

- region label;
- transcript/event confidence;
- preview;
- attenuate, silence, cut, or keep;
- smooth edit boundaries.

Do not destructively cut by default.

### Silence

Silence detection is not equivalent to deletion. Preserve:

- rhetorical pauses;
- room transitions;
- applause timing;
- emotional pauses;
- music tails.

Automatic silence shortening must be recipe-specific and reversible.

## 10. Workflow engine direction

### Current production lead — Temporal

Temporal's durable execution model is best aligned with customer-facing long media because workflows are event-sourced and resilient to process/worker failures while external Activities are expected to be idempotent.

Primary sources:

- [Temporal](https://github.com/temporalio/temporal)
- [Temporal Python SDK](https://github.com/temporalio/sdk-python)
- [Temporal durable execution documentation](https://docs.temporal.io/)

Recommended use:

- workflow holds compact state/references only;
- object storage holds media and large manifests;
- one Activity per independently retryable media step;
- idempotency keys based on input/model/recipe versions;
- child workflows for large branches or batches;
- heartbeat/cancellation for long native/model execution;
- explicit activity timeouts and retry classes;
- deterministic workflow code with versioning.

Start with Temporal Cloud if it materially reduces operational risk and cost is acceptable; preserve a self-host/exit plan.

### Audio Lab lead — Prefect

Prefect is a strong fit for Python-native experiment flows, parameter sweeps, cached artifacts, scheduled corpus runs, and researcher-visible batch orchestration.

Primary source:

- [Prefect](https://github.com/PrefectHQ/prefect)

Do not force the Lab and customer production system to share one workflow engine if their operational needs differ.

### Hatchet — keep as challenger

Hatchet remains attractive for a simpler Postgres-backed Python/TypeScript task platform, but it should not be selected by architecture taste alone. Long-running self-host reliability and recovery must be proven through issue #9's fault suite.

Primary source:

- [Hatchet](https://github.com/hatchet-dev/hatchet)

ADR-0004 remains open until the shared spike is complete.

## 11. Waveforms and timeline UI

### Do not decode long media fully in the browser

Generate a multiresolution peak pyramid in a worker:

```text
level 0: fine min/max windows
level 1: combine adjacent windows
level 2: combine again
...
```

Store compact binary or versioned JSON/typed-array data with channel and time metadata.

This is straightforward enough to implement independently and avoids introducing GPL `audiowaveform` as a required production dependency.

### Current UI lead — WaveSurfer.js

WaveSurfer.js is the current permissive candidate for:

- streamed playback;
- precomputed peaks;
- regions;
- zoom/scroll;
- events and plugins.

Primary source:

- [WaveSurfer.js](https://github.com/katspaugh/wavesurfer.js)

The spike must still prove:

- 1–3 hour files;
- sample/time mapping;
- variable-bitrate behavior;
- multichannel display;
- keyboard/screen-reader access;
- mobile performance;
- no full-source browser decode.

## 12. Deterministic editing

### Internal model first

Ampersand's edit core should use:

- integer microseconds or rational time;
- half-open intervals;
- explicit kept/cut ranges;
- deterministic command replay;
- immutable raw transcript plus versioned user edits;
- save/reopen/render reproducibility;
- property tests for contiguity, overlap, and round trips.

### Dawn-Cut guidance

Dawn-Cut is valuable because its pure TypeScript core emphasizes deterministic EDL semantics, transcript/timeline synchronization, integer microseconds, half-open intervals, invariants, and undo/replay.

Primary source:

- [Dawn-Cut](https://github.com/kwakseongjae/dawn-cut)

Recommended approach:

- audit its bounded core package;
- copy concepts freely only at the architectural level;
- vendor/adapt actual MIT code only after provenance and maintenance review;
- do not fork its entire application;
- keep Ampersand's Semantic Map and processing domain independent.

### Other references

- **CutScript:** useful implementation reference for WhisperX, DeepFilterNet, text editing, and FFmpeg export; not a foundation.
- **Auto-Editor:** useful baseline for loudness/silence-driven edit behavior and NLE export; pin exact open CLI boundaries.
- **OpenTimelineIO:** use for interchange, not as the internal word-level edit model.

OpenTimelineIO adapters have format-specific limitations; do not promise perfect round-trip preservation of effects/transitions in every NLE.

## 13. Audiogram and caption rendering

### Shared render specification

Browser preview and server export must consume the same versioned render spec:

- dimensions/aspect ratio;
- timing range;
- layers;
- background assets;
- text/caption style;
- waveform style and data source;
- fonts;
- animation parameters;
- safe-area rules;
- color/brand tokens.

### Server renderer

Recommended path:

```text
render spec + precomputed audio features
  ↓
@napi-rs/canvas / Skia frame renderer
  ↓
raw/image frame stream
  ↓
FFmpeg video/audio encoder
  ↓
H.264 MP4 and approved alternatives
```

Primary source:

- [@napi-rs/canvas](https://github.com/Brooooooklyn/canvas)

### Captions

Use libass through FFmpeg for final subtitle shaping/burn-in when appropriate.

Primary source:

- [libass](https://github.com/libass/libass)

Do not use browser `MediaRecorder` or real-time playback as the authoritative export engine.

## 14. Runtime and packaging guidance

### V1 workers

Prefer:

- Python for analysis/model orchestration;
- NumPy/SciPy and typed Pydantic/domain contracts;
- FFmpeg as controlled subprocess;
- ONNX Runtime where a candidate has a verified ONNX path;
- PyTorch isolated behind model adapters where necessary;
- one container profile per approved native/model group when dependency conflicts justify it.

### Do not introduce a model-serving platform immediately

Run models inside durable workers first.

Add BentoML, Triton, Ray Serve, or another dedicated inference layer only when measured evidence shows:

- repeated model loading dominates cost;
- multiple workers must share one GPU;
- dynamic batching is valuable;
- independent model scaling is required;
- process isolation is insufficient.

### Later Rust opportunities

Port only stable, measured bottlenecks such as:

- waveform peak generation;
- gain-envelope application;
- loudness analysis wrapper;
- render utilities;
- desktop/local processing.

Do not rewrite unproven research logic in Rust for theoretical performance.

## 15. Production, Lab, and reference-only classifications

### Work toward production first

- controlled FFmpeg build;
- libebur128;
- Silero VAD ONNX;
- custom Semantic Map;
- custom Leveler V0/V1;
- deterministic classic DSP/no-op baseline;
- DeepFilterNet candidate;
- two-pass final loudness/master validation;
- Postgres/S3 contracts;
- Temporal spike/current lead;
- custom waveform peak pyramid;
- WaveSurfer spike;
- same-position A/B playback.

### Keep in the Audio Lab

- ClearerVoice model family;
- WhisperX, Parakeet, and MOSS comparison;
- PANNs or other event classifiers;
- nara_wpe;
- Resemble Enhance and other generative restoration;
- separation/target-speaker models;
- Prefect experiment flows;
- objective metric implementations beyond standards validation;
- alternative levelers and filters.

### Reference only or deferred

- Dawn-Cut full app;
- CutScript full app;
- Auto-Editor full product;
- OpenCut/general video editors;
- ComfyUI as production orchestration;
- Waveform Playlist/multitrack editor before singletrack V1;
- broad model-serving infrastructure;
- GPL/AGPL/noncommercial projects without a reviewed isolation/compliance plan.

## 16. Explicit anti-patterns

Do not:

- treat `dynaudnorm` or `speechnorm` as the finished Adaptive Leveler;
- run every file through a neural denoiser;
- amplify regions merely because they are quiet;
- make generative restoration a default;
- combine five editors/frameworks into one repository;
- place binary media or huge transcript payloads in workflow event history;
- let provider-native ASR schemas become Ampersand's domain model;
- use browser AudioContext decoding for long-form production waveform generation;
- export long-form video through real-time canvas capture;
- download mutable model weights at runtime;
- assume a repository license covers model weights;
- use NISQA's commonly published noncommercial weights in commercial selection logic;
- embed GPL tools casually in a proprietary distributable;
- use Auphonic outputs or derived learnings as a benchmark or design target without written permission;
- postpone clean-input preservation testing until beta;
- build a gorgeous Studio before the quality and one-hour recovery proofs pass.

## 17. Concrete first implementation target

The first meaningful Ampersand engine should be:

```text
rights-cleared source
  ↓
FFprobe validation + source manifest
  ↓
canonical PCM only when needed
  ├── custom peak pyramid
  ├── libebur128 loudness/peak analysis
  └── Silero VAD
          ↓
initial Semantic Map
          ↓
router:
  clean/uncertain → no-op
  eligible noisy speech → DeepFilterNet candidate
          ↓
Ampersand Leveler V0 gain envelope
          ↓
conservative optional EQ/filtering
          ↓
FFmpeg two-pass loudness master
          ↓
libebur128/output validation
          ↓
WAV + MP3 + processing report
```

This target is intentionally narrower than Auphonic. It is broad enough to prove Ampersand's central thesis and narrow enough to evaluate rigorously.

## 18. Implementation order

1. Pin FFmpeg/libebur128/native build and standards tests.
2. Define processor, model, semantic-map, gain-envelope, and artifact manifests.
3. Build custom waveform peak pyramid.
4. Integrate Silero VAD through ONNX.
5. Implement Leveler V0 against synthetic level/silence/music tests.
6. Build the listening/clean-preservation harness.
7. Integrate DeepFilterNet as the first swappable model adapter.
8. Run ClearerVoice enhancement challenge.
9. Run WhisperX/Parakeet/MOSS speech-understanding challenge.
10. Run Temporal/Hatchet/Prefect workflow spike and accept provider ADR.
11. Complete one-hour end-to-end failure/recovery proof.
12. Only then build the full Studio alpha and migrate audiogram visuals.

## Decision summary

The expert direction is not “use every promising open-source repo.” It is:

> **Use mature infrastructure for media execution and durability; isolate models behind contracts; build Ampersand's semantic map, router, Leveler, conservative EQ, and quality controller ourselves; promote components only through rights-cleared listening evidence.**

That path minimizes infrastructure work without surrendering the parts that make the product valuable or defensible.
