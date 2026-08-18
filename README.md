# Ampersand

**Status:** V2 research, architecture, refoundation, and deployment planning  
**Current implementation:** legacy audiogram prototype on its existing Google-hosted path  
**Target web host:** ChatGPT Sites, followed by the owner's custom domain  
**Target processing plane:** external durable CPU/GPU media workers  
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

## Start with the planning authority

- [Ampersand V2 documentation index](./docs/README.md)
- [Master Plan](./docs/MASTER_PLAN.md)
- [Target Architecture](./docs/architecture/TARGET_ARCHITECTURE.md)
- [Technology and Algorithm Direction](./docs/architecture/TECHNOLOGY_AND_ALGORITHM_DIRECTION.md)
- [ChatGPT Sites Migration and Custom-Domain Plan](./docs/deployment/CHATGPT_SITES_MIGRATION_PLAN.md)
- [Phased Roadmap](./docs/roadmap/PHASED_ROADMAP.md)
- [Audio Quality Evaluation Plan](./docs/research/AUDIO_QUALITY_EVALUATION_PLAN.md)
- [Dependency and License Matrix](./docs/research/OSS_DEPENDENCY_AND_LICENSE_MATRIX.md)
- [Auphonic Capability and Research Boundary](./docs/research/AUPHONIC_CAPABILITY_AND_RESEARCH_BOUNDARY.md)

## Important governance boundary

Ampersand is not planned as a reverse-engineered implementation of Auphonic.

Auphonic's current Terms of Service restrict using its services, outputs, derivatives, evaluations, insights, or learnings to develop, train, evaluate, benchmark, or improve a competing system, and restrict using outputs as reference material, ground truth, design input, or a quality target without a tailored arrangement.

Accordingly, Ampersand's Audio Lab will use independent rights-cleared references, synthetic degradations, human listening, standards-based measurements, and legally admissible open baselines. Auphonic services and outputs are excluded from Ampersand research unless written permission specifically authorizes the intended activity.

See the full [research boundary](./docs/research/AUPHONIC_CAPABILITY_AND_RESEARCH_BOUNDARY.md).

## Hosting and deployment boundary

ChatGPT Sites is the target host for Ampersand's supported public web experience, Studio UI, and lightweight control functions.

ChatGPT Sites is **not** the target runtime for:

- FFmpeg and native DSP;
- GPU inference;
- long-running workflow orchestration;
- model caches;
- large temporary processing data;
- the Audio Lab.

Those capabilities remain independently deployable behind versioned APIs and durable workflow contracts.

GitHub remains the source of truth. Sites releases must be saved and reviewed against a known Git commit before deployment. The current Google-hosted deployment remains rollback until the Sites/custom-domain acceptance plan passes.

See [ADR-0006](./docs/decisions/ADR-0006-CHATGPT-SITES-WEB-CONTROL-PLANE.md) and the [migration plan](./docs/deployment/CHATGPT_SITES_MIGRATION_PLAN.md).

## What is in the repository today

The current source is an early React/Vite audiogram prototype with:

- several waveform visualization styles;
- background image and text controls;
- basic SRT/VTT transcript import;
- a browser canvas preview;
- browser real-time WebM rendering;
- a legacy Express proxy to Auphonic.

This implementation is useful as history and concept validation, but it is **not the V2 architecture** and should not be treated as production-ready.

The file-level preservation and replacement decisions are documented in [Legacy Salvage Matrix](./docs/research/LEGACY_SALVAGE_MATRIX.md).

## V2 development order

1. planning authority and governance;
2. rights-cleared Audio Lab and listening harness;
3. deterministic DSP baseline and Ampersand Leveler V0;
4. model/processor bake-offs with clean-input preservation;
5. durable upload/storage/workflow architecture proof;
6. ChatGPT Sites compatibility and external-processing boundary proof;
7. singletrack Studio alpha;
8. production hardening;
9. parallel Sites deployment and custom-domain cutover;
10. deterministic editing, captions, and audiograms;
11. automation, publishing, and multitrack research.

The project deliberately does **not** begin with a major UI rewrite or immediate DNS cutover. Audio quality, legal admissibility, reproducibility, privacy, worker recovery, hosting compatibility, and rollback are the first product risks to prove.

## Contribution rules during refoundation

Before adding a dependency or model:

- verify the exact code license;
- verify the exact checkpoint/model license;
- record provenance and hashes;
- review training-data/gated-access terms;
- run the applicable Ampersand quality tests;
- document runtime, privacy, and rollback behavior;
- link an approving issue/PR or ADR.

Before changing architecture or hosting:

- update or supersede the relevant ADR;
- keep provider-specific state out of core domain schemas;
- preserve immutable source and reproducible manifests;
- avoid production dependencies on unapproved Lab-only components;
- preserve the external-worker boundary;
- never commit secret values or place them in `.openai/hosting.json`;
- save and review a Sites version before deployment;
- do not change DNS until the custom-domain issue explicitly enters cutover;
- keep Google hosting available until rollback-safe acceptance passes.

## Legacy execution

The legacy prototype should be preserved with a permanent tag before structural refactoring. Its old Auphonic integration must not be used in the Ampersand Audio Lab or as a product-quality benchmark.

Updated legacy run instructions, if still needed, should live with the legacy tag rather than define the V2 project README.

## Current planning branch

`docs/ampersand-v2-research-plan-2026-08`

## Governing epics

- #14 — Ampersand V2 independent audio intelligence and singletrack foundation
- #20 — ChatGPT Sites migration, external processing boundary, and custom-domain cutover

The next implementation work should be created from the gated roadmap and linked back to the relevant planning document.