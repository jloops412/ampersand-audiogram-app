# Auphonic Public Reconstruction Matrix

**Status:** Active research assessment  
**Last verified:** 2026-08-18  
**Scope:** Public documentation, public repositories, public talks/interviews, standards, and public API schemas only

## Executive conclusion

Public research can recover a detailed functional and architectural blueprint of Auphonic, including its complete control surface, processor categories, many processing-order clues, several exact implementation facts, and the broad decision logic behind most tools.

Public research cannot recover the exact proprietary implementation of Auphonic's core Adaptive Leveler, modern neural denoisers, Voice AutoEQ, Bandwidth Extension, Studio Voice, mic-bleed removal, or automatic cutting models. Missing information includes model architectures, weights, training data, loss functions, feature representations, thresholds, smoothing constants, gain-control laws, filter coefficients, and routing policies.

Auphonic's current Terms of Service prohibit using its services, outputs, derivatives, evaluations, insights, or learnings to develop, train, evaluate, benchmark, reverse engineer, or build a competing system without a tailored arrangement. Therefore this matrix is limited to public-source research and independent engineering.

## Confidence labels

| Label | Meaning |
|---|---|
| **Confirmed exact** | Auphonic publicly identifies the component or exact implementation fact. |
| **Confirmed behavior** | Auphonic publicly describes behavior and processing purpose, but not the internal implementation. |
| **High-confidence inference** | Strongly implied by public behavior and standard engineering practice, but not explicitly disclosed. |
| **Unknown/proprietary** | Public sources do not disclose enough to identify the implementation. |
| **Historical clue only** | Public repository or old product evidence may indicate past/supporting use, not current production use. |

## Capability matrix

