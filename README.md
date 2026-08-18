# Ampersand

**Status:** V2 engine and Studio implementation planning  
**Current implementation:** legacy audiogram prototype  
**Immediate objective:** build the actual independent audio-processing product  
**Later release destination:** ChatGPT Sites and the owner's custom domain  
**Last planning update:** 2026-08-18

Ampersand is being refounded as an independent spoken-word audio intelligence, mastering, editing, and content-repurposing platform.

The intended product combines:

- conservative automatic spoken-word cleanup;
- content- and speaker-aware leveling;
- standards-based loudness and true-peak mastering;
- transcripts, speakers, and a semantic audio timeline;
- understandable Original/Master comparison and regional overrides;
- deterministic outputs and provenance;
- later transcript-driven editing, captions, audiograms, social clips, automation, and multitrack processing.

## Start here

- [Implementation Execution Plan](./docs/build/IMPLEMENTATION_EXECUTION_PLAN.md)
- [Ampersand V2 documentation index](./docs/README.md)
- [Master Plan](./docs/MASTER_PLAN.md)
- [Target Architecture](./docs/architecture/TARGET_ARCHITECTURE.md)
- [Technology and Algorithm Direction](./docs/architecture/TECHNOLOGY_AND_ALGORITHM_DIRECTION.md)
- [Auphonic Public Reconstruction Matrix](./docs/research/AUPHONIC_PUBLIC_RECONSTRUCTION_MATRIX.md)
- [Audio Quality Evaluation Plan](./docs/research/AUDIO_QUALITY_EVALUATION_PLAN.md)
- [Dependency and License Matrix](./docs/research/OSS_DEPENDENCY_AND_LICENSE_MATRIX.md)

## Current owner directive

**Build the product now.**

Do not spend the current development phase proving hosting compatibility, auditing Google hosting, planning DNS, or connecting the domain. ChatGPT Sites remains the intended later publication target, but it is not a prerequisite or workstream for the engine and Studio.

The active build is:

```text
source
  ↓
probe / waveform / loudness / VAD / optional ASR and speakers
  ↓
Semantic Audio Map
  ↓
Processing Router
  ├── protect / no-op
  ├── deterministic filters
  ├── admitted speech enhancement
  └── regional processing
  ↓
Ampersand Adaptive Leveler
  ↓
conservative speaker-aware EQ / filtering
  ↓
final loudness + true-peak master
  ↓
WAV / MP3 / report / later audiogram outputs
```

## Important governance boundary

Ampersand is not planned as a reverse-engineered implementation of Auphonic.

Auphonic's current Terms of Service restrict using its services, outputs, derivatives, evaluations, insights, or learnings to develop, train, evaluate, benchmark, or improve a competing system, and restrict using outputs as reference material, ground truth, design input, or a quality target without a tailored arrangement.

Accordingly, Ampersand's Audio Lab uses independent rights-cleared references, synthetic degradations, human listening, standards-based measurements, and legally admissible open baselines. Auphonic services and outputs are excluded from Ampersand research unless written permission specifically authorizes the activity.

See the [research boundary](./docs/research/AUPHONIC_CAPABILITY_AND_RESEARCH_BOUNDARY.md).

## What is in the repository today

The current source is an early React/Vite audiogram prototype with:

- several waveform visualization styles;
- background image and text controls;
- basic SRT/VTT transcript import;
- a browser canvas preview;
- browser real-time WebM rendering;
- a legacy Express proxy to Auphonic.

This implementation is useful as history and concept validation, but it is **not the V2 architecture** and should not be treated as production-ready.

See [Legacy Salvage Matrix](./docs/research/LEGACY_SALVAGE_MATRIX.md).

## Active build order

### Immediate wave

1. #3 — V2 workspace/refoundation
2. #12 — dependency/model admission manifests
3. #21 — core contracts and local processing CLI
4. #22 — Semantic Audio Map V0
5. #6 — deterministic DSP and Adaptive Leveler V0
6. #4/#5 — rights-cleared fixtures and minimal quality harness

### Integration wave

7. #7 — enhancement candidates
8. #8 — ASR/alignment/diarization providers
9. #23 — Processing Router V0
10. #9/#10 — durable workflow and storage lifecycle
11. #24 — durable singletrack engine

### Product wave

12. #11 — waveform/edit contracts
13. #25 — Studio MVP
14. #26 — Original/Master A/B and report
15. #13 — one-hour product proof
16. #27 — deterministic audiogram rendering

After these produce a working product, publish the compatible web application to ChatGPT Sites and connect the domain as a release task.

## Contribution rules

Before adding a dependency or model:

- verify exact code and checkpoint licenses;
- record provenance and hashes;
- review training-data/gated-access terms;
- run applicable quality and clean-preservation tests;
- document runtime, privacy, contraindications, and rollback;
- link an approving issue/PR or ADR.

Before changing architecture:

- update or supersede the relevant ADR;
- keep provider-specific state out of core domain schemas;
- preserve immutable source and reproducible manifests;
- avoid production dependencies on unapproved Lab-only components;
- preserve no-op/protected paths;
- implement the issue's working acceptance criteria rather than expanding speculative planning.

## Legacy execution

The legacy prototype should be preserved with a permanent tag before structural refactoring. Its old Auphonic integration must not be used in the Ampersand Audio Lab or as a product-quality benchmark.

## Current planning branch

`docs/ampersand-v2-research-plan-2026-08`

## Governing epic

- #14 — Ampersand V2 engine, Studio, and singletrack foundation

Issues #16–#20 were closed because they over-prioritized hosting proof before product implementation.