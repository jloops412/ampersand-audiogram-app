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
| **Preferred candidate** | Strong candidate for an implementation spike; not selected until gates pass. |
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
| [FFmpeg](https://ffmpeg.org/) | Probe, decode, resample, filter, encode, mux, render | LGPL 2.1+ by default; a build can become GPL depending on enabled components and external libraries | **Preferred candidate** as controlled system dependency | Create an approved build profile; inventory codecs and linked libraries; publish notices/source obligations as required |
| [libebur128](https://github.com/jiixyj/libebur128) | EBU R128 momentary, short-term, integrated loudness, LRA, and true-peak measurement | MIT | **Preferred candidate** | Verify maintenance and bindings; cross-check against FFmpeg and standards test vectors |
| [audiomentations](https://github.com/iver56/audiomentations) | Deterministic synthetic degradations for the evaluation corpus | MIT | **Preferred Lab candidate** | Pin transformations and random seeds; maintain provenance for every generated sample |
| [OpenTimelineIO](https://github.com/AcademySoftwareFoundation/OpenTimelineIO) | Professional timeline interchange boundary | Apache-2.0 | **Deferred preferred candidate** | Verify each target adapter and NLE compatibility separately; do not use as the primary transcript model |
| [rclone](https://github.com/rclone/rclone) | Generic external file destinations | MIT | **Deferred candidate** | Threat-model credential storage; verify provider API terms and supported OAuth flows |

## Upload, data, and web infrastructure

| Candidate | Proposed role | Code/license status | Current disposition | Required gate |
|---|---|---|---|---|
| [Uppy](https://github.com/transloadit/uppy) | Drag/drop and resumable media uploads | MIT | **Preferred candidate** | Direct-to-storage spike; resume after browser/process interruption; large-file tests |
| [tus protocol / tusd](https://github.com/tus/tusd) | Resumable upload protocol or self-hosted fallback | MIT | **Preferred interface** | Verify object-store integration, checksums, cancellation, auth, and orphan cleanup |
| [Supabase](https://github.com/supabase/supabase) | Managed Postgres/Auth/Storage/Realtime candidate | Apache-2.0 repository; managed-service terms remain separate | **Open candidate** | Architecture/cost/security spike; export/exit test; storage lifecycle and RLS validation |
| PostgreSQL plus S3-compatible storage | Durable metadata and object-storage abstraction | Provider and component terms vary | **Accepted architectural interfaces** | Select provider only after retention, egress, resumability, regional, backup, and cost evaluation |
| [WaveSurfer.js](https://github.com/katspaugh/wavesurfer.js) | Browser playback, waveform, and editable regions | BSD-3-Clause | **Preferred waveform UI candidate** | Long-file spike with precomputed peaks; accessibility, multichannel, zoom, and timing accuracy |
| [Peaks.js](https://github.com/bbc/peaks.js) | Alternative long-form waveform/segment UI | LGPL-3.0; active development has moved from GitHub to Codeberg | **Open comparison** | Legal integration analysis plus feature/performance comparison with WaveSurfer |
| [BBC audiowaveform](https://github.com/bbc/audiowaveform) | Server-side waveform peak generation | GPLv3 | **Lab/reference; not default production choice** | Legal review of subprocess/distribution model; compare with a permissive in-house/FFmpeg peak generator |
| [waveform-data.js](https://github.com/bbc/waveform-data.js) | Waveform data handling | LGPL-3.0 | **Open comparison** | Legal and bundle-boundary analysis |

## Durable workflow/orchestration

The workflow-engine decision is intentionally open. See ADR-0004.

| Candidate | Strengths for Ampersand | License/status | Current disposition | Required spike |
|---|---|---|---|---|
| [Hatchet](https://github.com/hatchet-dev/hatchet) | Python and TypeScript SDKs; queues, DAGs, retries, durable tasks, monitoring | MIT | **Open comparison** | Managed and self-hosted fault injection; long-run stability; resume semantics; artifact/event size; cost |
| [Temporal](https://github.com/temporalio/temporal) | Mature event-sourced durable execution; strong recovery semantics; Python SDK | MIT | **Open comparison** | Operational complexity, developer ergonomics, child-workflow/media-step model, managed cost |
| [Prefect](https://github.com/PrefectHQ/prefect) | Python-native workflows, retries, caching, orchestration UI | Apache-2.0 | **Open comparison** | Durable recovery, concurrency, cancellation, deployment model, self-host/managed feature parity |
| Restate | Lightweight durable execution and Python support | License and production fit not yet fully verified | **Research pending** | Verify license first, then include only if it offers a material advantage |
| Trigger.dev | Strong long-running TypeScript jobs and observability | Product licensing/hosting terms require review; Python is not the primary native execution model | **Rejected for primary Python media orchestration** | May be reconsidered for web-only tasks, not core DSP/ML workers |

## Speech activity, transcription, diarization, and semantics

| Candidate | Proposed role | Code/license status | Model/checkpoint status | Current disposition |
|---|---|---|---|---|
| [Silero VAD](https://github.com/snakers4/silero-vad) | Fast CPU speech activity baseline | MIT | Verify exact packaged model/version at pin | **Preferred candidate** |
| [WhisperX](https://github.com/m-bain/whisperX) | Batched ASR, VAD integration, forced alignment, diarization integration | BSD-2-Clause | Uses separately licensed models and dependencies, including pyannote pipelines | **Open comparison**; useful integration baseline, not a monolithic license grant |
| [pyannote.audio](https://github.com/pyannote/pyannote-audio) / `speaker-diarization-community-1` | Speaker diarization | Toolkit and individual pipeline terms differ | Community pipeline is gated and published under CC BY 4.0 with user-agreement/attribution requirements | **Open comparison**; legal and operational gate required |
| [MOSS-Transcribe-Diarize 0.9B](https://github.com/OpenMOSS/MOSS-Transcribe-Diarize) | Joint long-form ASR, diarization, timestamps, acoustic events | Apache-2.0 repository | Official model described as Apache-2.0; exact artifact hash still required | **High-priority Lab candidate** because it is very new |
| `moss-transcribe.cpp` | Emerging CPU/local inference for MOSS | MIT implementation; upstream weights separate | Reuses upstream model terms | **Lab candidate**; maturity/performance spike |
| [PANNs](https://github.com/qiuqiangkong/audioset_tagging_cnn) | AudioSet semantic sound classification baseline | MIT | Verify exact pretrained checkpoint and labels | **Lab candidate** |
| Whisper / faster-whisper | ASR substrate beneath candidate integrations | Whisper repository is MIT; implementation and converted-model artifacts have separate manifests | Verify exact model and conversion provenance | **Component candidates**, selected through ASR spike |
| FunASR / SenseVoice | Unified speech understanding alternatives | Terms vary by repository/model | Not yet fully verified | **Research pending** |

Known evaluation concerns:

- overlapping speech remains difficult for common diarization pipelines;
- forced-alignment support is language/model dependent;
- speaker assignment and word boundaries must be scored separately;
- a recent repository can have unresolved integration/version issues despite an attractive feature list;
- CPU, consumer-GPU, and managed-GPU profiles must be measured independently.

## Speech enhancement, separation, and restoration

| Candidate | Proposed role | Code/license status | Model/checkpoint status | Current disposition |
|---|---|---|---|---|
| [DeepFilterNet](https://github.com/Rikorose/DeepFilterNet) | Full-band 48 kHz speech denoise baseline; CPU-friendly option | Dual MIT/Apache-2.0 repository | Verify the exact bundled/released checkpoint and redistribution scope | **High-priority Lab candidate** |
| [ClearerVoice-Studio](https://github.com/modelscope/ClearerVoice-Studio) | Speech enhancement, separation, super-resolution, target-speaker extraction | Apache-2.0 repository | Verify every selected checkpoint separately; some official model cards identify Apache-2.0 | **High-priority Lab candidate** |
| [Resemble Enhance](https://github.com/resemble-ai/resemble-enhance) | Denoise plus restorative/bandwidth-extension experiment | MIT repository | Verify released checkpoints and provenance | **Lab candidate**, not assumed production-ready |
| VoiceRestore | Generative/flow-matching restoration experiment | MIT repository reported | Verify checkpoint license, provenance, maintenance, and security | **Lab only**; young project |
| Audio Separator / UVR model wrappers | Separation and difficult-source experimentation | Wrapper may be permissive; individual model families/checkpoints differ | Must verify every downloaded model | **Lab only** until model-by-model clearance |
| RNNoise | Lightweight classic neural denoise alternative | BSD-3-Clause | Verify packaged model and build | **Fallback candidate** |
| Cathar | Emerging Rust restoration toolkit | MIT/Apache-2.0 reported | Neural assets, if used, require separate review | **Watchlist/Lab**, too young for foundation |

No enhancement model is selected by benchmark claims in its README or paper. Promotion requires Ampersand's rights-cleared listening and preservation tests.

## Editing and rendering substrates

| Candidate | Proposed role | License/status | Current disposition | Required gate |
|---|---|---|---|---|
| Dawn-Cut | Deterministic TypeScript edit core, transcript/timeline synchronization, EDL, undo/replay | MIT; young project | **Architecture audit / possible vendoring candidate** | Code audit, tests, project-format stability, deterministic save/reopen/render proof |
| CutScript | Reference implementation for WhisperX, text editing, DeepFilterNet, and FFmpeg export | MIT; young desktop-oriented project | **Reference and spike source** | Do not fork wholesale without architecture review |
| Auto-Editor CLI | Silence/loudness-driven edits and timeline export | Open CLI reported under Unlicense/public domain; current product releases may mix in separately licensed application features | **Lab/reference candidate** | Pin exact open CLI commit; verify file-by-file boundaries |
| OpenTimelineIO | EDL/NLE interchange | Apache-2.0 | **Deferred preferred interface** | Adapter compatibility matrix |
| Waveform Playlist / dawcore | Later multitrack browser editor substrate | MIT reported | **Deferred** | Re-evaluate only after singletrack V1 |
| OpenCut | Later social/video editor substrate | MIT reported; active rewrite | **Deferred/track upstream** | No V1 dependency |
| AudioMass | Browser audio-editor reference | Verify exact license/version before use | **Reference only pending audit** | No foundation dependency |

## Evaluation tools and metrics

| Candidate | Role | License/status | Current disposition |
|---|---|---|---|
| [ViSQOL](https://github.com/google/visqol) | Full-reference perceptual speech/audio quality estimate | Apache-2.0 | **Preferred diagnostic metric** for applicable reference cases |
| EBU R128 / BS.1770 measurements | Loudness, LRA, and peak conformance | Standards, not a software dependency | **Required validation** |
| ITU-R BS.1534 / MUSHRA-style listening | Comparative human audio assessment | Standard/protocol | **Required methodology basis** where applicable |
| P.835-style SIG/BAK/OVRL ratings | Speech-enhancement listening dimensions | Standard methodology family | **Preferred denoise-listening structure** |
| NISQA pretrained models | Non-intrusive speech quality estimate | Common public weights include noncommercial/share-alike restrictions | **Rejected for production selection logic** unless a commercially admissible model is obtained |
| DNSMOS, PESQ, STOI, SI-SDR, SNR | Diagnostic metrics | Implementations and model assets have different terms | **Per-implementation review required**; never sole promotion criterion |

## Copyleft/reference boundary

The following may contain useful ideas, but their licenses require deliberate legal architecture before they can be incorporated into a proprietary product:

- BBC audiowaveform — GPLv3;
- Peaks.js / waveform-data.js — LGPL-3.0;
- `master_me` — GPL;
- PodcastPlugins — GPL;
- Spotify Pedalboard — GPLv3 in current releases;
- Essentia — AGPL in the standard open-source distribution;
- Matchering — GPL;
- any project that changed from a permissive license to noncommercial or source-available terms.

Studying behavior or public documentation is not permission to copy protected source. Reference-only projects must not be pasted, translated, or indirectly reproduced by automated agents into Ampersand.

## Production promotion checklist

A candidate can move from Lab to production only when all are true:

- [ ] exact code and model versions are pinned;
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

## Research priorities

1. Verify exact checkpoint licenses for DeepFilterNet, selected ClearerVoice models, Silero VAD, PANNs, MOSS, and restoration candidates.
2. Run the ASR/diarization comparison without committing the domain model to one provider's output schema.
3. Run the enhancement bake-off through a common processor contract.
4. Complete the Hatchet/Temporal/Prefect fault-injection spike.
5. Select WaveSurfer or Peaks only after long-file, accessibility, licensing, and timing tests.
6. Decide whether waveform peaks can be generated with a permissive Ampersand utility instead of shipping GPL audiowaveform.
7. Generate an automated third-party notice and software-bill-of-materials process before the first distributable build.