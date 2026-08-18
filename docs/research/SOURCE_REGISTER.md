# Ampersand V2 Source Register

**Status:** Active  
**Last verified:** 2026-08-18

## Purpose

This register records the primary sources supporting Ampersand's current planning baseline. It prevents future contributors from relying on uncited chat summaries, stale memory, marketing reposts, or secondary license descriptions.

Rules:

- prefer official documentation, standards bodies, canonical repositories, model cards, and license files;
- record the exact verification date;
- distinguish explicit documentation from engineering inference;
- re-check changing terms, licenses, releases, and hosted-service behavior before implementation or release;
- never treat GitHub's detected repository license as proof of every dependency or model checkpoint license;
- do not use Auphonic services or outputs for Ampersand research without written permission.

## Auphonic — legal and capability research

| Source | Relevance | Verification note |
|---|---|---|
| [Auphonic Terms of Service](https://us.auphonic.com/terms_of_service) | Governs prohibited use of services/outputs/derived learnings for competing development, training, evaluation, benchmarking, reverse engineering, design input, or quality targets | **Critical; re-check before every major release or connector decision** |
| [Auphonic Privacy Policy](https://us.auphonic.com/privacy) | Content handling, retention, and algorithm-improvement disclosures | Re-check before any connector or comparative discussion |
| [Audio Algorithms](https://us.auphonic.com/help/algorithms/index.html) | Public description of singletrack/multitrack segment classification foundation | Capability research only |
| [Singletrack Algorithms](https://us.auphonic.com/help/algorithms/singletrack.html) | Public leveling, denoise, filtering, EQ, BWE, mastering behavior | Capability research only |
| [Multitrack Algorithms](https://us.auphonic.com/help/algorithms/multitrack.html) | Public joint-track analysis, mixing, gates, bleed, ducking behavior | Capability research only |
| [Production Help](https://us.auphonic.com/help/web/production.html) | Public control and workflow surface | Capability inventory only |
| [Multitrack Help](https://us.auphonic.com/help/web/multitrack.html) | Public multitrack settings and behavior | Capability inventory only |
| [Algorithm API schema](https://auphonic.com/api/info/algorithms.json) | Machine-readable public settings inventory | Re-check periodically; not an implementation specification |
| [Output-file API schema](https://auphonic.com/api/info/output_files.json) | Public encoding/output inventory | Re-check periodically |
| [Auphonic changelog](https://auphonic.com/changelog) | Current feature changes | Date-sensitive; monitor without output testing |

## Standards and listening evaluation

| Source | Relevance | Notes |
|---|---|---|
| [ITU-R BS.1534](https://www.itu.int/rec/R-REC-BS.1534/en) | Subjective assessment of intermediate audio quality; MUSHRA foundation | Use appropriate version and controlled listening procedure |
| [ITU-T P.835](https://www.itu.int/rec/T-REC-P.835/en) | Separate speech, background, and overall ratings for noise-suppression evaluation | Particularly relevant to denoise |
| [ITU-R BS.1770-5](https://www.itu.int/rec/R-REC-BS.1770-5-202311-I/en) | Current in-force loudness and true-peak measurement algorithms | Measurement authority |
| [EBU R128](https://tech.ebu.ch/publications/r128) | Loudness normalization and permitted maximum level guidance | Product recipe/output guidance |
| [Google ViSQOL](https://github.com/google/visqol) | Apache-2.0 full-reference quality estimator with documented use limitations | Diagnostic only; not sole promotion judge |

## Media, measurement, and corpus tooling

| Source | Proposed role | License/status note |
|---|---|---|
| [FFmpeg](https://ffmpeg.org/) | Probe, decode, resample, filter, encode, mux, render | LGPL/GPL depends on build configuration; approved build profile required |
| [libebur128](https://github.com/jiixyj/libebur128) | R128 loudness/LRA/true-peak measurements | MIT |
| [audiomentations](https://github.com/iver56/audiomentations) | Deterministic degradation generation | MIT |
| [OpenTimelineIO](https://github.com/AcademySoftwareFoundation/OpenTimelineIO) | NLE/timeline interchange | Apache-2.0; adapter support varies |
| [rclone](https://github.com/rclone/rclone) | Generic external file destinations | MIT; provider terms/credentials remain separate |

## Upload, data, and waveform candidates

| Source | Proposed role | License/status note |
|---|---|---|
| [Uppy](https://github.com/transloadit/uppy) | Resumable upload UI and integrations | MIT |
| [tusd](https://github.com/tus/tusd) | TUS server/self-hosted upload fallback | MIT |
| [Supabase](https://github.com/supabase/supabase) | Postgres/Auth/Storage/Realtime managed or self-host candidate | Apache-2.0 repository; managed terms separate |
| [WaveSurfer.js](https://github.com/katspaugh/wavesurfer.js) | Waveform playback/regions candidate | BSD-3-Clause; precomputed peaks needed for long files |
| [Peaks.js](https://github.com/bbc/peaks.js) | Long-form waveform/segments alternative | LGPL-3.0; development location/status must be rechecked |
| [BBC audiowaveform](https://github.com/bbc/audiowaveform) | Peak generation reference/tool | GPLv3; not default production choice without legal review |
| [waveform-data.js](https://github.com/bbc/waveform-data.js) | Waveform data representation | LGPL-3.0 |

## Speech activity, transcription, and diarization

| Source | Proposed role | License/model note |
|---|---|---|
| [Silero VAD](https://github.com/snakers4/silero-vad) | Lightweight speech activity baseline | MIT repository; pin and verify exact model artifact |
| [WhisperX](https://github.com/m-bain/whisperX) | ASR + alignment + diarization composition baseline | BSD-2-Clause code; underlying models/dependencies separate |
| [pyannote.audio](https://github.com/pyannote/pyannote-audio) | Diarization toolkit | Pipeline/model terms vary |
| [speaker-diarization-community-1 model card](https://huggingface.co/pyannote/speaker-diarization-community-1) | Candidate diarization pipeline | CC BY 4.0 and gated/user-agreement requirements reported; verify live card |
| [MOSS-Transcribe-Diarize](https://github.com/OpenMOSS/MOSS-Transcribe-Diarize) | New joint ASR/diarization/events candidate | Apache-2.0 reported for repo/model; very new; exact artifact required |
| [moss-transcribe.cpp](https://github.com/OpenMOSS/moss-transcribe.cpp) | Emerging CPU/local MOSS inference | MIT implementation; upstream model terms separate |
| [PANNs](https://github.com/qiuqiangkong/audioset_tagging_cnn) | Semantic audio classification baseline | MIT repository; checkpoint verification required |
| [OpenAI Whisper](https://github.com/openai/whisper) | ASR foundation/reference | MIT repository; converted/runtime artifacts still require provenance |

## Speech enhancement and restoration

| Source | Proposed role | License/model note |
|---|---|---|
| [DeepFilterNet](https://github.com/Rikorose/DeepFilterNet) | Full-band speech enhancement baseline | Dual MIT/Apache-2.0 repository; verify exact checkpoint |
| [ClearerVoice-Studio](https://github.com/modelscope/ClearerVoice-Studio) | Enhancement, separation, super-resolution, target-speaker extraction | Apache-2.0 repository; model-by-model verification required |
| [Resemble Enhance](https://github.com/resemble-ai/resemble-enhance) | Restorative denoise/bandwidth experiment | MIT repository; verify checkpoint/provenance/maturity |
| [RNNoise](https://github.com/xiph/rnnoise) | Lightweight neural-denoise fallback | BSD-3-Clause repository |
| [Audio Separator](https://github.com/nomadkaraoke/python-audio-separator) | Lab separation-model wrapper | Wrapper/model licenses differ; verify every model |
| [Backblaze DeepFilterNet batch sample](https://github.com/backblaze-b2-samples/deepfilternet-batch-speech-enhancement) | Implementation reference for object storage + batch enhancement | MIT sample; not automatically our architecture |

Projects such as VoiceRestore or Cathar remain watchlist items until their canonical source, checkpoint terms, maintenance, and security are recorded here.

## Workflow engines

| Source | Relevance | License/status note |
|---|---|---|
| [Hatchet](https://github.com/hatchet-dev/hatchet) | Python/TS task and durable-workflow candidate | MIT; must pass long-run/fault injection |
| [Temporal](https://github.com/temporalio/temporal) | Mature durable execution candidate | MIT service; SDK and managed terms separate |
| [Temporal Python SDK](https://github.com/temporalio/sdk-python) | Python-worker integration | MIT; verify version compatibility |
| [Prefect](https://github.com/PrefectHQ/prefect) | Python-native workflow candidate | Apache-2.0; managed/self-host feature boundaries must be tested |

The provider decision remains open under ADR-0004.

## Editing and rendering references

| Source | Relevance | License/status note |
|---|---|---|
| [Dawn-Cut](https://github.com/kwakseongjae/dawn-cut) | Deterministic edit-core architecture candidate | MIT reported; young; code audit required |
| [CutScript](https://github.com/DataAnts-AI/CutScript) | WhisperX/DeepFilterNet/text-edit/FFmpeg implementation reference | MIT reported; young desktop architecture |
| [Auto-Editor](https://github.com/WyattBlue/auto-editor) | Silence/loudness edit and timeline export reference | Pin exact open CLI version; current product boundaries require verification |
| [Waveform Playlist](https://github.com/naomiaro/waveform-playlist) | Later multitrack editor candidate | MIT reported; deferred |
| [OpenCut](https://github.com/OpenCut-app/OpenCut) | Later social/video editor candidate | MIT reported; active rewrite; deferred |

## Reference-only/copyleft research

These may inform independent research but require explicit legal architecture before any code use:

- [master_me](https://github.com/trummerschlunk/master_me) — GPL;
- [PodcastPlugins](https://github.com/trummerschlunk/PodcastPlugins) — GPL;
- [Spotify Pedalboard](https://github.com/spotify/pedalboard) — verify current GPL terms and transitive plugin framework;
- Essentia — AGPL in standard open distribution;
- Matchering — GPL;
- NISQA public pretrained weights — commonly noncommercial/share-alike;
- any current source-available/noncommercial release of Rescript.

## Ampersand legacy repository evidence

Reviewed at commit `a5e234b04533d51025a9d0bde00bb584f2cc48fe`:

- `backend/server.js` — Auphonic proxy and static server;
- `src/App.tsx` — browser-owned generation workflow;
- `src/services/videoService.ts` — real-time canvas/audio MediaRecorder export;
- `src/services/audioService.ts` — browser whole-file decode and peaks;
- `src/services/auphonicService.ts` — upload/poll/download;
- `src/services/transcriptService.ts` — basic SRT/VTT parsing;
- `src/components/ControlPanel.tsx` — fixed low-level control surface;
- `src/components/Preview.tsx` — duplicated static canvas render behavior;
- `src/types.ts` and `src/constants.ts` — waveform vocabulary and fixed 1080×1080 defaults;
- `README.md` — generic AI Studio/Gemini boilerplate;
- `Dockerfile` — combined Node 18 frontend/backend image.

See [Legacy Salvage Matrix](./LEGACY_SALVAGE_MATRIX.md).

## Verification queue

Before Phase 1 implementation:

- exact DeepFilterNet checkpoint license/hash;
- selected ClearerVoice checkpoint licenses/hashes;
- Silero packaged model license/hash;
- PANNs checkpoint provenance;
- MOSS artifact/runtime requirements and license snapshot;
- ViSQOL build/dependency manifest;
- current waveform UI maintenance and license status;
- managed Supabase terms, export, retention, and cost;
- Hatchet/Temporal/Prefect current releases and managed/self-host terms;
- exact Dawn-Cut and Auto-Editor commits/licenses;
- current FFmpeg build profile and codec obligations.

Before public release, every live link and changing term in this register must be re-verified and archived in the release record.