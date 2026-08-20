# Ampersand

**Status:** V2 implementation is active

**Studio/control plane:** existing Google-hosted deployment, integration pending owner connection

**Heavy processing:** independent media and render workers
**Legacy prototype:** retained for history; not the V2 foundation

Ampersand is an independent spoken-word audio intelligence, mastering, editing, and content-repurposing platform. The product goal is one-click automatic mastering when that is enough, plus an understandable visual Studio when a user needs to inspect, compare, or override a decision.

The OpenAI Sites Studio checkpoint remains available as a non-production design/reference artifact at:

https://ampersand-audiograms.woodwardwarrior.chatgpt.site

## What works now

- a product-specific Studio reference shell with private durable source uploads;
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
- a deterministic Adaptive Leveler V0 shadow envelope with bounded speaker/content-aware gain and Studio-ready reasoning;
- deterministic two-pass WAV/MP3 loudness mastering;
- a versioned, rights-clear synthetic Audio Lab corpus with controls, degradations, lineage, and an opt-in one-hour stream;
- output validation, provenance, step manifests, and an understandable report;
- tests that reproduce manifests and media hashes across repeated runs.

This is the content-aware deterministic engine foundation, not a claim that the Adaptive Leveler, neural cleanup, checkpoint-backed VAD, ASR, or audiogram renderer is finished.

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
processing-plan.json
leveler-settings.json
gain-envelope.json
leveler-statistics.json
recipe.json
production.json
production-run.json
steps/*.json
artifacts/master.wav
artifacts/master.mp3
output-manifest.json
processing-report.json
```

Run all V2 gates:

```bash
uv run python scripts/check_v2_boundaries.py
uv run ruff check packages services scripts
uv run ruff format --check packages services scripts
uv run mypy
uv run pytest
```

See [Local Engine CLI](./docs/build/LOCAL_ENGINE_CLI.md), [Semantic Audio Map V0](./docs/architecture/SEMANTIC_AUDIO_MAP_V0.md), [Adaptive Leveler V0](./docs/architecture/ADAPTIVE_LEVELER_V0.md), and [Synthetic Fixture Corpus V0](./docs/research/SYNTHETIC_FIXTURE_CORPUS_V0.md) for the reproducibility, privacy, cost, validation, fusion, and rollback contracts.

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
7. #7/#8/#23 — enhancement, speech understanding, and Processing Router;
8. #24/#25/#26 — durable engine, Studio integration, A/B, and report;
9. #13 — one-hour recovery proof;
10. #27 — deterministic professional audiogram renderer.

Publishing into the existing Google deployment, operational management, and domain/DNS work remain deferred until those pieces produce a strong product and the owner connects the relevant Google account/project.

The four current production intents are convenience shortcuts, not the final settings model. Each run will support rich contract-backed settings and an immutable resolved-settings snapshot; users will be able to create and reuse versioned templates without changing historical runs.

## Governance boundary

Ampersand is not a reverse-engineered Auphonic implementation. Current Auphonic terms restrict using its services, outputs, derivatives, evaluations, insights, or learnings to develop or benchmark a competing system without a tailored arrangement. Ampersand therefore uses independent rights-cleared references, synthetic degradations, standards-based measurements, admitted open components, and human listening.

Read the [Implementation Execution Plan](./docs/build/IMPLEMENTATION_EXECUTION_PLAN.md), [documentation index](./docs/README.md), and [research boundary](./docs/research/AUPHONIC_CAPABILITY_AND_RESEARCH_BOUNDARY.md) before contributing.