| Capability | Publicly confirmed | What remains unknown | Reconstruction assessment |
|---|---|---|---|
| Global loudness normalization | Program/dialog/RMS targets; standards-based loudness; constant-gain normalization; multi-pass strategy | Exact pass logic, gating details beyond standards, target-correction heuristics | **High reconstructability** using BS.1770/R128 and independent multi-pass logic |
| True-peak limiting | Final limiter uses 4× oversampling to avoid intersample peaks | Limiter topology, look-ahead, attack/release, release curve, oversampling filter | **High functional reconstructability**, not exact matching |
| Adaptive Leveler | Classifies speech, music, background/noise/silence; equalizes speakers; treats music differently; excludes unwanted regions; applies compression/limiting | Classifier models, speaker model, comfort-band math, gain targets, smoothing, maximum boost/cut, compressor topology, training process | **Medium functional reconstructability; exact implementation unavailable** |
| Broadcast Leveler | Uses MaxLRA, MaxS, MaxM constraints and master/track behavior | Optimization/control law translating constraints into gain changes | **Medium/high functional reconstructability** |
| Classic Denoiser | Segments changing noise backgrounds; extracts per-region noise prints; detects 50/60 Hz hum and harmonics; classifier determines reduction | Noise-estimation/subtraction equations, artifact controls, classifier features/thresholds | **High conceptual reconstructability** with independent spectral methods |
| Dynamic Denoiser | Preserves speech and music; removes other fast-changing/complex noise; uses semantic metadata and per-segment AI settings | Neural architecture, mask/representation, training data, dereverb/breath interaction, model routing | **Low exact reconstructability; high outcome-level replaceability with OSS models** |
| Speech Isolation | Preserves speech only and removes music/noise; per-segment AI processing | Separation architecture, conditioning, phase handling, training data | **Low exact reconstructability; medium/high substitute availability** |
| Static/Music Denoiser | Preserves speech, music, ambience, and effects while removing stationary noise/reverb; AI noise detection without noise-print silence | Model architecture, separation/restoration method, reverb model, segment transitions | **Low exact reconstructability; medium independent approximation** |
| Noise/reverb/breath controls | Separate attenuation amounts; breath removal available for selected denoisers | Whether control is mask scaling, residual mixing, post-processing, or model conditioning | **High UI/behavior reconstructability** |
| Adaptive high-pass filter | Classifies lowest wanted signal per segment; considers speech/music/noise; uses zero-phase/linear filtering | Cutoff estimator, filter order, transition bands, segmentation/smoothing | **High independent reconstructability** |
| Voice AutoEQ | Separate, time-varying spectral EQ profiles per speaker; addresses muddiness, sharpness, sibilance, plosives; described as AI voice regeneration in current materials | Reference distributions, model architecture, filter representation, speaker conditioning, temporal smoothing, training targets | **Medium conservative substitute; low exact reconstructability** |
| De-plosive | Contributed to by both AutoEQ and Dynamic/Speech-Isolation denoise paths | Detector/model, localized processing, exact interaction | **Medium independent reconstructability** |
| Bandwidth Extension | Predicts and synthesizes missing high frequencies from existing speech; voice-specific; includes AutoEQ; avoids affecting music/noise/reverb | Generative architecture, vocoder/decoder, conditioning, bandwidth detection, training data/loss | **Low exact reconstructability; medium OSS substitute potential** |
| Studio Voice | Reconstructs/regenerates voice; repairs codec artifacts, clipping/distortion, missing highs, and other processing artifacts; runs effectively after denoise | Model family, architecture, weights, training corpus, speaker/identity preservation, inference windows, objective functions | **Very low exact reconstructability; experimental independent alternatives only** |
| Silence cutting | Detects removable silence while preserving intended pauses | Detector thresholds, linguistic/context logic, crossfade policy | **High independent reconstructability** |
| Filler cutting | Trained for filler sounds across English, German, and Romance-language data; works best with denoise | Acoustic/text model, language routing, timing/fades, confidence thresholds | **Medium/high independent reconstructability** using ASR/acoustic events |
| Cough/respiratory cutting | Detects coughs, throat clearing, sneezes, related sounds | Classifier architecture, confidence, distinction from breaths/laughter | **Medium independent reconstructability** |
| Music cutting | Detects foreground music; tuned for segments longer than about 20 seconds | Music classifier, foreground/background logic, exact duration/confidence rules | **High independent reconstructability** |
| Multitrack Leveler | Joint analysis across tracks; identifies active speaker/track; balances within and across tracks; speech compression; music preservation | Speaker/track ownership model, gain solver, overlap handling, compression/control laws | **Medium functional reconstructability, difficult quality tuning** |
| Adaptive Noise Gate | Uses speaker/music activity to set threshold, ratio, sustain, and related gate/expander parameters automatically | Parameter mapping, detector confidence, fades/hysteresis | **High functional reconstructability** |
| Mic-bleed removal | Identifies active speaker/track and removes same/correlated signals from other tracks; newer materials describe joint-track modeling | Joint model architecture, alignment/drift handling, separation objective, room preservation | **Low exact reconstructability; advanced R&D** |
| Ducking/foreground-background | Classifies foreground/background and reduces background tracks while speakers are active; exposes fade/level controls | Classifier and gain-envelope details | **High independent reconstructability** |
| ASR | Self-hosted OpenAI Whisper is explicitly confirmed; external Google, Amazon, Wit.ai, and Speechmatics integrations have also been documented | Exact Whisper version/model, preprocessing, segmentation, decoding settings, post-processing, current model upgrades | **Partly exact; surrounding pipeline proprietary** |
| Diarization/speaker naming | Speaker diarization and speaker labels exposed in workflow | Exact diarization model and speaker-assignment pipeline | **Medium substitute availability** |
| AI shownotes/chapters | Generated from speech recognition and production context | Exact LLM/model/provider, prompts, grounding, versioning | **Unknown and replaceable** |
| Encoding and metadata | Broad output formats, chapter/metadata mapping, API schemas; public Auphonic forks include LAME and eyeD3 | Current production encoder versions/build flags and metadata stack | **High functional reconstructability; public repos are historical clues only** |
| Audio feature extraction | Auphonic public organization maintains a Yaafe fork described as audio-feature extraction | Whether and where Yaafe is used in current production; custom features/models | **Historical clue only** |
| API/workflow | Public REST/OpenAPI, CLI, presets, external services | Internal orchestration/storage architecture | **Control surface reconstructable; backend internals not disclosed** |

