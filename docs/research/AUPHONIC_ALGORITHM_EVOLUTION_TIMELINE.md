# Auphonic Algorithm Evolution Timeline

**Status:** Active public-source chronology  
**Last verified:** 2026-08-18  
**Purpose:** Track how Auphonic's public processing architecture evolved from classic DSP and classifiers toward specialized deep-learning and generative restoration models.

## Why this timeline matters

Individual Auphonic pages can make the product appear to be one stable collection of algorithms. The historical record shows something more useful:

- the architecture has evolved incrementally for more than a decade;
- old deterministic/classifier systems coexist with newer neural systems;
- processors are replaced or have responsibilities moved between them;
- the semantic segmentation layer remains a recurring foundation;
- user feedback and service data repeatedly drive updates;
- current terminology may describe a materially different implementation than the same feature name several years earlier.

This timeline uses public sources only and does not use Auphonic outputs or prohibited black-box analysis.

---

## 2009–2012 — Python/DSP/ML service foundation

Founder Georg Holzmann has described the early processing and machine-learning engine as mainly Python, with NumPy, multiple ML libraries, optimized C components, and Cython. Django surrounded the engine; distributed jobs later used Celery and RabbitMQ.

By the 2012 API release, Auphonic publicly offered:

- standards-based loudness normalization;
- an intelligent leveler balancing speakers, music, and speech;
- compression as needed;
- noise restoration that classified regions with different backgrounds;
- automatic noise and hum removal;
- encoding, metadata, and publishing workflows.

Sources:

