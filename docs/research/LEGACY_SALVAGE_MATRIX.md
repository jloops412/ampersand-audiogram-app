# Legacy Prototype Salvage Matrix

**Status:** Accepted refoundation assessment  
**Repository reviewed:** `jloops412/ampersand-audiogram-app`  
**Legacy head reviewed:** `a5e234b04533d51025a9d0bde00bb584f2cc48fe`  
**Last verified:** 2026-08-18

## Executive assessment

The existing repository is valuable as a product prototype and history record, but it is not an appropriate architecture for Ampersand V2.

The strongest reusable value is in:

- audiogram concepts;
- waveform style vocabulary;
- caption/transcript import concepts;
- basic preview interactions;
- proof that audio, background imagery, captions, and visualization can be composed;
- the repository identity and historical context.

The weakest areas are the exact areas V2 needs most:

- durable productions and jobs;
- independent audio processing;
- resumable media ingest;
- storage and database domain model;
- server-side deterministic export;
- processing quality evaluation;
- security/privacy governance;
- dependency/model governance;
- scalable responsive Studio UX.

Recommendation: **preserve history, tag/archive the prototype, and refound in place. Do not incrementally stretch the current App/Express/browser-rendering structure into V2.**

## Current architecture summary

```text
React/Vite application
  ├── browser AudioContext decode
  ├── static canvas preview
  ├── fixed control sidebar
  ├── optional transcript file parser
  ├── optional Auphonic proxy workflow
  └── browser real-time canvas/audio MediaRecorder export

Express server
  ├── server-wide Auphonic username/password
  ├── multipart upload to local temporary directory
  ├── create/poll/download Auphonic production
  └── serve built frontend
```

The backend does not contain an Ampersand mastering engine. The browser export path plays the recording and records a canvas stream, so long exports are tied to real time and browser/runtime behavior.

## File-by-file disposition

| Path | Current responsibility | Disposition | Rationale / V2 action |
|---|---|---|---|
| `README.md` | Generic AI Studio run instructions and Gemini key reference | **Replace** | It does not describe the actual Auphonic proxy/audiogram architecture or V2 direction. Preserve in Git history only. |
| `howto.md` | Empty | **Remove or repurpose** | No content to preserve. |
| `metadata.json` | Prototype metadata | **Audit then remove/replace** | Do not retain unknown scaffolding by inertia. |
| `package.json` | Minimal React/Vite dependencies and scripts | **Replace through refoundation** | Lacks tests, linting, workspace organization, contracts, workers, and quality tooling. |
| `Dockerfile` | Builds frontend and Node backend into one Node 18 image | **Replace** | V2 requires separate web/control and media-worker images, pinned native dependencies, SBOM, health checks, and non-root hardening. |
| `backend/server.js` | Express static server and Auphonic API proxy | **Quarantine; do not extend** | No durable domain model, shared credentials, local temp uploads, polling, no queue/checkpoints. Legacy provider must not enter Audio Lab. |
| `backend/package.json` | Express proxy dependencies | **Replace** | V2 backend/control plane should be derived from domain requirements, not this server. |
| `src/App.tsx` | Global file/options/generation state and workflow | **Rewrite** | Production state must be server durable; source, analysis, runs, and outputs require domain objects. Component currently couples UI to processing. |
| `src/components/ControlPanel.tsx` | Fixed 384px-style settings sidebar | **Concept reference only** | Preserve inventory of user-adjustable visual properties, but replace UX with progressive presets, contextual inspector, timeline, and output workflow. |
| `src/components/FileUpload.tsx` | Basic local file input | **Replace** | V2 needs resumable direct-to-object-storage upload, validation, progress, cancellation, and recovery. |
| `src/components/Preview.tsx` | Static canvas preview with duplicated drawing logic | **Concept/code-fragment reference** | Some drawing math may inform a future render-spec implementation, but preview/export must share one renderer contract. |
| `src/components/icons.tsx` | Small prototype icon set | **Optional salvage** | Keep only if visually suitable and license/origin is verified; otherwise use the V2 design system. |
| `src/services/audioService.ts` | Browser decode and static peak calculation | **Replace** | Whole-file browser decode is unsafe for long media. Use precomputed peaks and streamed playback. Peak algorithm can inform tests only. |
| `src/services/auphonicService.ts` | Upload/poll/download against local proxy | **Quarantine** | Explicitly excluded from Lab. Any future connector requires a separate legal/product decision. |
| `src/services/transcriptService.ts` | Simple SRT/VTT parsing | **Salvage behavior; replace implementation with tests** | Useful basic behavior, but needs robust parsing, cue settings, encoding/newline handling, malformed input, word timing, speakers, and schema versioning. |
| `src/services/api.ts` | Browser-facing `createAudiogram` wrapper | **Replace** | The API is not headless: it creates DOM canvas and calls browser generation. V2 needs server-durable production APIs and a shared render spec. |
| `src/services/videoService.ts` | AudioContext playback + canvas capture + VP9 WebM MediaRecorder | **Retire** | Real-time, browser-dependent, codec-limited, non-resumable, and inappropriate for long/batch/server processing. Preserve visual behavior ideas only. |
| `src/types.ts` | Waveform styles and customization options | **Partial salvage** | Waveform vocabulary is useful. Replace monolithic options with versioned render spec, recipe, timeline, caption, and output schemas. |
| `src/constants.ts` | Fixed 1080×1080 canvas and defaults | **Replace; salvage visual defaults only** | Aspect ratio/output size must be per-output metadata. Default styles can seed template research. |
| `src/index.tsx`, `index.html`, Vite/TS config | Prototype application shell | **Replace as needed** | May remain during transition but should not constrain workspace/framework choice. |

