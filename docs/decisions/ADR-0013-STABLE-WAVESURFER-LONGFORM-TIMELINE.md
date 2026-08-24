# ADR-0013: Pin Stable WaveSurfer for the Long-Form Timeline Spike

- **Status:** Accepted for issue #11 Lane A; permanent promotion remains gated
- **Date:** 2026-08-24
- **Decision owner:** Ampersand product owner
- **Tracks:** #11, #25, #26

## Context

Ampersand already owns a versioned multiresolution waveform peak pyramid, an authenticated waveform endpoint, private
HTTP Range media endpoints, and same-position Original/Master playback. The Studio's custom canvas renders a passive
first-channel overview and duplicates timeline interaction that a maintained permissive library can provide.

Deep research selected WaveSurfer as the browser lead. Verification on the implementation date found that npm's stable
`latest` is 7.12.11 while v8 is still `8.0.0-beta.3` on the `beta` tag. All required Lane A features—external media,
precomputed per-channel peaks, Timeline, Hover, Regions, zoom, and bounded playback—already exist in v7.

## Decision

Pin WaveSurfer.js exactly at 7.12.11 for the bounded private-beta timeline spike. Keep every import and library-specific
interaction inside the web timeline adapter. Retain the full Ampersand-owned peak pyramid and derive a deterministic
single-level Studio sidecar for browser delivery. Feed WaveSurfer those precomputed peaks and duration, use a single
external HTML media element as playback truth, gate seeks/playback on `canplay`, and keep the browser non-authoritative.

Use exactly one ephemeral audition region with external accessible controls. Do not persist it or expose editing/export
claims. Keep Ampersand's integer-microsecond EDL and edit-core selection independent of WaveSurfer.

Do not use a floating version or the v8 beta. Reconsider v8 only after a stable release is pinned and passes the same
long-file, timing, accessibility, mobile, security, and bundle regression suite.

## Consequences

The Studio gains maintained navigation and audition controls without a CDN, service, native build, model, paid API, or
browser media decode for waveform construction. The stable package is BSD-3-Clause and declares no runtime
dependencies. Its notice and full license ship in served `/legal` assets, while its canvas/plugins still need
Ampersand-owned accessibility controls.

The UI remains replaceable because no WaveSurfer state enters provider-neutral contracts. The custom canvas is the Git
rollback path. `production_candidate` remains the dependency admission state until real 1–3-hour browser, timing/VBR,
multichannel, assistive-technology, and mobile tests pass.

Existing production systems remain on Auphonic and are not connected to, benchmarked by, changed by, or deployed with
this Ampersand-only decision.
