# Ampersand

**Status:** V2 implementation is active; Smart Cleanup guardrails are integrated in the private beta

**Studio/control plane:** new Cloud Run V1 beta deployed from reviewed GitHub `main`

**Heavy processing:** independent media and render workers
**Legacy prototype:** retained for history; not the V2 foundation

Ampersand is an independent spoken-word audio intelligence, mastering, editing, and content-repurposing platform. The product goal is one-click automatic mastering when that is enough, plus an understandable visual Studio when a user needs to inspect, compare, or override a decision.

The OpenAI Sites Studio checkpoint remains available as a non-production design/reference artifact at:

https://ampersand-audiograms.woodwardwarrior.chatgpt.site

## What works now

- a responsive private-beta Studio with a production library, single/batch upload, progress, retry, delete, and downloads;
- private resumable browser-to-Cloud-Storage uploads up to 1 GiB without proxying source bytes through Cloud Run;
- four useful quick-start intents with protect-first Smart Cleanup, an explicit Manual DSP mode, and executable loudness,
  true-peak, loudness-range, output-format, bitrate, metadata, and audiogram controls;
- browser-local reusable templates with immutable versions and an exact resolved-settings snapshot on every run;
- same-position Original/Master playback, precomputed waveforms, measured results, and an understandable report;
- a lightweight serial batch runner with independent durable job/source/output records and restart recovery;
- strict provider-neutral V2 contracts and exported JSON Schemas;
- a local, no-credential media-engine CLI;
- immutable source hashing and normalized media probing;
- canonical 48 kHz float working audio only when needed;
- multiresolution waveform peaks;
- standards-based loudness and true-peak measurement;
- a versioned, full-coverage Semantic Audio Map with soft speech/silence probabilities;
- deterministic 100 ms momentary/short-term loudness, sample-peak, and true-peak evidence;
- an Ampersand-owned, zero-model-cost energy/spectral VAD baseline;
- provider-normalization adapters, deduplicated provenance, raw audit artifacts, and explicit conflicts;
- a local Semantic Map visual debug report and safe protect/no-op/eligible decisions;
- a deterministic Processing Router V0 shadow plan with explicit protection, bypass, DSP/denoise candidates, safe
  overrides, fallbacks, and Studio-ready reason codes;
- a deterministic Adaptive Leveler V0 shadow envelope with bounded speaker/content-aware gain and Studio-ready reasoning;
- a sample-accurate, channel-linked, evaluation-only Leveler renderer that leaves production masters unchanged;
- deterministic two-pass WAV/MP3 loudness mastering;
- an auditable Smart Cleanup V0.3 plan with exact evidence, thresholds, stage dispositions, hashes, and safe no-op results;
- explicit Manual deterministic declipping, rumble/hum filtering, steady-noise reduction, gating, de-essing, voice EQ,
  and compression processing;
- full-duration H.264/AAC audiograms with 1:1, 4:5, 9:16, and 16:9 layouts; four waveform primitives; rich layout,
  opacity, typography, frame-rate, and quality controls; and color, uploaded image, or looping-video backgrounds;
- a versioned, rights-clear synthetic Audio Lab corpus with controls, degradations, lineage, and an opt-in one-hour stream;
- a local-only blinded listening/regression harness with deterministic loudness-matched Original/A/B and clean-input
  preservation sessions, delayed identity reveal, artifact scoring, diagnostics, and tamper-checked reports;
- output validation, provenance, step manifests, and an understandable report;
- tests that reproduce manifests and media hashes across repeated runs.

This is the content-aware deterministic engine foundation, not a claim that the Adaptive Leveler, active Router,
neural restoration, background-music separation, dereverberation, checkpoint-backed VAD, or ASR is finished. Smart
Cleanup candidates are protect-only until admitted detector and listening gates pass; Manual steady-noise reduction
remains available as an explicit global control.

## Run the independent engine