## Reusable product concepts

### Waveform visualization vocabulary

The prototype defines:

- Line;
- Mirrored Line;
- Bars;
- Bricks;
- Circle;
- Radial;
- Particles;
- Equalizer.

These should be converted into a versioned render-spec vocabulary. The visual implementations require quality, performance, accessibility, and preview/export parity tests before reuse.

### Audiogram inputs

Useful concepts:

- source audio;
- background image;
- transcript/captions;
- static overlay text;
- waveform and text styling;
- live preview;
- downloadable render.

V2 should extend these with:

- templates and brand kits;
- arbitrary output ratios;
- clip ranges;
- word-level captions;
- caption highlighting;
- deterministic server rendering;
- H.264 MP4 as a common delivery output;
- reusable media/render manifests.

### Transcript import

SRT/VTT import is worth preserving as a supported workflow, but it must map into a normalized transcript/caption schema rather than remain a loose array owned by React state.

### Programmatic creation intent

The comments around a “headless, developer-friendly API” reflect a good product direction even though the implementation is browser-bound. V2 should provide a real production API after the domain model and durable workflow are proven.

## Do not carry forward

- server-wide Auphonic customer credentials;
- Auphonic output as Ampersand evaluation or design input;
- local multipart uploads through the application server;
- whole-file browser decoding as the only waveform path;
- browser real-time rendering as authoritative export;
- one global React component owning workflow truth;
- fixed square output;
- WebM-only assumptions;
- user-facing low-level controls as the primary first-run experience;
- duplicated preview/export drawing code;
- unversioned option objects;
- generated object URLs without durable lifecycle/provenance;
- polling loops as the primary workflow model;
- generic error strings without step/failure identity.

## Preservation plan

Before structural implementation begins:

1. create a permanent legacy tag such as `legacy-audiogram-v0` at the reviewed commit;
2. preserve screenshots or a short screen recording if the prototype can still run safely;
3. archive a visual behavior checklist for waveform styles;
4. extract legal/provenance information for any images, fonts, icons, or generated assets before reuse;
5. create tests for any transcript parsing or rendering behavior intentionally preserved;
6. move legacy application code under a clearly marked path only if necessary during transition; otherwise rely on the tag/history;
7. prevent the legacy Auphonic integration from running in Lab or V2 CI.

## Refoundation sequence

### Stage 1 — planning and contracts

- merge V2 planning authority;
- add source/license/security manifests;
- define domain schemas and provider contracts;
- establish monorepo/workspace skeleton;
- keep legacy runtime unchanged on its tag.

### Stage 2 — Audio Lab and workers

- implement rights-cleared corpus manifests;
- implement processor adapters and experiment runner;
- add deterministic DSP baseline;
- build listening harness;
- no customer-facing migration yet.

### Stage 3 — durable production spine

- implement resumable object upload;
- create Production/Run/Step/Asset/Recipe schema;
- prove checkpoint/recovery;
- add minimal Original/Master playback.

### Stage 4 — Studio shell

- new responsive library and production UI;
- waveform/semantic timeline;
- contextual inspector;
- processing report;
- output workflow.

### Stage 5 — audiogram migration

- translate approved waveform styles into render spec;
- implement browser preview plus deterministic server renderer;
- add caption and aspect-ratio tests;
- retire the legacy browser renderer.

## Completion criteria

Legacy refoundation is complete when:

- the legacy commit/tag remains accessible;
- no V2 production path calls `backend/server.js` or the legacy Auphonic proxy;
- no V2 authoritative export calls `MediaRecorder` on a real-time canvas capture;
- all intentionally reused behavior has tests and provenance;
- root documentation points to V2 architecture and clearly labels the prototype;
- new implementation decisions are governed by the V2 ADRs and quality gates.