# Ampersand V2 Planning and Build Authority

**Status:** Active build baseline

**Last verified:** 2026-08-20
**Branch:** `main` plus reviewed issue branches

This directory is the durable authority for rebuilding Ampersand from an audiogram prototype into an independent spoken-word audio intelligence, mastering, editing, and content-repurposing platform.

## Current directive

**Build the actual Ampersand engine and Google-hosted Studio together.**

The owner's existing Google deployment remains the production web destination while the independent engine owns heavy audio work. Its exact Google service/project must be inspected only after the owner connects it at the integration stage. The OpenAI Sites checkpoint is reference-only. Rich per-production settings and immutable-versioned reusable templates are required; four intent shortcuts are not a complete Studio. ADR-0009 supersedes ADR-0008's hosting destination without weakening the engine-first quality boundaries.

## Start here

1. [Implementation Execution Plan](./build/IMPLEMENTATION_EXECUTION_PLAN.md)
2. [Master Plan](./MASTER_PLAN.md)
3. [Target Architecture](./architecture/TARGET_ARCHITECTURE.md)
4. [Technology and Algorithm Direction](./architecture/TECHNOLOGY_AND_ALGORITHM_DIRECTION.md)
5. [Phased Roadmap](./roadmap/PHASED_ROADMAP.md)
6. [Audio Quality Evaluation Plan](./research/AUDIO_QUALITY_EVALUATION_PLAN.md)
7. [Auphonic Capability and Research Boundary](./research/AUPHONIC_CAPABILITY_AND_RESEARCH_BOUNDARY.md)
8. [Auphonic Public Reconstruction Matrix](./research/AUPHONIC_PUBLIC_RECONSTRUCTION_MATRIX.md)
9. [Auphonic Public Technical Evidence Ledger](./research/AUPHONIC_PUBLIC_TECHNICAL_EVIDENCE_LEDGER.md)
10. [Auphonic Algorithm Evolution Timeline](./research/AUPHONIC_ALGORITHM_EVOLUTION_TIMELINE.md)
11. [Open-Source Dependency and License Matrix](./research/OSS_DEPENDENCY_AND_LICENSE_MATRIX.md)
12. [Legacy Salvage Matrix](./research/LEGACY_SALVAGE_MATRIX.md)
13. [Security, Privacy, and Data Governance](./SECURITY_PRIVACY_AND_DATA_GOVERNANCE.md)
14. [Source Register](./research/SOURCE_REGISTER.md)
15. [Local Engine CLI](./build/LOCAL_ENGINE_CLI.md)
16. [Semantic Audio Map V0](./architecture/SEMANTIC_AUDIO_MAP_V0.md)
17. [Studio Settings and Templates](./architecture/STUDIO_SETTINGS_AND_TEMPLATES.md)
18. [Synthetic Fixture Corpus V0](./research/SYNTHETIC_FIXTURE_CORPUS_V0.md)
19. [Blinded Listening and Regression Harness V0](./research/BLINDED_LISTENING_HARNESS_V0.md)
20. [Leveler Gain Renderer V0](./architecture/LEVELER_GAIN_RENDERER_V0.md)

## Architecture decision records

- [ADR-0001: Refound the existing repository in place](./decisions/ADR-0001-REFOUND-IN-PLACE.md)
- [ADR-0002: Lab-first development and independent evaluation](./decisions/ADR-0002-LAB-FIRST-INDEPENDENT-EVALUATION.md)
- [ADR-0003: Dependency and model admission gates](./decisions/ADR-0003-DEPENDENCY-AND-MODEL-GATES.md)
- [ADR-0004: Workflow engine selection remains open](./decisions/ADR-0004-WORKFLOW-ENGINE-SELECTION-OPEN.md)
- [ADR-0005: Provisional technology and algorithm direction](./decisions/ADR-0005-TECHNOLOGY-DIRECTION-PROVISIONAL.md)
- [ADR-0006: Historical hosting-boundary note](./decisions/ADR-0006-CHATGPT-SITES-WEB-CONTROL-PLANE.md)
- [ADR-0007: Build the product first; defer hosting migration work](./decisions/ADR-0007-BUILD-FIRST-HOSTING-DEFERRED.md)
- [ADR-0008: Establish Sites now without collapsing the engine boundary](./decisions/ADR-0008-SITES-CONTROL-PLANE-NOW.md)
- [ADR-0009: Keep Google hosting and make Studio settings/template-driven](./decisions/ADR-0009-GOOGLE-HOSTING-RICH-STUDIO.md)

