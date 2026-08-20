# Open-Source Dependency and License Matrix

**Status:** Active research register; no row alone authorizes production use  
**Last verified:** 2026-08-18

## Purpose

Ampersand should reuse mature infrastructure and open research wherever practical, but “open source” is not a sufficient production-admission criterion.

For every dependency, code license and model/checkpoint license are separate questions. Training-data terms, gated-access agreements, attribution, redistribution, hosted-service terms, patents, codec obligations, export controls, security posture, maintenance health, and transitive dependencies may also matter.

This document is an engineering planning aid, not legal advice.

## Disposition legend

| Disposition | Meaning |
|---|---|
| **Core recommendation** | Strong deterministic or infrastructure component we expect to use after build/security gates. |
| **First production candidate** | First candidate to attempt to promote through the Audio Lab; not yet approved. |
| **Current technical lead** | Best current fit, but formal provider/model ADR remains open until its spike passes. |
| **Open comparison** | Must be compared against alternatives under defined exit criteria. |
| **Lab candidate** | Approved only for controlled internal research after license verification. |
| **Reference only** | Concepts may be studied; code must not enter proprietary production without a separate decision. |
| **Deferred** | Potentially useful in a later phase. |
| **Rejected for current role** | Not appropriate for the identified production role. |

## Mandatory admission record

Before a dependency or model enters a production image, create a versioned manifest containing:

- canonical project and artifact URL;
- exact source commit/tag and package version;
- exact model/checkpoint identifier and hash;
- code license and copy of license text;
- model/checkpoint license and copy of license/model card;
- training-data terms when available;
- attribution and notice requirements;
- redistribution and hosted-use analysis;
- transitive native libraries and their licenses;
- CPU/GPU/runtime requirements;
- known security advisories and open critical issues;
- benchmark results on Ampersand's rights-cleared corpus;
- known failure modes;
- rollback and replacement plan;
- approving ADR or pull request.

## Foundational media and standards

