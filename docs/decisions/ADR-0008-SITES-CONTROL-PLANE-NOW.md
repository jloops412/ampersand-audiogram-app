# ADR-0008: Establish OpenAI Sites Now Without Collapsing the Engine Boundary

- **Status:** Superseded by ADR-0009 on 2026-08-20
- **Superseded by:** [ADR-0009: Keep Google Hosting and Make Studio Settings/Template-Driven](./ADR-0009-GOOGLE-HOSTING-RICH-STUDIO.md)
- **Date:** 2026-08-20
- **Decision owners:** Ampersand product and engineering

## Context

ADR-0007 correctly stopped hosting research from displacing the actual product, but it deferred the intended OpenAI Sites destination entirely. The owner has now directed the project to leave the legacy Google/AI Studio hosting assumptions and establish the Sites product surface while the independent engine is built.

## Decision

OpenAI Sites is the active home for:

- the responsive Ampersand Studio;
- authenticated product and workspace views;
- lightweight versioned control APIs;
- durable production metadata;
- supported object upload and artifact access;
- progress, reports, comparison, and user controls.

An independently deployable processing tier remains responsible for:

- FFmpeg and libebur128;
- native DSP and optional approved CPU/GPU models;
- long-running durable workflows;
- large temporary media and model caches;
- authoritative audio and video rendering.

Sites and engine implementation proceed together behind Ampersand-owned contracts. The custom domain and final retirement of the legacy Google-hosted surface remain release-readiness tasks.

## Consequences

- product UX and deployment truth can mature alongside engine contracts;
- the browser and Sites runtime do not become accidental long-form processors;
- D1/R2 may implement the Sites metadata/blob boundary where they fit, without becoming permanent provider-native domain schemas;
- GitHub remains the durable planning and implementation authority;
- a polished shell does not count as engine progress, and engine research does not justify postponing a usable Studio.

## Active issues

- #17 — Sites product/control-plane foundation;
- #18 — upload, storage, progress, and external-worker boundary;
- #20 — governing Sites migration epic;
- #19 — later custom-domain and legacy-host cutover.

## Supersession

ADR-0007 remains historically useful for its warning against hosting-driven drift. This ADR supersedes only its decision to defer Sites implementation.

The owner subsequently chose to keep the existing Google-hosted deployment. ADR-0009 therefore supersedes this ADR's production-host selection while preserving its useful lightweight-web/independent-worker boundary and the Sites checkpoint as a reference artifact.
