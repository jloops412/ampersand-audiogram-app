# Ampersand V2 Planning Authority

**Status:** Active planning baseline  
**Last verified:** 2026-08-18  
**Branch:** `docs/ampersand-v2-research-plan-2026-08`

This directory is the durable planning authority for rebuilding Ampersand from an audiogram prototype into an independent spoken-word audio intelligence, mastering, editing, and content-repurposing platform.

The documents here are intentionally separated into product, research, architecture, roadmap, and decision records so future contributors do not have to reconstruct the strategy from chat history.

## Start here

1. [Master Plan](./MASTER_PLAN.md)
2. [Target Architecture](./architecture/TARGET_ARCHITECTURE.md)
3. [Phased Roadmap](./roadmap/PHASED_ROADMAP.md)
4. [Audio Quality Evaluation Plan](./research/AUDIO_QUALITY_EVALUATION_PLAN.md)
5. [Auphonic Capability and Research Boundary](./research/AUPHONIC_CAPABILITY_AND_RESEARCH_BOUNDARY.md)
6. [Open-Source Dependency and License Matrix](./research/OSS_DEPENDENCY_AND_LICENSE_MATRIX.md)
7. [Legacy Salvage Matrix](./research/LEGACY_SALVAGE_MATRIX.md)
8. [Security, Privacy, and Data Governance](./SECURITY_PRIVACY_AND_DATA_GOVERNANCE.md)
9. [Source Register](./research/SOURCE_REGISTER.md)

## Architecture decision records

- [ADR-0001: Refound the existing repository in place](./decisions/ADR-0001-REFOUND-IN-PLACE.md)
- [ADR-0002: Lab-first development and independent evaluation](./decisions/ADR-0002-LAB-FIRST-INDEPENDENT-EVALUATION.md)
- [ADR-0003: Dependency and model admission gates](./decisions/ADR-0003-DEPENDENCY-AND-MODEL-GATES.md)
- [ADR-0004: Workflow engine selection remains open](./decisions/ADR-0004-WORKFLOW-ENGINE-SELECTION-OPEN.md)

## Governing rules

1. **Audio quality is proven before it is productized.** The Ampersand Audio Lab and its rights-cleared evaluation corpus are developed before substantial Studio polish.
2. **Ampersand is independent, not a reverse-engineered Auphonic implementation.** Auphonic's public documentation may inform capability research. Its services, outputs, derivatives, evaluations, or learnings must not be used to benchmark, train, evaluate, or improve Ampersand without written permission from Auphonic.
3. **Human listening is the final quality gate.** Objective metrics are diagnostic evidence, not automatic truth.
4. **No dependency enters production because its repository is merely described as open source.** Code license, model/checkpoint license, training-data terms, attribution, redistribution obligations, security posture, maintenance health, and deployment constraints are reviewed separately.
5. **Provider interfaces precede provider commitments.** Storage, workflow, transcription, diarization, enhancement, restoration, waveform, and publishing implementations remain replaceable.
6. **Singletrack spoken-word mastering comes first.** Multitrack mixing, generative voice restoration, advanced social video editing, and broad publishing integrations follow only after the singletrack engine passes defined quality and reliability gates.
7. **Original media is immutable.** Processing is non-destructive, reproducible, versioned, and traceable to a recipe, engine version, dependency version, and source checksum.
8. **Privacy is a product feature.** User media must have explicit retention, deletion, access-control, consent, and model-training policies.
9. **The repository documents decisions, not just intentions.** Material architectural or research choices require an ADR or an update to an existing ADR.
10. **Unknowns stay visibly open.** A candidate is not labeled selected until its spike and exit criteria are complete.

## Decision status legend

| Status | Meaning |
|---|---|
| **Accepted** | Approved as the current direction; changes require a superseding ADR. |
| **Provisional** | Preferred direction, pending a defined spike or legal/security check. |
| **Open** | Deliberately undecided; alternatives and exit criteria are documented. |
| **Rejected** | Evaluated and not suitable for the stated use. |
| **Lab only** | Permitted for internal research but not approved for production or redistribution. |

## Documentation maintenance

Every material research update should include:

- the date verified;
- primary-source links;
- whether the result changes architecture, scope, licensing, security, quality methodology, or roadmap;
- a confidence label where a conclusion is inferred rather than explicitly documented;
- an ADR update when a decision changes.

The source register should be reviewed before implementation begins and again before any public or commercial release.