# Ampersand

**Status:** V2 implementation is active

**Studio/control plane:** OpenAI Sites

**Heavy processing:** independent media and render workers
**Legacy prototype:** retained for history; not the V2 foundation

Ampersand is an independent spoken-word audio intelligence, mastering, editing, and content-repurposing platform. The product goal is one-click automatic mastering when that is enough, plus an understandable visual Studio when a user needs to inspect, compare, or override a decision.

The first OpenAI Sites Studio checkpoint is live for its owner at:

https://ampersand-audiograms.woodwardwarrior.chatgpt.site

## What works now

- an OpenAI Sites Studio/control-plane foundation with private durable source uploads;
- strict provider-neutral V2 contracts and exported JSON Schemas;
- a local, no-credential media-engine CLI;
- immutable source hashing and normalized media probing;
- canonical 48 kHz float working audio only when needed;
- multiresolution waveform peaks;
- standards-based loudness and true-peak measurement;
- a conservative protected baseline Semantic Map and Processing Plan;
- deterministic two-pass WAV/MP3 loudness mastering;
- output validation, provenance, step manifests, and an understandable report;
- tests that reproduce manifests and media hashes across repeated runs.

This is the deterministic engine foundation, not a claim that the Adaptive Leveler, neural cleanup, VAD, ASR, or audiogram renderer is finished.

## Run the independent engine

Prerequisites: Python 3.12+, [uv](https://docs.astral.sh/uv/), FFmpeg, and ffprobe.

```bash
uv sync --all-packages --dev
uv run ampersand-generate-fixture /tmp/ampersand-fixture.wav
uv run --package ampersand-media-worker ampersand-engine process \
  /tmp/ampersand-fixture.wav \
  --output /tmp/ampersand-production
```

The output directory contains:

```text
source-manifest.json
probe.json
canonical-manifest.json       # only when canonicalization was needed
analysis.json
waveform-peaks.json
semantic-map.json
processing-plan.json
gain-envelope.json
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

See [Local Engine CLI](./docs/build/LOCAL_ENGINE_CLI.md) for the reproducibility, privacy, cost, validation, and rollback contract.

## Repository responsibilities

| Path | Responsibility |
|---|---|
| `apps/web` | OpenAI Sites Studio integration notes and future shared client adapters |
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
OpenAI Sites Studio + lightweight control plane
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

Domain/DNS cutover remains deferred until those pieces produce a strong product.

## Governance boundary

Ampersand is not a reverse-engineered Auphonic implementation. Current Auphonic terms restrict using its services, outputs, derivatives, evaluations, insights, or learnings to develop or benchmark a competing system without a tailored arrangement. Ampersand therefore uses independent rights-cleared references, synthetic degradations, standards-based measurements, admitted open components, and human listening.

Read the [Implementation Execution Plan](./docs/build/IMPLEMENTATION_EXECUTION_PLAN.md), [documentation index](./docs/README.md), and [research boundary](./docs/research/AUPHONIC_CAPABILITY_AND_RESEARCH_BOUNDARY.md) before contributing.
