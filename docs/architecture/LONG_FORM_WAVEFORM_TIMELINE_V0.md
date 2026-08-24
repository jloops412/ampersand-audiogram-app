# Long-Form Waveform Timeline V0

**Status:** Issue #11 Lane A implementation checkpoint; browser promotion gates remain open  
**Last verified:** 2026-08-24  
**Decision:** ADR-0013  
**Stack:** `issue-11/wavesurfer-longform-timeline` on PR #44

## Outcome

The Studio uses WaveSurfer.js 7.12.11 as a replaceable browser presentation adapter over Ampersand's existing
`WaveformPeaks` artifact and authenticated media stream. It adds a navigable source timeline, timeline labels, hover
time, zoom/scroll, keyboard seek, same-position Original/Master switching, and one bounded preview audition region.

This is not the deterministic edit core. No WaveSurfer object, floating-point region, or plugin state enters a
Production, recipe, template, report, EDL, or render request. The audition region is ephemeral and explicitly does not
trim, change, or re-render an export.

## Data and playback path

```text
immutable source
  → media worker FFmpeg stream decode
  → Ampersand multiresolution min/max peak pyramid (integer duration in microseconds)
  → canonical waveform-peaks.json + deterministic one-level waveform-studio.json
  → authenticated endpoint prefers waveform-studio.json (canonical fallback for older productions)
  → validated, budgeted Float32Array per channel
  → WaveSurfer canvas/timeline UI

authenticated original or master media endpoint
  → HTTP Range / same-origin private session
  → one external HTMLMediaElement playback clock
  → WaveSurfer cursor and bounded audition playback
```

Supplying both channel peaks and exact duration makes WaveSurfer render precomputed data instead of fetching and
decoding the full source for its waveform. The HTML media element continues to stream audio. The timeline is labeled
`Source timeline` because the same immutable-source peaks intentionally anchor both Original and Master comparison.
WAV is preferred for Master comparison when present; MP3 remains the fallback.

## Long-file peak policy

The worker emits a canonical 48 kHz peak pyramid beginning at 960 samples per window and repeatedly combines adjacent
windows. It also writes a deterministic one-level Studio sidecar using the same 240,000-sample/channel budget. The
private endpoint prefers that compact sidecar and falls back to the full pyramid for older productions. The web adapter:

1. validates positive duration, sample rate, channel count, finite ordered bounds, and exact channels per window;
2. selects the finest pyramid level whose interleaved min/max data is at most 240,000 samples per channel;
3. converts each channel to `[min, max, min, max, …]` in a `Float32Array`;
4. clamps the contract's small `±1.1` numeric tolerance to WaveSurfer's `[-1, 1]` input range;
5. rejects malformed data and leaves authenticated native streaming playback available.

The sidecar prevents new long-form browser sessions from transferring and retaining every pyramid level. The full
canonical artifact remains unchanged for provenance and downstream use. The sidecar is a partial representation of the
same logical `waveform_id`, not an independently identified manifest; its distinct representation hash is recorded in
the waveform JobStep and processing report. Real 1–3-hour transfer, parse, render, memory, and timeline-density
measurements remain hard promotion gates; the sparse unit fixture is not evidence for those gates.

## Interaction and accessibility boundary

- The native audio controls remain the semantic playback fallback.
- The waveform host is keyboard focusable: Space/K toggles, arrows seek five seconds, and Home/End seek boundaries.
- Zoom is a labeled HTML range with a Fit control; pointer-wheel zoom is not required.
- Current time and load/source state are external text with polite live status.
- The audition region has external Set 10s, Set in, Set out, numeric in/out, Play selection, and Clear controls.
- Every created or updated selection is normalized to 0.25–60 seconds. Region drag/resize is enabled only for a fine
  pointer; coarse-pointer devices retain the external controls and `pan-y` page scrolling.
- Playback/seek actions wait for both rendered peaks and the external media element's `canplay` state. Bounded audition
  playback also pauses when the tab is hidden and has a native media-time guard.
- WaveSurfer's visual Timeline and Hover plugins are enhancements, not the only time or navigation interface.

WaveSurfer publishes no accessibility conformance claim and its canvas/plugins do not supply a complete keyboard or
screen-reader interface. Browser and assistive-technology smoke tests therefore remain explicit promotion gates.

