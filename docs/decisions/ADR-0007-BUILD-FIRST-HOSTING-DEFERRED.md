# ADR-0007: Build the Product First; Defer Hosting Migration Work

- **Status:** Historical; hosting destination superseded by ADR-0009
- **Current hosting decision:** [ADR-0009](./ADR-0009-GOOGLE-HOSTING-RICH-STUDIO.md)
- **Date:** 2026-08-18
- **Decision owners:** Ampersand product and engineering

## Context

The owner intends to publish the completed Ampersand web experience through ChatGPT Sites and connect an owned domain. Earlier planning expanded that intention into a separate Google-host audit, Sites compatibility proof, D1/R2 evaluation, migration epic, and DNS-cutover program.

That work over-prioritized deployment mechanics before the actual Ampersand product exists. The central risk and value remain the audio engine, semantic analysis, adaptive processing, durable production workflow, and Studio experience derived from the Auphonic public research and independent engineering direction.

## Decision

The active engineering program will focus on building:

1. the core media and production contracts;
2. the Semantic Audio Map;
3. the Processing Router;
4. the original Ampersand Adaptive Leveler;
5. deterministic filtering, loudness, and true-peak mastering;
6. admitted denoise, ASR, alignment, and diarization providers;
7. the durable singletrack processing pipeline;
8. the Studio waveform, transcript, A/B comparison, processing report, controls, and exports;
9. deterministic audiogram rendering.

ChatGPT Sites remains the intended later web-hosting destination. Connecting it and the custom domain is a release/deployment activity after the product is sufficiently complete. It is not a build gate, research lane, or current proof project.

Issues #16 through #20 are closed as not planned for the current phase.

## Hosting requirements that remain relevant

The build should remain portable enough to publish later:

- web UI separated from heavy workers;
- environment-based configuration;
- no committed secrets;
- provider-neutral control APIs;
- direct/resumable uploads where needed;
- browser does not run authoritative long-form processing;
- release artifacts tied to reviewed Git commits.

These are sound product architecture requirements, not a reason to pause the build for hosting-specific validation.

## Consequences

### Positive

- agents can immediately implement the product's highest-value capabilities;
- research is converted into working engine code rather than more deployment planning;
- the backlog centers on user-visible functionality and audio quality;
- hosting beta details cannot distract or block core engineering;
- the completed product remains publishable to Sites or another compatible host later.

### Negative

- deployment incompatibilities may be discovered closer to release;
- Google-host configuration is not audited now;
- final custom-domain work remains unplanned at implementation detail;
- a later release issue will still be necessary.

These risks are acceptable because the web/worker boundary is preserved and the owner explicitly prioritizes the build.

## Required follow-up

- add `docs/build/IMPLEMENTATION_EXECUTION_PLAN.md` as the active execution authority;
- update issue #14 to prioritize actual engine and Studio build lanes;
- create implementation issues for missing Semantic Map, Router, engine vertical slice, Studio MVP, and renderer work;
- close the dedicated hosting proof issues;
- remove deployment proof work from `AGENTS.md` and the root README's immediate order;
- keep the intended ChatGPT Sites/custom-domain destination as a short deferred release note;
- create a fresh deployment issue only when the application is ready to publish.

## Supersession relationship

ADR-0006 remains a useful architectural note that heavy media processing should not be coupled to a lightweight web-host runtime. ADR-0007 supersedes its deployment workstream and makes clear that no Sites-specific proof or migration task is part of the current build phase.
