# Audio Quality Evaluation Plan

**Status:** Accepted methodology baseline; numerical promotion thresholds remain provisional until pilot power analysis  
**Last verified:** 2026-08-18

## Purpose

Ampersand's central product claim is that it can improve spoken-word recordings automatically without making good material worse. That claim cannot be established by model README examples, paper benchmark tables, loudness conformance alone, or a polished interface.

This plan defines an independent, reproducible quality program using rights-cleared references, known degradations, human listening, objective diagnostics, and explicit promotion gates.

Auphonic services and outputs are excluded from this evaluation unless written permission specifically authorizes their use. See [Auphonic Capability and Research Boundary](./AUPHONIC_CAPABILITY_AND_RESEARCH_BOUNDARY.md).

## Quality principles

1. **Human listening is the final gate.** Metrics diagnose; listeners decide whether the result is preferable and artifact-free.
2. **Clean-input preservation is mandatory.** A processor that improves bad material but audibly harms good material needs routing constraints, not a global default.
3. **Quality is use-case specific.** A phone-recording recipe, wedding-ceremony recipe, studio-podcast recipe, and music-under-speech recipe may choose different processing.
4. **All comparisons are loudness controlled.** Unmatched loudness creates misleading preference.
5. **No candidate sees the hidden test partition during tuning.**
6. **Every result is reproducible.** Source hash, degradation manifest, recipe, model hash, code commit, runtime, and output hash are recorded.
7. **No single score selects a winner.**
8. **Failure modes matter more than average scores.** Catastrophic voice distortion, missing words, chirping, musical noise, gating, or speaker-identity changes can disqualify a candidate despite a good mean.
9. **No-op is a valid and often correct decision.**
10. **Real-world and synthetic evidence are both required.**

## Corpus structure

### Current implementation checkpoint

[Synthetic Fixture Corpus V0](./SYNTHETIC_FIXTURE_CORPUS_V0.md) now provides deterministic mathematical controls, clean/degraded lineage, development/validation/withheld partition semantics, and an opt-in one-hour durability stream. It is sufficient for automated control-law, protection, transition, channel, reproducibility, and pipeline tests. It is deliberately insufficient for human quality promotion; Tier A/C real recordings and blinded listening remain required.

### Tier A — Clean reference speech

Purpose:

- establish ground truth;
- test clean-input preservation;
- generate deterministic degradations;
- measure full-reference quality and restoration.

Requirements:

- explicit commercial research rights;
- speaker consent and documented provenance;
- representative genders, vocal ranges, accents, languages, speaking styles, and microphone distances;
- dry studio and controlled-room material;
- mono and stereo cases where relevant;
- no copyrighted music unless separately cleared.

### Tier B — Deterministically degraded references

Create named, versioned variants from Tier A using reproducible transforms and source assets.

Initial degradation families:

- stationary HVAC/hiss at multiple SNRs;
- colored noise;
- short transient noises;
- crowd/traffic/restaurant backgrounds;
- 50 Hz and 60 Hz hum with harmonics;
- reverberation across several RT60 ranges;
- clipping and saturation;
- codec and low-bitrate artifacts;
- telephone/narrow-band and sample-rate limitations;
- spectral tilt, muffling, and harshness;
- level inconsistency within one speaker;
- level inconsistency across speakers;
- breaths and plosives;
- speech plus foreground or background music;
- abrupt environment changes;
- dropouts or signal loss for restoration research.