## Governing rules

1. **One product, two runtime responsibilities.** The Google-hosted web/control surface implements the Studio; external workers implement high-quality media processing. Neither is a substitute for the other, and the boundary remains provider-neutral.
2. **Auphonic research becomes independent architecture.** Public findings inform capability and structure; Auphonic services/outputs/derived learnings are not used to benchmark, tune, evaluate, or design Ampersand without written permission.
3. **Ampersand owns the intelligence layer.** Semantic Map, Router, Adaptive Leveler, recipes, quality policy, and Studio explanations remain Ampersand-controlled.
4. **Human listening is the final quality gate.** Objective metrics are diagnostic evidence, not automatic truth.
5. **No dependency enters production because it is merely described as open source.** Code license, checkpoint terms, provenance, security, quality, and deployment constraints are separate gates.
6. **Provider interfaces precede provider commitments.** ASR, diarization, enhancement, storage, workflow, waveform, and render implementations remain replaceable.
7. **Singletrack spoken-word mastering comes first.** Multitrack, generative restoration defaults, broad publishing, and full social-video editing follow later.
8. **Original media is immutable.** Processing is non-destructive, reproducible, versioned, and traceable.
9. **No-op/protection is a valid result.** Clean, uncertain, musical, ambient, or unsupported content must not be processed merely because a tool exists.
10. **The browser is not the authoritative long-form processor or renderer.**
11. **Privacy is a product feature.** Retention, deletion, access, consent, and no-training defaults are part of the build.
12. **The repository documents decisions and working acceptance criteria.** Material decisions require ADR updates; speculative planning must not displace implementation.

## Active GitHub execution

### Immediate build wave

- #3 — V2 workspace/refoundation
- #12 — dependency/model manifests
- #21 — core contracts and local CLI
- #22 — Semantic Audio Map V0
- #6 — deterministic DSP and Adaptive Leveler V0
- #4/#5 — rights-cleared fixtures and quality harness

### Integration wave

- #7 — enhancement providers
- #8 — ASR/alignment/diarization providers
- #23 — Processing Router V0
- #9/#10 — durable workflow and storage lifecycle
- #24 — durable singletrack vertical slice
- #18 — Google-hosted control/upload/worker integration after owner connection

### Product wave

- #11 — waveform/edit contracts
- #25 — Studio MVP
- #31 — rich settings, reusable templates, and Google-hosting direction
- #26 — Original/Master comparison and processing report
- #13 — one-hour end-to-end proof
- #27 — deterministic audiogram renderer

Issue #31 records the owner's 2026-08-20 direction. #17, #18, #19, #20, and #25 must be read with ADR-0009: Google remains the production host, Sites is reference-only, and live deployment work waits for the owner connection.

## Decision status legend

| Status | Meaning |
|---|---|
| **Accepted** | Approved as current direction; changes require a superseding ADR. |
| **Provisional** | Preferred direction pending a defined implementation/quality/legal gate. |
| **Open** | Deliberately undecided with bounded alternatives and exit criteria. |
| **Rejected** | Evaluated and unsuitable for the stated role. |
| **Lab only** | Permitted for controlled research, not production. |
| **Deferred release task** | Intentionally postponed until a working product exists. |

## Documentation maintenance

Every material update should include:

- verification date and primary sources;
- whether architecture, implementation order, quality, licensing, privacy, or scope changed;
- confidence labels for deductions;
- ADR updates for decisions;
- issue/PR links and runnable evidence.

Before implementation begins, agents should read `AGENTS.md`, the execution plan, their assigned issue, and its linked authority documents.