## Dependency and security evidence

| Evidence | Result |
|---|---|
| Exact package | `wavesurfer.js` 7.12.11, exact npm lock; stable `latest` on 2026-08-24 |
| v8 status | `8.0.0-beta.3` is prerelease on npm's `beta` tag; deliberately not used |
| License | BSD-3-Clause; full text archived under `infra/licenses`, copied into served `/legal`, and linked in the Studio footer |
| npm tarball SHA-256 | `a337bf2548e41a7211a39b0d16bd70c32eb07cf0ba243e4eb7190f371b2f92a0` |
| Runtime dependencies | None declared; browser JavaScript/TypeScript/plugin bundles only |
| Engine identity | Media worker 0.9.0; sidecar/report output change receives a new run fingerprint/build ID |
| Vulnerability check | `npm audit --omit=dev`: zero vulnerabilities on 2026-08-24 |
| Production bundle delta | JS 202.03 → 285.60 kB raw and 61.63 → 84.79 kB gzip; CSS 29.03 → 32.14 kB raw and 6.65 → 7.21 kB gzip versus exact PR #44 head |
| External data/service | None; no CDN, analytics, model, native library, runtime download, or third-party media request |
| Private access | Existing `/api/v2` beta session; waveform and Range media endpoints remain non-public |

The machine-readable manifest remains `production_candidate`, not `approved`, until the remaining issue #11 gates pass.
It is stored separately from media-worker dependency manifests because WaveSurfer is a web runtime adapter and is not a
recipe processor. This is an issue #11 addition record, not a comprehensive web-runtime allowlist; React/ReactDOM
admission and notice coverage remains tracked in issue #12.

## Verification matrix

| Issue #11 Lane A gate | Current evidence | Status |
|---|---|---|
| No full-source browser waveform decode | Explicit load always receives server peaks plus duration; native element streams media | Implemented; browser network smoke pending |
| 1–3 hour files | Worker writes a selected-level sidecar; sparse three-hour metadata test selects 135,000 samples/channel | Architecture/unit pass only; real transfer/parse/render/memory fixture pending |
| Zoom, scroll, region | Core zoom plus Timeline/Hover/Regions; creation/update normalization enforces one 0.25–60s audition | Implemented; browser smoke pending |
| Timing and VBR | One media clock, guarded source loads, position clamp, WAV preference, Range endpoint test | Real A/B tolerance and VBR fixtures pending |
| Multichannel | Per-channel conversion and mismatch rejection unit tests | Unit pass; browser visual smoke pending |
| Keyboard/screen reader | Native controls, labeled host/range/buttons/inputs/live state | Code/build pass; assistive-technology smoke pending |
| Responsive/mobile | Compact CSS; coarse-pointer region drag disabled; external controls remain available | Code/build pass; device smoke pending |
| License/security/bundle | Exact pin/hash/license/no-dependency/audit; served notice/license asserted in build | Pass for candidate status |

Lane B remains open: integer-microsecond EDL contracts, transcript/edit mapping, undo/redo command replay,
save/reopen/render reproducibility, and property/invariant tests.

## Rollback and release order

Rollback is to revert the issue #11 PR and restore the prior custom canvas waveform; no media artifact or domain schema
migration is required. Existing Auphonic production systems are outside this data path and remain unchanged.

This stacked work does not merge or deploy until PR #44's access/queue gate clears. Release order is #44 merge,
deployment, and smoke test; then rebase/retarget this change to reviewed `main`, rerun all gates, verify the queue again,
and only then merge/deploy this timeline separately.

## Primary sources

- [WaveSurfer.js 7.12.11 source tag](https://github.com/katspaugh/wavesurfer.js/tree/7.12.11)
- [WaveSurfer.js releases](https://github.com/katspaugh/wavesurfer.js/releases)
- [Official pre-decoded peaks documentation](https://wavesurfer.xyz/docs/peaks/)
- [Official playback and bounded-segment documentation](https://wavesurfer.xyz/docs/playback/)
- [Official Regions documentation](https://wavesurfer.xyz/docs/plugins/regions/)
- [Official Timeline documentation](https://wavesurfer.xyz/docs/plugins/timeline/)
- [Official Hover documentation](https://wavesurfer.xyz/docs/plugins/hover/)
