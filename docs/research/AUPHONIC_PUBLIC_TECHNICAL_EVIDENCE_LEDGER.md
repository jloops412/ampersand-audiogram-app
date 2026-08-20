# Auphonic Public Technical Evidence Ledger

**Status:** Active public-source research record  
**Last verified:** 2026-08-18  
**Scope:** Public documentation, public repositories, public talks/interviews, public hiring material, standards, and public API schemas only

## Purpose

This ledger records concrete evidence about Auphonic's implementation history, current technical direction, data flywheel, processing artifacts, and likely architecture. It separates:

- facts Auphonic has explicitly published;
- historical implementation evidence;
- strong but non-confirmed engineering deductions;
- questions that remain proprietary or unresolved.

It complements [Auphonic Public Reconstruction Matrix](./AUPHONIC_PUBLIC_RECONSTRUCTION_MATRIX.md), which is organized by product capability.

## Research boundary

Auphonic's current Terms of Service prohibit using its services, outputs, derivatives, evaluations, insights, or learnings to develop, train, evaluate, benchmark, reverse engineer, or improve a competing system without a tailored arrangement.

Accordingly, this ledger does not use:

- controlled Auphonic input/output experiments;
- Auphonic outputs as references or quality targets;
- binary decompilation;
- extraction of models or implementation details from distributed software;
- tuning toward Auphonic examples.

See [Auphonic Capability and Research Boundary](./AUPHONIC_CAPABILITY_AND_RESEARCH_BOUNDARY.md).

## Evidence labels

| Label | Meaning |
|---|---|
| **Current confirmed** | Explicitly stated in current official Auphonic material. |
| **Historical confirmed** | Explicitly stated by Auphonic or its founder in older public material; may no longer describe current production. |
| **Public-code clue** | Present in Auphonic's public organization or distributed tooling, but current production use is not established. |
| **High-confidence deduction** | Strongly supported by multiple public facts and standard engineering practice, but not directly confirmed. |
| **Plausible deduction** | Technically reasonable but insufficiently evidenced to guide a production decision alone. |
| **Unknown** | Public sources do not establish the answer. |

---

# 1. Current implementation stack

## 1.1 Official current hiring evidence

Auphonic's current Machine/Deep Learning and Signal Processing Engineer posting asks for:

- Python;
- PyTorch;
- NumPy;
- SciPy;
- C/C++;
- Linux/Bash;
- Git;
- deep-learning model training on GPU servers;
- classical signal-processing knowledge including filtering, FFTs, sampling, MFCCs, and VAD;
- work with large-scale real-world datasets on GPU infrastructure;
- approaches ranging from simple audio-engineering tricks and classical DSP to large deep-learning models.

Primary source:

- [Auphonic ML/DSP Engineer](https://auphonic.com/jobs/ml-engineer)

**Evidence classification:** Current confirmed.

### Deduction

Auphonic's present-day engine is almost certainly a hybrid stack rather than a single end-to-end model:

```text
Python orchestration/research
  ├── PyTorch neural models
  ├── NumPy/SciPy analysis and DSP
  ├── C/C++ optimized/native paths
  └── conventional features and detectors
       ├── FFT/spectral features
       ├── MFCC or similar speech/audio descriptors
       └── VAD/activity features
```

**Confidence:** High.

The job description is especially important because it shows that classical DSP and hand-crafted analysis remain part of Auphonic's current engineering culture even after its shift to larger neural models.

## 1.2 Historical founder implementation description

In a public Django Chat interview, founder Georg Holzmann described:

- signal processing and machine learning as mainly implemented in Python;
- extensive use of NumPy and multiple machine-learning libraries;
- optimized components written in C;
- Cython used to compile/accelerate Python paths;
- Django as the surrounding web system;
- Django REST Framework for API concerns;
- Celery and RabbitMQ for distributed audio-processing tasks;
- long-running audio jobs rather than extremely large numbers of tiny jobs;
- an Electron user interface paired with a Python processing backend for the desktop application;
- Cython and PyInstaller used to package the Python backend.

Primary source:

- [Django Chat: Auphonic — Georg Holzmann](https://djangochat.com/episodes/auphonic-automated-audio-post-production/transcript)

**Evidence classification:** Historical confirmed.

### Deduction

The current engine likely evolved from a mature offline Python/Cython/C processing graph rather than being replaced wholesale by a monolithic cloud-native model. Modern PyTorch services may now sit beside or replace individual legacy processors, while shared semantic analysis and deterministic stages remain in Python/native code.

**Confidence:** High, but current orchestration details are unknown.

---

# 2. Data flywheel and training process

## 2.1 Daily adaptation and real-world service data

Auphonic repeatedly states that its algorithms:

- were trained with data from its web service;
- keep learning and adapting to new audio signals every day;
- use large-scale real-world datasets;
- are improved through customer feedback.

Primary sources:

- [Auphonic ML/DSP Engineer](https://auphonic.com/jobs/ml-engineer)
- [Auphonic Features](https://us.auphonic.com/features)
- [Multitrack Algorithms](https://us1.auphonic.com/help/algorithms/multitrack.html)
- [Auphonic Leveler Batch Processor](https://auphonic.com/leveler)

**Evidence classification:** Current confirmed.

## 2.2 Human listening and feedback

Auphonic's privacy policy and terms state that uploaded content may be viewed or listened to by employees or contractors working on audio-processing algorithms. A 2013 processing-statistics article explicitly asked users to report incorrect/problematic regions so the data could be used to train classifiers. Current Studio Voice beta material similarly asks users to submit difficult examples and says feedback directly shapes the final model.

Primary sources:

- [Auphonic Privacy Policy](https://eu1.auphonic.com/privacy)
- [Auphonic Terms of Service](https://auphonic.com/terms_of_service)
- [Audio Processing Statistics Explained](https://eu1.auphonic.com/blog/2013/12/16/audio-processing-statistics-explained/)
- [Studio Voice Beta](https://auphonic.com/blog/2026/07/21/studio-voice-beta/)

**Evidence classification:** Current and historical confirmed.

## 2.3 Manually labeled algorithm datasets

Auphonic disclosed that its filler-word model was trained on manually labeled real-world audio datasets. Initial labeled/trained/tested languages included English, German, Spanish, and French. Later in-house improvements targeted Greek, Romanian, and Hungarian, and Auphonic explicitly says filler detection is language specific.

Primary sources:

- [Automatic Filler Word Cutter](https://us.auphonic.com/blog/2023/10/04/new-automatic-filler-word-cutter/)
- [Fillerword Cutting Optimized for Greek, Romanian and Hungarian](https://us1.auphonic.com/blog/2025/04/22/fillerword-cutting-optimized-for-greek-romanian-and-hungarian/)

**Evidence classification:** Current confirmed.

### Deduction: the principal moat

Auphonic's largest advantage is likely not one secret filter. It is the combination of:

1. years of diverse production audio;
2. automatically generated semantic/quality metadata;
3. user-reported failures;
4. targeted human listening and labeling;
5. repeated model/DSP iteration;
6. production-scale feedback about artifacts and edge cases.

This creates a durable data-and-evaluation flywheel that is difficult to duplicate merely by downloading equivalent open-source models.

**Confidence:** High.

### Ampersand implication

Ampersand should build its own lawful version of this flywheel through:

- rights-cleared corpus material;
- explicit opt-in research contributions only;
- processing reports and artifact categories;
- blinded listening;
- clean-input preservation;
- versioned user feedback tied to exact recipe/model versions;
- no-training-by-default product policy.

---

# 3. The semantic timeline is a first-class internal artifact

## 3.1 Processing-statistics schema

Auphonic's documented processing statistics expose:

### Input measurements

- integrated loudness;
- loudness range;
- maximum momentary and short-term loudness;
- noise/background level;
- signal level;
- SNR.

### Output measurements

- integrated loudness;
- loudness range;
- maximum momentary and short-term loudness;
- true peak;
- Adaptive Leveler gain minimum, mean, and maximum.

### Timeline regions

- music/speech segments with start and stop times;
- noise/hum-reduction segments with applied denoise amount and dehum state;
- multitrack activity regions and per-track gain statistics in the multitrack schema.

Primary source:

- [Audio Processing Statistics Explained](https://eu1.auphonic.com/blog/2013/12/16/audio-processing-statistics-explained/)

**Evidence classification:** Historical confirmed and still architecturally relevant.

## 3.2 Editor visualization

Auphonic's editor and statistics visualizations associate semantic region types and leveler decisions with waveform regions. Public descriptions distinguish speech, music, quiet speech requiring substantial amplification, and speech regions receiving little or no amplification.

Primary sources:

- [Auphonic Editor Help](https://us1.auphonic.com/help/web/production.html)
- [Auphonic Leveler](https://auphonic.com/leveler)

**Evidence classification:** Confirmed behavior.

### Deduction

Auphonic almost certainly persists or regenerates a unified analysis graph containing at least:

```text
Region
  start
  stop
  semantic label(s)
  speaker/activity information
  background/noise state
  confidence or classifier evidence
  desired/applied processing parameters
  leveler gain trajectory or summary
```

Its processing engine is therefore better modeled as **analysis metadata plus render decisions**, not merely an opaque chain of audio filters.

**Confidence:** High.

### Additional deduction from gain statistics

The published `gain_min`, `gain_mean`, and `gain_max` fields imply that Adaptive Leveling produces a time-varying gain trajectory whose distribution is summarized after processing. Very low multitrack gain minima reported in historical statistics are consistent with gate/near-mute behavior being represented in related gain/activity paths.

**Confidence:** Medium/high.

### Ampersand implication

The existing Ampersand plan to persist a versioned `SemanticMap`, `ProcessingRegion`, and gain-envelope artifact is strongly validated by Auphonic's public architecture.

---

# 4. Denoising architecture deductions

## 4.1 Classic Denoiser

Auphonic explicitly describes this process:

1. analyze the source;
2. segment it into regions with different background characteristics;
3. extract a noise print for each region;
4. detect 50 Hz or 60 Hz hum and harmonic partials;
5. use a classifier to determine how much denoise/dehum is needed;
6. remove noise and hum region by region.

Primary sources:

- [Noise and Hum Reduction for Auphonic Leveler](https://auphonic.com/blog/2014/04/28/noise-and-hum-reduction-in-auphonic-leveler/)
- [Multitrack Algorithms — Classic Denoiser](https://us1.auphonic.com/help/algorithms/multitrack.html)
- [Advanced Noise/Hum Controls](https://us.auphonic.com/blog/2018/08/21/leveler-presets-lra-target-advanced-audio-params-beta/)

**Evidence classification:** Confirmed behavior.

### Likely independent implementation family

A functionally equivalent classic system can be independently built from:

- noise-only/speech-pause detection;
- regional minimum-statistics or spectral noise estimation;
- Wiener filtering or conservative spectral subtraction;
- hum fundamental estimation;
- narrow harmonic notch filters;
- classifier- or heuristic-controlled attenuation;
- artifact-aware flooring/wet-dry limits.

This does not establish Auphonic's equations or parameters.

## 4.2 Why the modern Static Denoiser is fundamentally different

Auphonic's current Static Denoiser can preserve speech, music, ambience, sound effects, and atmosphere while removing stationary noise and reverb without requiring a noise-only pause. Auphonic contrasts it with the Classic Denoiser, which depends on noise-print extraction from silence/speech pauses.

Primary sources:

- [New Static and Music Denoiser](https://auphonic.com/blog/2025/07/31/new-auphonic-static-and-music-denoiser/)
- [Multitrack Algorithms](https://us1.auphonic.com/help/algorithms/multitrack.html)

**Evidence classification:** Current confirmed behavior.

### Deduction

The current Static Denoiser is probably not merely upgraded spectral subtraction. Its preservation of continuous music/ambience while removing stationary interference strongly suggests learned source estimation, learned masks, or a hybrid neural/deterministic separator conditioned on semantic content.

**Confidence:** High.

## 4.3 Dynamic Denoiser versus Speech Isolation

Auphonic defines different preservation targets:

- **Dynamic Denoiser:** preserve speech and music; remove other changing/complex noise.
- **Speech Isolation:** preserve speech only; remove music and background content as well.

Separate controls now exist for noise, reverb, and breathing attenuation.

Primary sources:

- [AI Noise & Reverb Reduction](https://auphonic.com/blog/2022/07/27/new-noise-reduction/)
- [Independent Noise/Reverb/Breath Controls](https://auphonic.com/blog/2024/05/16/independently-control-noise-reverb-and-breath-reduction-amounts/)

**Evidence classification:** Current confirmed behavior.

### Deduction

Dynamic Denoiser and Speech Isolation likely share portions of a model family, feature pipeline, or training framework but differ in target-source definitions or conditioning. Their separate attenuation controls likely alter unwanted-component estimates, residual mixing, model conditioning, or post-inference masks rather than invoke completely unrelated processing for every numeric amount.

**Confidence:** Medium. Exact architecture is unknown.

### Product-level deduction

The most important feature is not simply denoise quality; it is the **preservation contract**:

```text
Dynamic Denoiser: wanted = speech + music
Speech Isolation: wanted = speech
Static Denoiser: wanted = speech + music + ambience/effects
```

Ampersand should model preservation targets explicitly in its processor capabilities and routing rules.

---

# 5. AutoEQ, BWE, and Studio Voice

## 5.1 Voice AutoEQ is now more than conventional EQ

Auphonic describes Voice AutoEQ as a speaker-aware, time-varying system for correcting sibilance, boominess, dullness, plosives, and overall spectral balance. In its 2026 Studio Voice announcement, Auphonic explicitly calls both Voice AutoEQ and Studio Voice AI models that re-generate the voice, with AutoEQ focused on spectral balance.

Primary sources:

- [Auphonic Features](https://us.auphonic.com/features)
- [Bandwidth Extension and Voice AutoEQ](https://auphonic.com/blog/2025/04/04/new-bandwidth-extension-feature/)
- [Studio Voice Beta](https://auphonic.com/blog/2026/07/21/studio-voice-beta/)

**Evidence classification:** Current confirmed behavior.

### Deduction

Current AutoEQ likely operates at least partly in a learned speech-restoration domain rather than solely outputting static biquad settings. It may still use explicit filters or deterministic post-processing, but public language no longer supports treating it as merely a traditional automatic equalizer.

**Confidence:** Medium/high.

## 5.2 Bandwidth Extension

Auphonic says BWE:

- analyzes existing frequency information;
- predicts and synthesizes missing upper-frequency components;
- is optimized specifically for speech;
- avoids adding frequencies to music, noise, reverb, and environmental sounds;
- is always combined with Voice AutoEQ.

Primary source:

- [New Bandwidth Extension Feature](https://auphonic.com/blog/2025/04/04/new-bandwidth-extension-feature/)

**Evidence classification:** Current confirmed behavior.

### Deduction

BWE must be gated by speech/semantic masks or operate on a separated speech estimate. Otherwise it could not reliably avoid enhancing background sounds. The likely order is:

```text
semantic speech selection
  ↓
optional denoise/separation
  ↓
voice spectral correction
  ↓
bandwidth reconstruction
  ↓
region recombination
```

**Confidence:** High for semantic gating; exact model/order is unknown.

## 5.3 Studio Voice

Studio Voice:

- reconstructs/regenerates substantially more of the voice than AutoEQ;
- repairs low-bitrate codec/compression artifacts;
- repairs clipping and distortion;
- restores missing high frequencies;
- repairs artifacts from denoisers, TTS, and other processing;
- runs after denoise in severe cases to restore damaged speech;
- includes bandwidth extension and may eventually replace the earlier BWE model;
- can be applied only to selected regions.

Primary source:

- [Studio Voice Beta](https://auphonic.com/blog/2026/07/21/studio-voice-beta/)

**Evidence classification:** Current confirmed behavior.

### Deduction

The public behavior is consistent with a conditional generative speech-restoration model using a neural decoder/vocoder, latent restoration network, flow/diffusion-style reconstruction, neural codec representation, or a hybrid. Public evidence does not identify which family is used.

**Confidence:** Low for model family; high that this is materially generative/restorative rather than ordinary filtering.

### Strong processing-order clue

Auphonic explicitly says Studio Voice runs after the denoiser when aggressive cleanup damages speech. This is the clearest public ordering statement for its modern neural stack:

```text
noise/reverb separation
  ↓
voice reconstruction/restoration
  ↓
leveling/mastering/output
```

The exact placement relative to AutoEQ, compression, and Adaptive Leveler remains unknown.

---

# 6. Multitrack and mic-bleed deductions

## 6.1 Historical Crossgate

The original multitrack system used knowledge of which speaker was active in which track to attenuate inactive microphones and remove correlated spill. Auphonic called this Crossgate and described it as distinct from its Adaptive Noise Gate/Expander.

Primary sources:

- [Multitrack Private Beta](https://us.auphonic.com/blog/2014/05/13/multitrack-private-beta/)
- [Multitrack Release](https://us.auphonic.com/blog/2014/10/21/auphonic-multitrack-algorithms-release/)

**Evidence classification:** Historical confirmed.

## 6.2 Current Mic Bleed Remover

Auphonic says its 2025 model:

- analyzes all microphones together;
- learns what belongs to each microphone;
- removes only material originating from other mics;
- preserves track noise, ambience, music, timing, and natural room character;
- handles overlapping speech;
- handles misaligned tracks;
- handles strong bleed and background noise;
- is not merely a smart gate.

Primary source:

- [Mic Bleed Remover](https://auphonic.com/blog/2025/10/08/mic-bleed-remover/)

**Evidence classification:** Current confirmed behavior.

### Deduction

This behavior is much more consistent with joint multichannel source attribution/separation than threshold gating or simple correlation cancellation. A plausible high-level formulation is:

```text
all microphone tracks
  ↓
joint alignment / shared representation
  ↓
per-source or per-mic ownership estimates
  ↓
remove cross-owned speech components
  ↓
preserve local ambience/noise/music residuals
```

Robustness to misalignment implies either delay-tolerant features, learned alignment, explicit lag estimation, or windowed cross-track synchronization.

**Confidence:** High for joint source-attribution/separation category; exact model unknown.

---

# 7. Automatic cutting models

## 7.1 Filler detection

Auphonic trained a dedicated filler cutter on manually labeled real-world audio. It treats filler detection as language-specific and has expanded training for additional languages in-house.

**Deduction:** The system is probably not a simple text substitution list. The need for manual audio labels, language-specific training, and detection of non-lexical sounds strongly suggests an acoustic-event or speech-token classifier, potentially combined with ASR language/context signals.

**Confidence:** High.

## 7.2 Cough and respiratory detection

Auphonic detects coughs, throat clearing, sneezing, and related respiratory sounds.

**Deduction:** This is likely a dedicated acoustic-event detector or multi-class event model, separate from VAD and transcript logic. Boundary refinement and crossfades likely use local waveform/silence context after event detection.

**Confidence:** Medium/high.

## 7.3 Silence and music cutting

Auphonic emphasizes preserving intentional pauses and targets longer foreground-music sections for automatic music cutting.

**Deduction:** Silence cuts probably combine amplitude/VAD intervals with duration, neighboring speech, and linguistic/context rules. Music cutting likely combines semantic music classification, foreground/background confidence, and minimum-duration thresholds.

**Confidence:** High at the functional level.

Primary sources:

- [Automatic Filler Word Cutter](https://us.auphonic.com/blog/2023/10/04/new-automatic-filler-word-cutter/)
- [Fillerword Language Improvements](https://us1.auphonic.com/blog/2025/04/22/fillerword-cutting-optimized-for-greek-romanian-and-hungarian/)
- [Automatic Video Cutting](https://auphonic.com/blog/2026/04/15/automatic-video-cutting/)
- [Auphonic Cut Editor](https://auphonic.com/blog/2025/05/22/new-auphonic-cut-editor/)

---

# 8. Speech-recognition preprocessing

## 8.1 Confirmed foundation

Auphonic publicly confirmed that its self-hosted speech-recognition engine uses OpenAI Whisper. It has also supported external engines such as Google Cloud Speech, Amazon Transcribe, Wit.ai, and Speechmatics.

Primary source:

- [Auphonic Whisper ASR](https://auphonic.com/blog/2022/11/08/auphonic-whisper-asr-beta/)

## 8.2 Historical founder description

Georg Holzmann described Auphonic's own speech-recognition preprocessing as:

- dividing audio into smaller regions;
- excluding music;
- sending dialog-only slices to speech services;
- recombining results with timestamps and speaker information.

Primary source:

- [Django Chat transcript](https://djangochat.com/episodes/auphonic-automated-audio-post-production/transcript)

**Evidence classification:** Historical confirmed.

### Deduction

The same semantic segmentation layer likely supports both audio processing and ASR. Auphonic probably avoids transcribing full mixed programs blindly and instead transcribes high-confidence speech regions, then maps text back to the production timeline.

**Confidence:** High.

### Unknown

Public sources do not establish Auphonic's current:

- Whisper model/version;
- decoding settings;
- VAD implementation;
- alignment model;
- diarization model;
- punctuation/normalization pipeline;
- speaker assignment method;
- current use of other ASR foundations.

---

# 9. Infrastructure and runtime profile

## 9.1 Historical service topology

Auphonic historically described:

- Django/DRF web/API services;
- Celery and RabbitMQ for long-running distributed jobs;
- a relatively modest web/database tier;
- separate machines for audio processing;
- adding processing servers as workload grew.

Primary source:

- [Django Chat transcript](https://djangochat.com/episodes/auphonic-automated-audio-post-production/transcript)

**Evidence classification:** Historical confirmed.

## 9.2 Current GPU/deep-learning evidence

Auphonic joined NVIDIA Inception to accelerate deep-learning development. It stated that one Dynamic Denoiser training cycle took almost a week on GPUs and would take months on CPUs. The current job posting also describes large-scale real-world data and GPU-server training.

Primary sources:

- [Auphonic Joins NVIDIA Inception](https://auphonic.com/blog/2022/09/21/auphonic-joins-nvidia-inception/)
- [Auphonic ML/DSP Engineer](https://auphonic.com/jobs/ml-engineer)

**Evidence classification:** Current confirmed.

## 9.3 Custom hardware and faster-than-real-time processing

Auphonic says most newer algorithms use custom hardware and therefore cannot be brought to its old desktop applications. Its current product pages say processing averages about 5% of source duration—roughly three minutes for one hour of audio.

Primary sources:

- [Auphonic Desktop Programs](https://auphonic.com/standalone)
- [Auphonic Features](https://us1.auphonic.com/features)

**Evidence classification:** Current confirmed.

### Deduction

The modern service is likely an offline heterogeneous processing platform:

```text
CPU/native stages
  ├── decode/probe
  ├── loudness/features
  ├── deterministic filters
  └── encode/metadata

GPU stages
  ├── modern denoisers
  ├── voice restoration/BWE/AutoEQ
  ├── mic-bleed model
  └── ASR/diarization as applicable
```

Parallel analysis branches and dedicated model-serving workers would be consistent with the reported average runtime, but current orchestration details are not public.

**Confidence:** High for heterogeneous CPU/GPU processing; medium for specific orchestration.

---

# 10. Encoding and desktop-era implementation clues

Auphonic's historical desktop documentation states that:

- sample-rate and bit-depth conversion used SoX high-quality resampling and dithering;
- MP3 output used LAME;
- public Auphonic repositories include forks of LAME and eyeD3;
- the desktop app bundled Python processing with Electron/PyInstaller in a later generation.

Primary sources:

- [Auphonic Leveler](https://auphonic.com/leveler)
- [Auphonic public GitHub organization](https://github.com/auphonic)
- [Django Chat transcript](https://djangochat.com/episodes/auphonic-automated-audio-post-production/transcript)

**Evidence classification:** Historical confirmed/public-code clue.

### Caution

These sources do not prove the current cloud service still uses the same SoX, LAME, eyeD3, or desktop packaging versions. They are useful historical design clues only.

---

# 11. Public repositories: what they reveal and what they do not

The Auphonic public organization includes or has included:

- Auphonic Mobile;
- API examples;
- n8n integration;
- SoundCloud integration;
- Yaafe audio-feature extraction fork;
- LAME fork;
- eyeD3 fork;
- cross-compilation/mobile build tooling.

The Yaafe fork is especially relevant because the current job posting still mentions MFCCs, VAD, FFTs, and classical features. However, a public fork does not prove current production usage or expose Auphonic's proprietary feature definitions.

Primary source:

- [Auphonic GitHub organization](https://github.com/auphonic)
- [Auphonic Yaafe fork](https://github.com/auphonic/Yaafe)

**Evidence classification:** Public-code clue.

No identified public repository exposes the current:

- Adaptive Leveler;
- neural denoisers;
- AutoEQ;
- BWE;
- Studio Voice;
- mic-bleed model;
- automatic cutting models;
- routing policy.

---

# 12. Processing-order reconstruction

The exact complete order is not published, but public facts support this likely high-level graph:

```text
INPUT / DECODE
  ↓
TECHNICAL ANALYSIS
  ├── loudness / peak / clipping
  ├── SNR / noise / signal estimates
  └── bandwidth / spectral information
  ↓
SEMANTIC ANALYSIS
  ├── speech / speaker activity
  ├── music / foreground / background
  ├── silence / noise / ambience
  └── acoustic events
  ↓
REGION / TRACK PROCESSING PLAN
  ├── denoiser type and amounts
  ├── filtering / AutoEQ / Studio Voice
  ├── cutting suggestions
  └── multitrack ownership / gate / ducking
  ↓
DENOISE / ISOLATION / DEREVERB
  ↓
VOICE RESTORATION / AUTOEQ / BWE
  ↓
ADAPTIVE LEVELING
  ↓
SHORT-TERM DYNAMICS CONTROL
  ↓
FINAL GLOBAL LOUDNESS NORMALIZATION
  ↓
TRUE-PEAK LIMITING
  ↓
ENCODING / METADATA / CHAPTERS / TRANSCRIPTS / CUTS
```

### Confidence by boundary

- Analysis before content-aware processing: **very high**.
- Denoise before Studio Voice in severe cases: **confirmed**.
- Adaptive Leveling separate from final loudness normalization: **confirmed**.
- Compression separate from Leveler strength: **confirmed behavior**.
- Exact order of AutoEQ/BWE versus Leveler: **unknown**.
- Exact placement of cutting relative to audio processing/render: **implementation detail unknown**, though cuts are persisted and editable as timeline metadata.

---

# 13. New strategic deductions for Ampersand

## 13.1 Auphonic's secret sauce is an analysis-and-control system

The public evidence increasingly suggests that Auphonic's strongest product advantage is not one universal neural model. It is a shared semantic/control layer that:

- classifies content;
- tracks speaker and microphone activity;
- estimates technical defects;
- chooses specialized processors;
- selects region-specific amounts;
- preserves content that should not be altered;
- applies smooth gain and mixing decisions;
- records metadata for editing, reporting, and feedback.

This validates Ampersand's focus on `SemanticMap`, `ProcessingRouter`, `AdaptiveLeveler`, and `QualityController` as first-class proprietary systems.

## 13.2 Training data matters more than architecture guessing

Even if Ampersand identified the broad model family behind every Auphonic feature, it would still lack:

- Auphonic's service-scale real-world distributions;
- manually labeled difficult cases;
- years of user feedback;
- hidden failure corpora;
- listening expertise;
- iteration history.

Therefore the highest-leverage Ampersand investment remains its lawful corpus, evaluation harness, artifact taxonomy, and opt-in feedback pipeline—not speculative attempts to guess exact neural layers.

## 13.3 Specialized preservation targets should be explicit

Auphonic's denoiser family is best understood by what each mode promises to preserve. Ampersand's processor contract should therefore declare:

- required semantic inputs;
- wanted-source classes;
- unwanted-source classes;
- music/ambience preservation policy;
- speech-identity risk;
- supported region types;
- attenuation/restoration controls;
- confidence and bypass rules.

## 13.4 Model output should never be the only truth

Auphonic's editor, region overrides, separate reduction amounts, and feedback mechanisms show that even mature AI models need human correction. Ampersand should expose:

- semantic regions;
- processor selections;
- gain envelopes;
- confidence;
- regional bypass/strength;
- Original/Master comparison;
- reversible edits.

---

# 14. Unresolved high-value research questions

Public-source work should continue around:

1. Whether Auphonic has published patents, theses, conference papers, or code under individual employee names.
2. Full extraction of the CC BY 4.0 talk **“Wie lernt eine Maschine? KI Audio mit Auphonic”** from SUBSCRIBE 11, which explicitly covers model-development and training considerations.
3. Historical university theses or publications by Georg Holzmann and collaborators on music information retrieval, audio classification, leveling, or noise reduction.
4. Older and current job postings that may identify model-serving, training, data, or C++ frameworks.
5. Changes in Auphonic's public Yaafe fork and whether they reveal feature-extraction modifications.
6. Public OpenAPI schemas and statistics fields added for Studio Voice, per-segment processing, cutting, and mic bleed.
7. Current CLI implementation language and package provenance, if publicly disclosed.
8. Whether external technical talks describe evaluation metrics, labeling processes, augmentation, or model families.
9. Public acknowledgments, funding programs, research partnerships, or academic collaborators.
10. Whether current production pages reveal CPU/GPU constraints or unsupported combinations that imply processor ordering.

Any new finding must continue to distinguish public fact from inference and must not use Auphonic outputs or prohibited black-box analysis.

---

# Bottom line

Public evidence now supports a much more specific reconstruction than “Auphonic uses AI”:

- historically Python/Cython/C with Django, Celery, and RabbitMQ;
- currently Python/PyTorch/NumPy/SciPy plus C/C++ and classical DSP features;
- large real-world datasets and GPU training;
- human listening/feedback and manually labeled task-specific datasets;
- a persisted semantic region model and time-varying gain/processing metadata;
- specialized denoise preservation targets;
- joint multitrack analysis;
- generative/restorative speech models after denoise;
- standards-based final mastering;
- a hybrid CPU/GPU offline service that processes much faster than real time.

The exact proprietary equations, thresholds, weights, model architectures, and training data remain unavailable. Ampersand should use these facts to design an independent system—not to chase an unattainable byte-for-byte reconstruction.