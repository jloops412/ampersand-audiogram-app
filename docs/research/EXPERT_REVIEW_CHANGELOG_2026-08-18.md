# Expert Review Changelog — 2026-08-18

This note records material changes produced by the expert-level library, repository, and algorithm review. It is not a replacement for the linked architecture or ADR documents.

## Material direction changes

### Workflow orchestration

Previous posture: Hatchet was frequently discussed as the likely production workflow engine.

Updated posture:

- Temporal is the current technical lead for customer-facing durable media workflows because of its mature event-sourced recovery model and explicit activity-idempotency semantics.
- Prefect is the preferred candidate for Audio Lab experiment orchestration and corpus sweeps.
- Hatchet remains a strong simpler challenger but must pass the full multi-day database and fault-injection suite before selection.
- ADR-0004 remains formally open.

### Waveform generation

Previous posture: BBC audiowaveform was a likely waveform-data generator.

Updated posture:

- BBC audiowaveform is GPLv3 and should not become a required V1 spine dependency without deliberate legal architecture.
- Ampersand should implement a compact independent multiresolution min/max peak pyramid.
- WaveSurfer.js is the current browser UI lead, subject to long-file/accessibility tests.

### Speech understanding

Previous posture: WhisperX/pyannote was the primary likely stack.

Updated posture:

Run a three-way comparison:

1. WhisperX + approved diarization pipeline — mature integration baseline;
2. NVIDIA Parakeet-TDT 0.6B v3 + separate diarization — fast timestamp-focused challenger;
3. MOSS-Transcribe-Diarize 0.9B — experimental joint ASR/diarization/events challenger.

Silero VAD through ONNX remains the early CPU baseline. Mastering must not fail because transcription fails.

### Enhancement

Previous posture: several model families were listed without a promotion order.

Updated posture:

- DeepFilterNet3 is the first production enhancement candidate to attempt to promote.
- ClearerVoice is the high-priority challenger family for harder noise, separation, and super-resolution.
- nara_wpe is added as a classical dereverberation Lab baseline, especially for multichannel/far-field material.
- Resemble Enhance and other generative restoration stay Lab-only and opt-in unless identity/naturalness safety is proven.

### Rendering

Previous posture: server rendering was directionally planned but not narrowed.

Updated posture:

- define one shared render specification;
- browser consumes the spec for preview;
- server renders frames with @napi-rs/canvas/Skia and encodes/muxes through FFmpeg;
- libass handles final subtitle shaping/burn-in where appropriate;
- browser MediaRecorder remains prohibited as authoritative long-form export.

### Leveler and AutoEQ

Previous posture: high-level control concepts.

Updated posture:

- the Leveler now has a concrete robust per-speaker comfort-band and regularized bounded gain-envelope direction;
- silence/noise/music/uncertainty explicitly hold or suppress gain changes;
- short-term compression follows leveling rather than replacing it;
- final global loudness normalization remains a separate stage;
- AutoEQ begins as conservative speaker-aware long-term spectral balancing with broad small corrections, not a black-box neural model.

## New planning authority

- `docs/architecture/TECHNOLOGY_AND_ALGORITHM_DIRECTION.md`
- `docs/decisions/ADR-0005-TECHNOLOGY-DIRECTION-PROVISIONAL.md`
- updated dependency/license matrix;
- updated source register;
- updated docs index.

## Unchanged hard rules

- no Auphonic outputs/services/derived learnings in Ampersand evaluation or design without written permission;
- model/checkpoint licenses verified separately from repository code;
- human listening and clean-input preservation remain mandatory;
- singletrack spoken-word foundation precedes multitrack and generative restoration;
- no candidate is production-approved until its spike and promotion gates pass.