## Public code evidence

Auphonic's public GitHub organization exposes applications, API examples, workflow integrations, and forks/supporting tools including:

- Auphonic Mobile;
- API examples;
- Yaafe audio feature extraction;
- LAME;
- eyeD3;
- MXE;
- SoundCloud integration;
- n8n integration.

No public repository identified in the organization exposes the current core Adaptive Leveler, neural denoisers, AutoEQ, BWE, Studio Voice, mic-bleed model, or cutting-model implementation.

These repositories provide useful dependency and historical clues but do not prove current production usage. The Yaafe fork is especially relevant as evidence that Auphonic has worked with conventional audio feature extraction, but it must not be treated as proof that current classifiers use Yaafe or any specific feature set.

## Public implementation facts that are unusually valuable

The following details are concrete enough to influence an independent design without copying proprietary internals:

1. Analysis and semantic segmentation precede many processing decisions.
2. Speech, music, foreground/background, silence, noise types, and speakers are treated differently.
3. Leveling, compression, final loudness normalization, and true-peak limiting are separate stages/concepts.
4. Noise reduction is a family of specialized processors, not one universal model.
5. Classic denoise uses per-region noise prints and hum-harmonic analysis.
6. Modern denoisers can be selected per segment and expose separate noise/reverb/breath amounts.
7. Adaptive filtering operates per segment and preserves wanted low-frequency content.
8. AutoEQ is speaker-specific and time-varying.
9. BWE and Studio Voice are generative/restorative, not ordinary EQ.
10. Studio Voice runs after denoise in severe cases to repair speech damage.
11. Multitrack processing uses cross-track information rather than isolated per-track processing.
12. Automatic edits remain timeline metadata that can be adjusted or exported.

## What cannot be recovered responsibly from public research

Without source access, a patent-level disclosure, a technical paper, or a direct license/partnership, public research cannot establish the exact:

- model architectures and parameter counts;
- model weights;
- training/validation data;
- data labeling processes;
- loss functions;
- feature representations;
- classifier thresholds;
- confidence calibration;
- per-segment routing rules;
- Leveler target/comfort-band mathematics;
- attack/release/smoothing constants;
- compressor/limiter curves;
- filter orders and coefficients;
- denoise mask generation and phase treatment;
- AutoEQ target curves;
- generative vocoder/decoder architecture;
- mic-bleed separation model;
- cutting-model architecture and boundary adjustment rules;
- daily adaptation/retraining process;
- current production dependency versions and infrastructure.

## Research methods permitted for Ampersand

- read and archive public Auphonic documentation and API schemas;
- review public Auphonic repositories without copying restricted/proprietary code;
- study public interviews, talks, job postings, standards, and general research;
- map public behaviors to independent open-source/research alternatives;
- develop original algorithms from standards and rights-cleared data;
- evaluate on Ampersand's independent corpus;
- contact Auphonic for a written tailored arrangement, partnership, or licensing discussion.

## Research methods excluded without written permission

- controlled input/output characterization using Auphonic services;
- black-box parameter inference from Auphonic outputs;
- decompiling desktop or CLI binaries;
- extracting model files or implementation details from distributed software;
- tuning Ampersand toward Auphonic output;
- using Auphonic examples/outputs as reference, training, evaluation, or quality-target material;
- indirect use of those outputs through human ratings or automated agents.

## Practical implication for Ampersand

Ampersand should not pursue exact internal duplication. It should pursue independent functional equivalence through:

- a semantic timeline;
- specialized processor routing;
- an original adaptive leveler;
- conservative speaker-aware filtering;
- standards-based final mastering;
- independent speech enhancement/restoration candidates;
- rigorous human listening and clean-input preservation;
- a clearer and more controllable Studio experience.

This path can reproduce much of the customer-visible result without requiring knowledge of Auphonic's undisclosed internals.