- [Django Chat interview](https://djangochat.com/episodes/auphonic-automated-audio-post-production/transcript)
- [Auphonic API v1 release](https://auphonic.com/blog/2012/10/08/auphonic-audio-processing-web-api-version-1-released/)

### Architectural interpretation

The initial product already separated:

```text
analysis/classification
  ↓
content-aware level decisions
  ↓
restoration
  ↓
loudness/encoding/workflow
```

The core product idea was never merely a compressor preset.

---

## 2013 — Processing statistics and feedback become explicit

Auphonic documented machine-readable processing statistics containing:

- input loudness, LRA, SNR, signal level, and noise level;
- output loudness, true peak, LRA, and leveler gain min/mean/max;
- music/speech regions;
- noise/hum-reduction regions and amounts.

It also asked users to report problematic segments so that those examples could train classifiers.

Source:

- [Audio Processing Statistics Explained](https://eu1.auphonic.com/blog/2013/12/16/audio-processing-statistics-explained/)

### Architectural interpretation

By 2013, Auphonic publicly exposed evidence of:

- a persisted or reproducible semantic timeline;
- a time-varying leveler gain trajectory;
- regional denoise decisions;
- a human-feedback-to-training loop.

These are durable architectural concepts that continue to appear in later products.

---

## 2014 — Classic denoise reaches desktop; multitrack joint analysis launches

### Classic Noise and Hum Reduction

Auphonic described:

1. segmenting audio by changing background-noise characteristics;
2. extracting a noise print per region;
3. detecting power-line hum and harmonics;
4. using a classifier to decide necessary attenuation;
5. applying sharp filters and broadband reduction.

Auphonic said the web and desktop algorithms were the same at that time.

Source:

- [Noise and Hum Reduction for the Leveler](https://auphonic.com/blog/2014/04/28/noise-and-hum-reduction-in-auphonic-leveler/)

### Multitrack

The first multitrack architecture jointly processed all tracks and used shared knowledge to:

- determine the active speaker/track;
- balance speakers across tracks;
- apply compression to speech while preserving music;
- extract per-track noise profiles;
- attenuate inactive microphones with an Adaptive Noise Gate;
- remove crosstalk with Crossgate.

Sources:

- [Multitrack Private Beta](https://us.auphonic.com/blog/2014/05/13/multitrack-private-beta/)
- [Multitrack Release](https://us.auphonic.com/blog/2014/10/21/auphonic-multitrack-algorithms-release/)

### Architectural interpretation

Auphonic's multitrack system has always been joint-context processing, not “run singletrack independently on every stem, then sum.”

---

## 2018–2020 — Control laws become user-visible and broadcast-oriented

Auphonic exposed more advanced Leveler and restoration controls:

- Leveler Strength;
- compressor presets separated from Leveler Strength;
- separate music/speech parameters;
- MusicSpeech classifier override;
- Music Gain and Track Gain;
- Broadcast Mode with MaxLRA, MaxS, and MaxM;
- automatic/manual hum frequency and attenuation;
- per-region classifier override through fixed amounts.

The company said these advanced parameters had stabilized by 2020.

Sources:

- [Leveler Presets, LRA Target and Advanced Parameters](https://us.auphonic.com/blog/2018/08/21/leveler-presets-lra-target-advanced-audio-params-beta/)
- [Advanced Leveler Broadcast Parameters](https://us.auphonic.com/blog/2020/12/04/advanced-leveler-broadcast-parameters/)

### Architectural interpretation

This period confirms the separation among:

- long/mid-term leveling;
- short-term compression;
- speech versus music treatment;
- regulatory loudness constraints;
- final global loudness and peak handling.

Ampersand should retain this conceptual separation even if its controls are simpler.

---

## 2022 — Deep denoising and GPU development become explicit

### New noise-reduction models

Auphonic introduced modern Dynamic Denoising and Speech Isolation:

- Dynamic Denoiser preserves speech and music while removing complex changing noise;
- Speech Isolation preserves speech and removes music/background as well;
- the old noise-print system becomes the Classic Denoiser category.

### GPU training

Auphonic joined NVIDIA Inception and disclosed that one Dynamic Denoiser training cycle took nearly a week on GPUs and would take months on CPUs. It described thousands of files and larger deep-learning models.

### Self-hosted Whisper

Auphonic launched its first self-hosted ASR engine using OpenAI Whisper, alongside historical external ASR integrations.

Sources:

- [New Noise Reduction Algorithms](https://auphonic.com/blog/2022/06/10/new-noise-reduction-algorithms-beta/)
- [Auphonic Joins NVIDIA Inception](https://auphonic.com/blog/2022/09/21/auphonic-joins-nvidia-inception/)
- [Auphonic Whisper ASR](https://auphonic.com/blog/2022/11/08/auphonic-whisper-asr-beta/)

### Architectural interpretation

2022 is the clearest public transition from primarily classifier-controlled classic DSP toward dedicated neural source-preservation and isolation models, while keeping the surrounding semantic and mastering architecture.

---

## 2023 — AutoEQ v1: conservative, per-speaker, time-varying EQ

The first AutoEQ announcement said:

- the source is classified into meaningful segments;
- spectral EQ profiles are created separately for each speaker;
- profiles change continuously over time;
- changing speaker/mic position is handled;
- background music can remain unchanged;
- the system follows conservative rules;
- already-good recordings should receive little or no significant change;
- AutoEQ could not recover frequencies absent from low-bitrate audio and was explicitly not bandwidth extension.

Source:

- [New Auphonic AutoEQ Filtering](https://us.auphonic.com/blog/2023/01/24/autoeq-beta/)

### Critical evolution clue

In 2023, Auphonic described AutoEQ primarily as subtle, time-dependent spectral adjustment. In 2026, it describes AutoEQ as an AI model that re-generates voice for spectral balance.

This suggests at least one of:

- the internal AutoEQ model changed materially;
- learned reconstruction was added behind the same feature name;
- the product description became more technically explicit;
- deterministic EQ remains as post-processing around a learned voice model.

Public sources do not identify which explanation is correct.

---

## 2023–2024 — Automatic editing and independent reduction controls

### Filler cutter

Auphonic disclosed manually labeled real-world datasets for English, German, Spanish, and French filler detection. It later expanded language-specific training.

### Separate denoising components

Auphonic separated the user controls for:

- noise reduction;
- reverb reduction;
- breath reduction.

Previously one amount controlled the selected denoiser's combined behavior.

Sources:

- [Automatic Filler Word Cutter](https://us.auphonic.com/blog/2023/10/04/new-automatic-filler-word-cutter/)
- [Independent Noise, Reverb and Breath Controls](https://auphonic.com/blog/2024/05/16/independently-control-noise-reverb-and-breath-reduction-amounts/)

### Architectural interpretation

The denoise model output must support independently controllable unwanted components, masks, residuals, or post-model stages. The exact mechanism is not disclosed.

---

## 2025 — Voice restoration, model replacement, and joint multitrack separation accelerate

### Bandwidth Extension and enhanced AutoEQ

Auphonic added speech-specific BWE that predicts and synthesizes missing upper-frequency content. It is always paired with AutoEQ and avoids enhancing music, noise, reverb, and environmental sound.

AutoEQ was updated for:

- reverberant speech;
- speech over background music.

De-plosive processing was moved/integrated into Noise Reduction, improving combinations with Dynamic Denoiser and Speech Isolation.

Source:

- [Bandwidth Extension and Enhanced AutoEQ](https://auphonic.com/blog/2025/04/04/new-bandwidth-extension-feature/)

### New Static/Music Denoiser

Auphonic introduced a learned Static Denoiser that no longer needs a noise-only pause and can preserve continuous music, ambience, sound design, and effects while reducing stationary noise and reverb.

Source:

- [New Static and Music Denoiser](https://auphonic.com/blog/2025/07/31/new-auphonic-static-and-music-denoiser/)

### New Mic Bleed Remover

Auphonic replaced the conceptual limits of its old smart-gate/Crossgate approach with a model that:

- jointly analyzes all tracks;
- learns what belongs to each microphone;
- handles overlap and misalignment;
- removes cross-owned speech;
- preserves ambience, timing, music, and track noise.

Source:

- [Mic Bleed Remover](https://auphonic.com/blog/2025/10/08/mic-bleed-remover/)

### Denoising Editor

Auphonic exposed region-level processor and amount overrides, confirming that processing selection is increasingly represented as editable timeline metadata.

Source:

- [Auphonic Blog Index — Denoising Editor](https://auphonic.com/help/resources/blog.html)

### Architectural interpretation

2025 shows Auphonic moving from global feature switches toward a modular **per-region processing graph**:

```text
region
  ├── denoiser choice
  ├── noise/reverb/breath amounts
  ├── filter/AutoEQ/BWE choice
  └── user override
```

It also shows processor responsibilities moving over time—e.g., de-plosive work shifting toward denoise.

---

## 2026 — Studio Voice, video cutting, CLI, and production-scale automation

### Studio Voice

Studio Voice reconstructs substantially more of the speech signal than AutoEQ and can repair:

- low-bitrate codec/compression damage;
- clipping and distortion;
- missing high frequencies;
- artifacts from denoisers, TTS, and other voice processing.

Auphonic explicitly says Studio Voice runs after denoise in severe cases to restore speech damaged by aggressive cleanup. It includes bandwidth extension and may replace the earlier BWE model.

Source:

- [Studio Voice Beta](https://auphonic.com/blog/2026/07/21/studio-voice-beta/)

### Automatic video cutting

The existing silence, filler, cough, music, and custom cut system was extended to video while keeping automatic and manual editing in one timeline experience.

Source:

- [Automatic Video Cutting](https://auphonic.com/blog/2026/04/15/automatic-video-cutting/)

### CLI/OpenAPI

Auphonic released a dependency-free cross-platform CLI backed by its cloud service and expanded its OpenAPI coverage. This does not expose the processing engine locally; it expands workflow/API access.

Source:

- [Auphonic CLI](https://auphonic.com/blog/2026/03/26/auphonic-cli/)

### Current runtime profile

Auphonic says newer algorithms require custom hardware and reports average processing around 5% of source duration.

Sources:

- [Desktop Programs](https://auphonic.com/standalone)
- [Auphonic Features](https://us1.auphonic.com/features)

### Architectural interpretation

The modern system is likely heterogeneous:

```text
CPU/native analysis, DSP, encoding
  +
GPU neural denoise, restoration, ASR, multitrack models
  +
shared semantic timeline and region-processing plan
  +
durable cloud workflow/API layer
```

Exact orchestration and model-serving implementations remain private.

---

# Cross-era deductions

## 1. Auphonic evolves by replacing processors behind stable product concepts

Names such as AutoEQ or Static Denoiser do not guarantee the same implementation across years. Ampersand must version processors and recipes explicitly rather than silently replacing a model behind an old label.

## 2. Semantic segmentation is the stable architectural spine

From the earliest Leveler and noise regions through modern AutoEQ, BWE, Studio Voice, ASR, cutting, and multitrack processing, content segmentation remains the recurring shared layer.

## 3. Processor responsibilities overlap and move

De-plosive behavior appears in AutoEQ and denoising paths; Studio Voice repairs denoiser artifacts; BWE is paired with AutoEQ; current Studio Voice may replace BWE. Ampersand should model processor capabilities and ordering rather than assume one defect always maps to one module.

## 4. “No processing” is a mature feature

The 2023 AutoEQ announcement emphasized conservative behavior and little/no change when the source already sounds good. Modern segment editors let users bypass or change processors regionally. Ampersand's router must treat no-op as a first-class result.

## 5. The data/evaluation loop is as important as model architecture

Auphonic repeatedly combines production data, user-reported failures, manually labeled datasets, and direct listening feedback. Ampersand's independent quality program is therefore not secondary infrastructure—it is the closest lawful equivalent to Auphonic's long-term moat.

# Ampersand consequences

The timeline reinforces the current plan:

- own the Semantic Audio Map;
- own processor/recipe versioning;
- own the Processing Router;
- build the Adaptive Leveler independently;
- preserve no-op and clean-input behavior;
- isolate models behind replaceable adapters;
- expose regional decisions and overrides;
- record exact model/processor provenance;
- expect processing responsibilities and preferred models to evolve;
- never market a stable feature name as if it guarantees a fixed internal implementation.

# Research queue

- fully review the CC BY 4.0 2024 talk **“Wie lernt eine Maschine? KI Audio mit Auphonic”**;
- locate any slides, subtitles, or related workshop materials;
- search older talks and interviews for Leveler training/evaluation details;
- inspect public Auphonic repository history for feature-extraction changes;
- archive current OpenAPI schemas for per-segment filters, denoisers, cuts, and Studio Voice;
- monitor whether Studio Voice replaces BWE or changes product sections after beta;
- monitor public hiring material for serving/training framework clues;
- continue searching academic theses, research partnerships, patents, and conference publications under employee names.

All work remains subject to the documented public-source-only research boundary.