Prerequisites: Python 3.12+, [uv](https://docs.astral.sh/uv/), FFmpeg, and ffprobe.

```bash
uv sync --all-packages --dev
uv run ampersand-generate-fixture /tmp/ampersand-fixture.wav
uv run --package ampersand-media-worker ampersand-engine process \
  /tmp/ampersand-fixture.wav \
  --output /tmp/ampersand-production
```

Generate the broader deterministic Audio Lab controls separately with `uv run ampersand-generate-corpus /tmp/ampersand-fixture-corpus`.

Prepare a versioned listening experiment and serve it only on localhost:

```bash
uv run ampersand-listening prepare /absolute/path/to/experiment.json --output /tmp/listening-session
uv run ampersand-listening serve /tmp/listening-session
```

Render a shadow Leveler envelope only for that evaluation workflow:

```bash
uv run --package ampersand-media-worker ampersand-engine render-leveler-candidate \
  /absolute/path/to/exact-analysis-source.wav \
  /tmp/ampersand-production/gain-envelope.json \
  --output /tmp/ampersand-leveler-candidate
```

The output directory contains:

```text
source-manifest.json
probe.json
canonical-manifest.json       # only when canonicalization was needed
analysis.json
waveform-peaks.json
semantic-map-v0.json
semantic-map-debug.html
provider-native/*.json
provider-native/*.manifest.json
router-settings.json
processing-plan.json
processing-router-report.json
leveler-settings.json
gain-envelope.json
leveler-statistics.json
recipe.json
resolved-settings.json
cleanup-plan.json
production.json
production-run.json
steps/*.json
artifacts/master.wav
artifacts/master.mp3
artifacts/audiogram.mp4       # only when requested
output-manifest.json
processing-report.json
```

Run all V2 gates:

```bash
uv run python scripts/check_v2_boundaries.py
uv run ruff check packages services lab scripts
uv run ruff format --check packages services lab scripts
uv run mypy
uv run pytest
```

## Run the private beta locally

The beta keeps the independent Python engine and the web/control surface in one deployable container while preserving
their versioned contract boundary. With Node.js 20 installed:

```bash
uv sync --all-packages --dev
npm install
npm install --prefix apps/worker-control
npm run build
AMPERSAND_DATA_DIR=/tmp/ampersand-beta-data \
AMPERSAND_STATIC_DIR="$PWD/dist" \
AMPERSAND_ENGINE_BIN="$PWD/.venv/bin/ampersand-engine" \
AMPERSAND_BETA_TOKEN="replace-with-a-long-random-key" \
node apps/worker-control/server.js
```

Open `http://localhost:8080`. Multipart upload remains capped at 30 MiB for local fallback. A configured Cloud Run beta
uses scoped resumable browser-to-Cloud-Storage sessions for source files up to 1 GiB; the bucket must use the reviewed
origin-specific CORS policy in `infra/cloud-storage-cors.json`.

See [Local Engine CLI](./docs/build/LOCAL_ENGINE_CLI.md),
[Semantic Audio Map V0](./docs/architecture/SEMANTIC_AUDIO_MAP_V0.md),
[Processing Router V0](./docs/architecture/PROCESSING_ROUTER_V0.md),
[Smart Cleanup Guardrails V0.3](./docs/architecture/SMART_CLEANUP_GUARDRAILS_V0_3.md),
[Adaptive Leveler V0](./docs/architecture/ADAPTIVE_LEVELER_V0.md),
[Leveler Gain Renderer V0](./docs/architecture/LEVELER_GAIN_RENDERER_V0.md),
[Synthetic Fixture Corpus V0](./docs/research/SYNTHETIC_FIXTURE_CORPUS_V0.md), and
[Blinded Listening and Regression Harness V0](./docs/research/BLINDED_LISTENING_HARNESS_V0.md) for the reproducibility,
privacy, cost, validation, evaluation, and rollback contracts.

## Repository responsibilities

| Path | Responsibility |
|---|---|
| `apps/web` | Google-hosted Studio source boundary and shared client adapters |
| `apps/worker-control` | lightweight provider-neutral job/control API boundary |
| `packages/contracts` | canonical Pydantic contracts and runtime-neutral JSON Schemas |
| `packages/test-fixtures` | deterministic rights-clear synthetic fixture generation |
| `services/media-worker` | independent CPU media graph and local CLI |
| `services/render-worker` | future authoritative audio/video render boundary |
| `lab` | segregated rights-cleared evaluation work |
| `infra` | admission manifests, deployment, migration, SBOM, and container authority |
| `src`, `backend` | legacy prototype only; never imported by V2 code |

## Product architecture

```text
Google-hosted Studio + lightweight control plane
                  ↓ versioned Ampersand contracts
immutable objects + durable job records
                  ↓
independent media workers
  probe · peaks · semantics · cleanup · level · master
                  ↓
independent deterministic render workers
  WAV · MP3 · report · captions · audiograms
```

Original media is immutable. Expensive work is checkpointable. Provider-native results must be normalized before product logic consumes them. Unknown, clean, uncertain, musical, or unsupported content may remain protected/no-op.

## Current build order

1. #3 — finish V2 refoundation and permanent legacy tag;
2. #12 — enforce dependency/model admission manifests, SBOM, and notices;
3. #21 — core contracts and runnable local CLI;
4. #22 — Semantic Audio Map V0;
5. #6 — deterministic DSP and Ampersand Adaptive Leveler V0;
6. #4/#5 — rights-cleared fixtures and listening/regression harness;
7. #7/#8/#23 — enhancement, speech understanding, and active Processing Router promotion;
8. #24/#25/#26 — durable engine, Studio integration, A/B, and report;
9. #13 — one-hour recovery proof;
10. #27 — expand the deterministic audiogram renderer with captions, clip selection, and richer motion styles.
11. #43 — protect-first Smart Cleanup planning and exact Manual deterministic overrides.

Issue #24 now includes an intentionally narrow private-beta publish checkpoint. It creates the new Ampersand Cloud Run
baseline from GitHub. Older deployments are deprecated and may be inventoried and removed after this service is verified;
custom-domain/DNS work and a public production launch remain deferred until the stronger release gates pass. See the
[Google V1 beta publish guide](./docs/deployment/GOOGLE_V1_BETA_PUBLISH.md).

The four current production intents are convenience shortcuts, not the final settings model. Each run will support rich contract-backed settings and an immutable resolved-settings snapshot; users will be able to create and reuse versioned templates without changing historical runs.

## Governance boundary

Ampersand is not a reverse-engineered Auphonic implementation. Current Auphonic terms restrict using its services, outputs, derivatives, evaluations, insights, or learnings to develop or benchmark a competing system without a tailored arrangement. Ampersand therefore uses independent rights-cleared references, synthetic degradations, standards-based measurements, admitted open components, and human listening.

Read the [Implementation Execution Plan](./docs/build/IMPLEMENTATION_EXECUTION_PLAN.md), [documentation index](./docs/README.md), and [research boundary](./docs/research/AUPHONIC_CAPABILITY_AND_RESEARCH_BOUNDARY.md) before contributing.