[audiomentations](https://github.com/iver56/audiomentations) is a preferred Lab candidate for many transformations, with fixed random seeds and complete manifests. Additional FFmpeg or custom transforms may be used when their equations and parameters are recorded.

Each generated item must retain the clean parent and a machine-readable degradation record.

### Tier C — Rights-cleared real-world recordings

Purpose:

- expose failures not represented by synthetic data;
- reflect actual customer workflows;
- test long-form reliability.

Candidate classes:

- wedding ceremonies;
- wedding speeches and toasts;
- event-room recordings;
- podcast interviews;
- phone/voicemail/audio-guestbook messages;
- narration and sermons;
- meetings and voice memos;
- dialogue from simple videos.

Requirements:

- documented right to use the recording for product research;
- participant consent appropriate to the intended use;
- removal or masking of unnecessary identifying information;
- restricted access and encrypted storage;
- clear retention/deletion policy;
- prohibition on external model-provider upload unless specifically authorized.

### Tier D — Independent engineer references

For selected difficult real-world items, commission an experienced human audio engineer to create a documented best-effort master without access to candidate identity.

The engineer reference is not assumed infallible. It provides:

- a realistic quality anchor;
- insight into necessary processing decisions;
- a comparison for tonal balance, dynamics, cleanup, and intelligibility;
- labels for defects and regions that required manual intervention.

The contract must permit evaluation use and define confidentiality, ownership, and publication rights.

### Tier E — Edge and adversarial cases

Examples:

- already excellent mastered audio;
- long silence and near-silence;
- whispers and very quiet speech;
- laughter, crying, applause, cheering, and crowd overlap;
- non-speech-only files;
- music-only files;
- multiple simultaneous speakers;
- extreme clipping;
- severe reverb;
- unsupported languages;
- very long files;
- variable sample rates, channel layouts, and broken metadata;
- corrupted or truncated files.

The expected outcome may be a safe refusal, warning, reduced processing, or no-op rather than a processed master.

## Dataset partitioning

Maintain at least three logical partitions:

- **Development:** visible during implementation and debugging;
- **Validation:** used to choose settings and compare candidate recipes;
- **Hidden test:** inaccessible during tuning and used for promotion decisions.

Speaker and recording-session leakage across partitions must be minimized. Synthetic variants of one clean parent remain in the same partition as that parent.

The corpus version must be immutable after a promotion test begins.

## Experiment unit

Every experiment receives an immutable manifest similar to:

```json
{
  "experiment_id": "exp_2026_08_001",
  "corpus_version": "ampersand-corpus-v0.1",
  "partition": "validation",
  "source_sha256": "...",
  "degradation_manifest": "degradations/hvac_snr_12_rt60_500.json",
  "processor": {
    "provider": "deepfilternet",
    "code_commit": "...",
    "checkpoint_id": "...",
    "checkpoint_sha256": "...",
    "container_digest": "..."
  },
  "recipe": "spoken_word_cleanup_v0",
  "parameters": {},
  "runtime": {
    "device": "cpu",
    "hardware_profile": "...",
    "wall_seconds": 0,
    "peak_memory_mb": 0
  },
  "output_sha256": "..."
}
```

## Candidate-render protocol

For each item:

1. validate source integrity;
2. generate or load approved degradation metadata;
3. render the unprocessed baseline and each candidate through the same canonical I/O path;
4. retain lossless intermediate output before final delivery encoding;
5. measure loudness, true peak, sample peak, channels, duration, and clipping;
6. create loudness-matched listening versions without changing the archived master;
7. assign opaque random identifiers;
8. randomize presentation order per listener;
9. include hidden references and anchors where the protocol requires them;
10. store objective metrics separately from listening identities until scoring is closed.

## Human listening protocols

### A. Comparative intermediate-quality assessment

For broad processing and restoration comparisons, use a MUSHRA-inspired protocol based on ITU-R BS.1534 where appropriate:

- clean reference when one exists;
- hidden reference;
- intentionally degraded anchor(s);
- randomized candidate order;
- identical playback level and segment;
- quality scale and artifact comments;
- listener-screening and consistency checks.

Official standard:

- [ITU-R BS.1534](https://www.itu.int/rec/R-REC-BS.1534/en)

### B. Noise-suppression assessment

For denoise tests, use a P.835-style structure that separates:

- **SIG:** speech-signal quality;
- **BAK:** background-noise intrusiveness/quality;
- **OVRL:** overall quality.

This prevents a heavily processed sample from winning merely because it removed more noise while damaging speech.

Official methodology:

- [ITU-T P.835](https://www.itu.int/rec/T-REC-P.835/en)

### C. Pairwise recipe preference

For product-level decisions such as “Smart Master A versus Smart Master B,” use randomized, loudness-matched, same-position pairwise preference with:

- prefer A;
- no meaningful preference;
- prefer B;
- artifact-category selection;
- confidence rating.

### D. Clean-input preservation

Listeners compare original clean material with processed output and answer:

- Is there any audible degradation?
- Did voice identity/timbre change?
- Is speech less natural?
- Were ambience, breaths, or music altered unnaturally?
- Would processing be preferable to no processing?

A default recipe should be conservative enough that already-good recordings usually remain unchanged or perceptually equivalent.

### E. Long-form continuity review

Short clips do not expose all failures. Selected full productions must be reviewed for:

- gain-envelope drift;
- inconsistent speaker treatment;
- audible transitions at processing-region boundaries;
- lost words;
- long-term listener fatigue;
- music transitions;
- render/edit synchronization;
- artifacts appearing only after many minutes.

## Listener groups

Use separate cohorts:

- audio engineers or trained listeners;
- domain professionals familiar with podcasts/events/dialogue;
- representative non-expert users;
- internal developers only for exploratory debugging, not final promotion evidence.

Exact listener counts and item counts will be established through pilot variance and statistical power analysis. Promotion reports must include confidence intervals, listener exclusions, effect sizes, and per-item failures rather than only a mean score.

## Objective diagnostics

### Standards and conformance

- integrated, short-term, and momentary loudness;
- loudness range;
- true peak and sample peak;
- clipping/overs;
- duration and synchronization;
- channel count and phase behavior;
- output-codec validation.

Use current ITU-R BS.1770 and EBU R128 guidance as applicable:

- [ITU-R BS.1770-5](https://www.itu.int/rec/R-REC-BS.1770-5-202311-I/en)
- [EBU R128](https://tech.ebu.ch/publications/r128)

### Full-reference diagnostics

When a clean reference exists:

- ViSQOL for applicable speech/audio cases;
- SI-SDR and SNR for controlled degradations;
- spectral and temporal error diagnostics;
- intelligibility measures whose implementation licenses are approved.

ViSQOL must be used within its documented input assumptions and limitations. Its own documentation notes that it may perform well for some denoise/restoration uses and poorly for others, so it is not a universal judge.

- [Google ViSQOL](https://github.com/google/visqol)

### Speech understanding

- word error rate;
- character error rate where appropriate;
- timestamp/alignment error;
- speaker diarization error rate;
- speaker-attributed word error rate;
- overlap-specific error;
- language and accent stratification.

### Performance and cost

Record per processed hour:

- wall-clock real-time factor;
- CPU/GPU model and utilization;
- peak RAM/VRAM;
- storage and temporary-storage usage;
- cloud compute cost;
- cold-start and model-load time;
- failure/retry frequency.

## Artifact taxonomy

Every listener or reviewer should be able to flag:

- musical noise;
- chirping/warbling;
- watery or phasey speech;
- robotic/generative voice changes;
- missing phonemes or words;
- pumping/breathing;
- noise gating/chopping;
- transient smearing;
- sibilance or harshness;
- muffling or lost air;
- bass boom/mud;
- plosive damage;
- reverb tail truncation;
- ambience collapse;
- music damage;
- speaker-level inconsistency;
- processing-boundary clicks or shifts;
- clipping/distortion;
- timing drift;
- identity or emotional-expression changes.

Critical artifact categories may disqualify a candidate regardless of mean preference.

## Promotion gates

A processor is promoted only for a defined use-case and parameter range, never globally by default.

### Lab candidate → approved processor

Required:

- license/security/runtime gates pass;
- beats or meaningfully complements the deterministic baseline on validation material;
- clean-input preservation is acceptable;
- no unresolved critical artifact pattern;
- hidden-test human evaluation passes;
- performance/cost is viable;
- known contraindications and fallback are documented.

### Processor → default recipe

Additional requirements:

- router can reliably identify applicable material;
- no-op behavior exists for low-confidence cases;
- full long-form review passes;
- regional transitions are inaudible or acceptably controlled;
- at least one alternative or bypass path exists;
- product copy does not overstate unsupported quality.

### Recipe → public V1

Additional requirements:

- complete provenance report;
- support matrix by input type/language/channel/runtime;
- production reliability test;
- accessible A/B comparison;
- privacy and deletion tests;
- rollback capability;
- release ADR.

## Regression program

Every processor, model, recipe, dependency, or routing change triggers an appropriate subset of:

- deterministic golden-output checks;
- loudness/peak conformance;
- clean-preservation suite;
- artifact-target suite;
- hidden mini-listening panel;
- long-file reliability run;
- ASR/diarization regression;
- performance/cost comparison.

Large model changes or routing changes require a full promotion test.

## Reporting

Each promotion report must include:

- experiment purpose and hypothesis;
- corpus version and rights status;
- candidates and exact manifests;
- listening protocol;
- objective diagnostics;
- statistical results and uncertainty;
- per-item wins/losses;
- artifact distribution;
- clean-input results;
- runtime/cost;
- known failure modes;
- decision: promote, constrain, continue research, or reject;
- approving reviewers and date.

## First pilot

The first pilot should be deliberately small but complete:

- 10–20 clean speech excerpts from multiple speakers;
- deterministic HVAC, crowd, reverb, clipping, and bandwidth degradations;
- 5–10 rights-cleared real-world clips;
- deterministic DSP/no-op baseline;
- DeepFilterNet candidate;
- one cleared ClearerVoice candidate;
- Ampersand Leveler V0 separately and in approved combinations;
- loudness-matched blinded web interface;
- P.835-style denoise ratings;
- clean-input preservation ratings;
- ViSQOL and standards measurements where applicable;
- reproducible manifests and output hashes.

The pilot's purpose is to validate the evaluation machinery and estimate variance—not to declare final product superiority.
