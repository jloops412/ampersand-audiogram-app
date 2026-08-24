# ADR-0014: Build an Original Dependency-Free Deterministic Edit Core

- **Status:** Accepted for issue #11 Lane B V0; rich editing tracks and Studio integration remain gated
- **Date:** 2026-08-24
- **Decision owner:** Ampersand product owner
- **Tracks:** #11, #25, #27

## Context

Ampersand needs a stable editing domain beneath its WaveSurfer presentation adapter and future transcript-driven
Studio. The model must preserve immutable source identity, avoid floating-point drift, map transcript/source/output time,
replay edits, serialize predictably, and generate an authoritative server-render plan without inheriting browser state.

Issue #11 required an audit of Dawn-Cut before choosing bounded vendoring/adaptation or an original implementation.
The audit used the upstream repository at commit `7de68fce41505d8092ec227806b8d4bea4127675` (2026-07-10), not a third-party
summary. The repository was created in June 2026, describes itself as v0.1, and carries an MIT license. Its core package
is version `0.0.0`, private/unpublished, and depends on Zod. It is pure TypeScript and demonstrates useful integer-time,
timeline, sync, EDL, property-test, and history concepts.

The same package also models a broader video editor: random clip/track IDs, frame-rate snapping, speed changes,
transitions/effects, filesystem media paths, embedded transcripts, and a multi-version `.dawn` project. Vendoring it
would import domain and supply-chain surface that Ampersand V0 neither needs nor wants to make authoritative.

## Decision

Implement Ampersand's V0 edit core independently, with no copied or adapted Dawn-Cut code.

The new `@ampersand/edit-core` package:

- has no runtime or development dependency beyond the root pinned TypeScript compiler and Node test runner;
- uses non-negative safe-integer microseconds and half-open ranges;
- persists only immutable source identity and canonical cut ranges in EDL V1;
- keeps raw transcript/provider output outside the EDL;
- resolves transcript word selections into source-bound immutable commands;
- implements undo/redo by deterministic command replay from a base EDL;
- makes cut-seam ambiguity explicit through left/right mapping bias;
- emits an FFmpeg audio render plan but never executes media or owns paths/codecs;
- rejects unknown EDL fields and non-canonical documents;
- ships generated invariant tests and a real PCM FFmpeg repeatability test.

WaveSurfer state is prohibited from all edit-core contracts. Captions, chapters, overlays, speed, multitrack, and video
rendering require later versioned contracts rather than optional unvalidated fields in V1.

## Provenance decision

Dawn-Cut remains a cited architectural reference only. No upstream source, test fixture, identifier, schema, comment,
or project format is copied or adapted. Therefore Dawn-Cut is not an Ampersand dependency, is not added to the
dependency manifest or third-party notices, and creates no runtime license obligation for this implementation.

Any future proposal to copy or adapt upstream code is a new dependency-admission decision under ADR-0003 and must pin
an exact commit, record copied paths and modifications, carry required MIT notice text, pass security/maintenance
review, and demonstrate an advantage over Ampersand's current core.

## Consequences

Ampersand gets the required deterministic contracts with a much smaller domain and no new install, bundle, network,
model, native, or license surface. Its source-asset model aligns with private object storage and durable Productions
instead of desktop filesystem paths. The EDL stays usable from a web/control plane, media worker, CLI, or future agent.

The tradeoff is that Ampersand must implement and maintain later caption/chapter/overlay and multitrack semantics itself.
V0 intentionally does not claim that those gates, Studio editing, or video rendering are complete. A PCM test proves
repeatability within the pinned test environment, not bit-exact encoding across every FFmpeg build or codec.

## Alternatives considered

### Vendor Dawn-Cut core

Rejected for V0. The core is valuable but private/unpublished, coupled to a broader video/project model, and brings a
runtime validator dependency plus maintenance/provenance surface disproportionate to Ampersand's bounded cut contract.

### Add Dawn-Cut as a package dependency

Rejected. The audited `@dawn-cut/core` package is private and not an independently consumable published release.

### Put edits in WaveSurfer Regions or React state

Rejected. Floating browser/plugin state cannot be the authoritative save/reopen/render contract.

### Store kept clips instead of cuts

Deferred. For single-source destructive omissions, canonical cuts are the smallest user-intent representation and kept
ranges are an exact derived complement. A future multitrack EDL may introduce explicit clips under a new schema.

## Rollback

Remove the edit-core package and its CI/documentation wiring. No production database, asset, recipe, or deployed runtime
currently imports V0, so rollback requires no migration. Existing Auphonic production systems are unaffected.

## Primary sources

- [Dawn-Cut audited commit](https://github.com/kwakseongjae/dawn-cut/tree/7de68fce41505d8092ec227806b8d4bea4127675)
- [Dawn-Cut core package](https://github.com/kwakseongjae/dawn-cut/blob/7de68fce41505d8092ec227806b8d4bea4127675/packages/core/package.json)
- [Dawn-Cut project persistence](https://github.com/kwakseongjae/dawn-cut/blob/7de68fce41505d8092ec227806b8d4bea4127675/packages/core/src/project.ts)
- [Dawn-Cut property tests](https://github.com/kwakseongjae/dawn-cut/blob/7de68fce41505d8092ec227806b8d4bea4127675/packages/core/src/commands.property.test.ts)
- [Dawn-Cut MIT license](https://github.com/kwakseongjae/dawn-cut/blob/7de68fce41505d8092ec227806b8d4bea4127675/LICENSE)