| Candidate | Proposed role | Code/license status | Current disposition | Required gate |
|---|---|---|---|---|
| [FFmpeg](https://ffmpeg.org/) | Probe, decode, resample, filter, encode, mux, render | LGPL 2.1+ by default; a build can become GPL depending on enabled components and external libraries | **Core recommendation** | Create approved build profile; inventory codecs/linked libraries; standards/output tests |
| [libebur128](https://github.com/jiixyj/libebur128) | EBU R128 momentary, short-term, integrated loudness, LRA, and true-peak measurement | MIT | **Core recommendation** | Verify bindings; cross-check against FFmpeg and standards test vectors |
| [libsoxr](https://github.com/chirlu/soxr) | High-quality configurable resampling | LGPL-2.1+ | **Provisional native-build component** | Include only through reviewed build profile; measure quality, latency, and obligations |
| [audiomentations](https://github.com/iver56/audiomentations) | Deterministic synthetic degradations for evaluation | MIT | **Preferred Lab candidate** | Pin transformations/seeds; preserve provenance |
| [OpenTimelineIO](https://github.com/AcademySoftwareFoundation/OpenTimelineIO) | Professional timeline interchange boundary | Apache-2.0 | **Deferred recommendation** | Verify target adapters and NLE limitations separately |
| [rclone](https://github.com/rclone/rclone) | Generic external file destinations | MIT | **Deferred candidate** | Threat-model credentials; provider API terms/OAuth review |

## Upload, data, and web infrastructure

| Candidate | Proposed role | Code/license status | Current disposition | Required gate |
|---|---|---|---|---|
| [Uppy](https://github.com/transloadit/uppy) | Drag/drop and resumable media uploads | MIT | **Preferred candidate** | Direct-to-storage resume/cancel/large-file tests |
| [tus protocol / tusd](https://github.com/tus/tusd) | Resumable upload protocol or self-host fallback | MIT | **Accepted interface candidate** | Checksums, auth, cancellation, orphan cleanup |
| [Supabase](https://github.com/supabase/supabase) | Managed Postgres/Auth/Storage/Realtime candidate | Apache-2.0 repository; managed-service terms separate | **Open candidate** | Cost/security/export spike; RLS/lifecycle validation |
| PostgreSQL plus S3-compatible storage | Durable metadata and object-storage abstraction | Provider/component terms vary | **Accepted architectural interfaces** | Provider selection after retention, egress, region, backup, cost evaluation |
| [WaveSurfer.js](https://github.com/katspaugh/wavesurfer.js) | Browser playback, waveform, editable regions | BSD-3-Clause | **Current technical lead** | 1–3 hour precomputed-peaks, timing, accessibility, multichannel, mobile tests |
| [Peaks.js](https://github.com/bbc/peaks.js) | Alternative long-form waveform/segment UI | LGPL-3.0; development moved to Codeberg | **Open comparison** | Legal integration and feature/performance comparison |
| [BBC audiowaveform](https://github.com/bbc/audiowaveform) | Server-side waveform peak generation | GPLv3 | **Reference/Lab only; not V1 spine** | Prefer independent multiresolution peak generator; legal review if ever used |
| [waveform-data.js](https://github.com/bbc/waveform-data.js) | Waveform data handling | LGPL-3.0 | **Open comparison** | Legal and bundle-boundary analysis |

## Durable workflow/orchestration

The workflow-engine decision remains formally open under ADR-0004, but the expert review establishes a current ranking.

| Candidate | Strengths for Ampersand | License/status | Current disposition | Required spike |
|---|---|---|---|---|
| [Temporal](https://github.com/temporalio/temporal) | Mature event-sourced durable execution; Python SDK; crash/outage recovery; explicit Activity idempotency model | MIT | **Current production technical lead** | Managed and self-host cost/ops, history size, heartbeat/cancel, versioning, full fault suite |
| [Prefect](https://github.com/PrefectHQ/prefect) | Python-native flows, retries, caching, scheduling, experiment visibility | Apache-2.0 | **Preferred Audio Lab candidate** | Corpus sweep/caching/reproducibility; managed/self-host boundary |
| [Hatchet](https://github.com/hatchet-dev/hatchet) | Python/TypeScript, Postgres-backed queues/DAGs/durable tasks, simpler operational model | MIT | **Production challenger** | Multi-day self-host stability, DB recovery, artifact/event limits, full fault suite |
| Restate | Lightweight durable execution and Python support | License/fit not fully verified | **Research pending** | Verify license and material advantage before inclusion |
| Trigger.dev | Long-running TypeScript jobs and observability | Product licensing/hosting terms require review; Python not primary execution model | **Rejected for core Python media orchestration** | May be reconsidered for web-only tasks |

## Speech activity, transcription, diarization, and semantics

| Candidate | Proposed role | Code/license status | Model/checkpoint status | Current disposition |
|---|---|---|---|---|
| [Silero VAD](https://github.com/snakers4/silero-vad) | Early CPU speech-probability mask | MIT | Verify exact packaged model/hash | **First production candidate through ONNX** |
| [WhisperX](https://github.com/m-bain/whisperX) | ASR, VAD integration, forced alignment, diarization integration | BSD-2-Clause | Separately licensed models/dependencies including pyannote | **Mature baseline candidate** |
| [NVIDIA Parakeet-TDT 0.6B v3](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3) | Fast timestamped long-form ASR | Official model card reports CC BY 4.0 | Separate diarization required; 16 kHz mono/GPU profile | **High-priority challenger** |
| [MOSS-Transcribe-Diarize 0.9B](https://github.com/OpenMOSS/MOSS-Transcribe-Diarize) | Joint long-form ASR, diarization, timestamps, acoustic events | Apache-2.0 repository/model reported | Exact artifact hash/runtime still required | **Experimental high-priority challenger** |
| `moss-transcribe.cpp` | Emerging local/CPU inference for MOSS | MIT implementation; upstream weights separate | Reuses upstream model terms | **Lab candidate; maturity test** |
| [pyannote.audio](https://github.com/pyannote/pyannote-audio) / `speaker-diarization-community-1` | Speaker diarization | Toolkit/pipeline terms differ | Community pipeline gated, CC BY 4.0, attribution/user agreement | **Open comparison** |
| [PANNs](https://github.com/qiuqiangkong/audioset_tagging_cnn) | AudioSet semantic sound classification | MIT | Verify exact checkpoint/labels | **Lab candidate** |
| Whisper / faster-whisper | ASR substrate | Whisper repo MIT; converted/runtime artifacts separate | Exact model/conversion provenance required | **Component candidates** |

Selection must score WER/CER, word timing, DER, speaker-attributed WER, overlap behavior, language/accent, long-file reliability, CPU/GPU cost, and confidence calibration separately. Transcription failure must not block mastering.

## Speech enhancement, dereverberation, separation, and restoration

| Candidate | Proposed role | Code/license status | Model/checkpoint status | Current disposition |
|---|---|---|---|---|
| [DeepFilterNet](https://github.com/Rikorose/DeepFilterNet) | Full-band 48 kHz dynamic speech denoise | Dual MIT/Apache-2.0 repository | Verify exact bundled/released checkpoint | **First production enhancement candidate** |
| [ClearerVoice-Studio](https://github.com/modelscope/ClearerVoice-Studio) | 16/48 kHz enhancement, separation, super-resolution, target-speaker extraction | Apache-2.0 repository | Verify each selected checkpoint separately | **High-priority Lab challenger family** |
| [nara_wpe](https://github.com/fgnt/nara_wpe) | Weighted Prediction Error dereverberation | MIT | No model weight required for core algorithm | **Lab baseline, especially multichannel/far-field** |
| [Resemble Enhance](https://github.com/resemble-ai/resemble-enhance) | Denoise plus generative/restorative bandwidth experiment | MIT repository | Verify checkpoint/provenance | **Lab only; not default** |
| [RNNoise](https://github.com/xiph/rnnoise) | Lightweight neural-denoise fallback | BSD-3-Clause | Verify build/model | **Fallback candidate** |
| [Audio Separator](https://github.com/nomadkaraoke/python-audio-separator) | Separation-model research wrapper | Wrapper permissive; model families vary | Every downloaded model requires separate review | **Lab only** |
| [Asteroid](https://github.com/asteroid-team/asteroid) | Speech separation/enhancement research framework | MIT | Recipes/models separate | **Research/reference framework** |
| [SpeechBrain](https://github.com/speechbrain/speechbrain) | Broad speech research toolkit | Apache-2.0 | Recipe/checkpoint terms separate | **Research/reference framework** |

No model is selected by README demos or paper averages. Promotion is region/use-case bounded and requires clean-input preservation.

## Rendering and subtitle stack

| Candidate | Proposed role | License/status | Current disposition | Required gate |
|---|---|---|---|---|
| [@napi-rs/canvas](https://github.com/Brooooooklyn/canvas) | Node/Skia deterministic frame rendering | MIT | **Provisional recommendation** | Font, layout, performance, preview/export parity spike |
| [libass](https://github.com/libass/libass) | Final ASS/SSA subtitle shaping/burn-in through FFmpeg | ISC | **Strong recommendation** | Font licensing/embedding, target-platform render tests |
| FFmpeg video/audio encoder | Frame/audio encode and mux | Build-license profile varies | **Core recommendation** | H.264/codec build and distribution review |
| Motion Canvas | Code-driven animation/templates | MIT | **Optional Lab/template prototype only** | Use only if shared render spec integration is simpler than custom engine |

## Editing and interchange substrates

| Candidate | Proposed role | License/status | Current disposition | Required gate |
|---|---|---|---|---|
| Dawn-Cut | Deterministic TypeScript edit core and invariants | MIT; young | **Architecture audit / bounded vendoring candidate** | Code audit, project format, save/reopen/render proof |
| CutScript | Reference for WhisperX, text edit, DeepFilterNet, FFmpeg export | MIT; young desktop project | **Reference and spike source** | Do not fork wholesale |
| Auto-Editor CLI | Silence/loudness edit behavior and NLE export | Open CLI boundary must be pinned | **Lab/reference candidate** | Verify exact commit/license boundaries |
| OpenTimelineIO | NLE interchange | Apache-2.0 | **Deferred recommendation** | Adapter compatibility/limitations matrix |
| Waveform Playlist / dawcore | Later multitrack editor | MIT reported | **Deferred** | Re-evaluate after singletrack V1 |
| OpenCut | Later social/video editor | MIT reported; active rewrite | **Deferred/watch upstream** | No V1 dependency |

## Evaluation tools and metrics

| Candidate | Role | License/status | Current disposition |
|---|---|---|---|
| [ViSQOL](https://github.com/google/visqol) | Full-reference perceptual quality diagnostic | Apache-2.0 | **Preferred diagnostic metric for applicable cases** |
| [pystoi](https://github.com/mpariente/pystoi) | STOI/eSTOI intelligibility diagnostic | MIT | **Approved candidate when clean reference exists** |
| EBU R128 / BS.1770 | Loudness/peak conformance | Standards | **Required** |
| BS.1534/MUSHRA-style listening | Comparative human assessment | Standard methodology | **Required where applicable** |
| P.835 SIG/BAK/OVRL | Denoise assessment | Standard methodology | **Preferred denoise protocol** |
| NISQA public pretrained weights | Non-intrusive speech quality | Common weights CC BY-NC-SA | **Rejected for commercial production-selection logic** |
| DNS Challenge tooling/data | Enhancement research/evaluation | Code permissive; dataset elements vary | **Lab/reference with item-level rights review** |
| PESQ, DNSMOS, SI-SDR, SNR | Diagnostics | Implementations/assets differ | **Per-implementation review; never sole judge** |

## Copyleft/reference boundary

These may contain useful ideas but require deliberate legal architecture before code use:

- BBC audiowaveform — GPLv3;
- Peaks.js / waveform-data.js — LGPL-3.0;
- `master_me` — GPL;
- PodcastPlugins — GPL;
- Spotify Pedalboard — current GPLv3 distribution concerns;
- Essentia — AGPL in standard open distribution;
- Matchering — GPL;
- Mutagen — GPL-2+;
- projects that moved to noncommercial/source-available licensing.

Studying public behavior/documentation is not permission to copy source. Automated contributors must not translate or reproduce reference-only implementations into proprietary modules.

## Production promotion checklist

A candidate moves from Lab to production only when:

- [ ] exact code and model versions/hashes are pinned;
- [ ] code and checkpoint licenses are archived;
- [ ] commercial hosted use and redistribution are permitted;
- [ ] attribution/notices are implemented;
- [ ] dependency security scan passes;
- [ ] container build is reproducible;
- [ ] CPU/GPU resource profile is recorded;
- [ ] quality tests pass for intended use cases;
- [ ] clean-input preservation passes;
- [ ] failure modes and contraindications are documented;
- [ ] privacy/data-flow review passes;
- [ ] rollback or alternative provider exists;
- [ ] approving ADR/PR is linked.

## Current implementation priorities

1. Controlled FFmpeg/libebur128/libsoxr build and standards fixtures.
2. Semantic Map, processor/model, gain-envelope, and artifact contracts.
3. Independent multiresolution waveform peak generator.
4. Silero VAD ONNX integration.
5. Ampersand Leveler V0.
6. DeepFilterNet adapter and listening bake-off.
7. ClearerVoice challenger bake-off.
8. WhisperX/Parakeet/MOSS ASR-diarization comparison.
9. Temporal/Hatchet/Prefect fault-injection spike.
10. @napi-rs/canvas + FFmpeg/libass render-spec proof.
11. SBOM, third-party notices, verified model registry, and production allowlist.