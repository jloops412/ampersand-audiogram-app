# ADR-0001: Refound the Existing Repository in Place

- **Status:** Accepted
- **Date:** 2026-08-18
- **Decision owners:** Ampersand product and engineering

## Context

The current repository contains a small React/Vite audiogram prototype, an Express server that proxies Auphonic productions, basic SRT/VTT parsing, canvas waveform previews, and browser real-time WebM rendering.

It does not contain the durable domain model, independent audio engine, job orchestration, object storage, quality laboratory, security governance, or production rendering architecture required for the intended product.

The codebase is small enough that preserving its architecture would create more constraint than value. However, its Git history, waveform concepts, transcript-import behavior, and audiogram product direction remain useful.

## Decision

Refound Ampersand V2 **inside the existing repository** while preserving the legacy implementation through Git history and a permanent legacy tag.

V2 implementation will be based on new versioned domain contracts and separate web/control/media-worker responsibilities. Legacy code may be referenced or tested, but it will not define the V2 architecture.

## Consequences

### Positive

- preserves provenance and prior work;
- avoids repository fragmentation and lost context;
- permits selective migration of useful concepts;
- makes legacy versus V2 decisions explicit;
- avoids incrementally turning a browser demo into an accidental production platform;
- gives future agents one project location and planning authority.

### Negative

- repository structure will change substantially;
- some existing code will be retired rather than polished;
- a temporary legacy/V2 transition may increase navigation complexity;
- deploy scripts and current hosting assumptions will need replacement;
- a careful tag/archive step is required before destructive refactors.

## Alternatives considered

### Continue incremental improvement of the prototype

Rejected. The most important missing capabilities are architectural, not cosmetic. Extending the current App/Express/MediaRecorder design would accumulate migration debt.

### Create a completely new repository

Rejected for now. It would preserve a cleaner tree but split history, planning, issues, and context. A new repository may be considered later only for a separately deployable public SDK or research corpus.

### Fork an existing editor or audio application wholesale

Rejected. No reviewed project provides the entire desired product with an acceptable combination of architecture, maturity, license, and scope. Wholesale forking would replace build debt with integration and upstream-divergence debt.

## Required follow-up

- create `legacy-audiogram-v0` tag before structural implementation;
- update root README to identify the prototype and link V2 planning;
- create V2 workspace skeleton only after planning merge;
- preserve tests/screenshots for intentionally migrated visual/transcript behavior;
- prevent legacy Auphonic code from running in Audio Lab or V2 CI;
- use [Legacy Salvage Matrix](../research/LEGACY_SALVAGE_MATRIX.md) as the file-level migration authority.

## Supersession

A future decision may split services or SDKs into separate repositories, but it must preserve this repository as the historical/product authority or explicitly replace it through another ADR.