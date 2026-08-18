# ADR-0004: Workflow Engine Selection Remains Open

- **Status:** Accepted open decision
- **Date:** 2026-08-18
- **Decision owners:** Ampersand platform engineering

## Context

Ampersand processing consists of long-running, expensive, partially parallel media steps. A production may run for minutes or hours and must survive browser closure, worker death, process restarts, duplicate events, transient provider failures, and cancellation without repeating completed work unnecessarily.

A simple in-memory queue or one opaque “process file” task is insufficient.

Current promising candidates include:

- Hatchet — Python and TypeScript, task queues, DAGs, durable tasks, retries, and operational UI;
- Temporal — mature event-sourced durable execution and strong recovery semantics with Python support;
- Prefect — Python-native workflow orchestration, retries, caching, and monitoring.

Each has different operational complexity, hosted/self-hosted boundaries, event/history models, developer ergonomics, and recovery behavior. No current research justifies permanent selection before implementation-level fault testing.

## Decision

Keep the workflow engine behind an Ampersand-owned `WorkflowEngine` contract and run a bounded three-way spike before selection.

Do not encode provider-specific workflow IDs, decorators, states, or event payloads into the product's primary Production/Run/Step domain model.

## Shared spike workflow

Each candidate must implement the same logical DAG:

```text
probe
  ├── waveform
  ├── loudness
  ├── VAD/ASR
  └── semantic analysis
        ↓
processing router
        ↓
enhancement
        ↓
leveler
        ↓
master
  ├── WAV
  └── MP3
```

Binary media and large analysis payloads remain in object storage. Workflow histories carry references and compact manifests only.

## Fault-injection tests

Each candidate must demonstrate:

- worker killed mid-step;
- worker killed after output upload but before completion acknowledgement;
- orchestrator/control service restart;
- duplicate step delivery;
- transient object-store failure;
- model/service unavailable;
- retryable versus non-retryable failure;
- run cancellation during an expensive step;
- cancellation between steps;
- timeout and heartbeat loss;
- missing/corrupt intermediate;
- concurrency and per-resource rate limits;
- one-hour source and multi-hour workflow duration;
- operation after several days of continuous service;
- versioned workflow/recipe change while old runs remain active;
- complete run deletion and audit retention.

The correct result is not merely “workflow eventually completed.” The spike must prove idempotency, checkpoint reuse, understandable state, and bounded duplicate cost.

## Evaluation criteria

Weighted criteria will include:

| Criterion | Importance |
|---|---:|
| Correct checkpoint/recovery semantics | Critical |
| Python media-worker ergonomics | Critical |
| Idempotency and duplicate handling | Critical |
| Cancellation and retry control | High |
| Operational visibility and debugging | High |
| Managed-service reliability option | High |
| Self-host/exit path | Medium/High |
| Local development experience | Medium |
| Event/history size constraints | High |
| Long-running/versioning behavior | High |
| Security/tenancy integration | High |
| Cost at projected processing volume | High |
| Replit-compatible control-plane integration | Medium |
| Community/maintenance/security posture | High |
| Vendor lock-in and migration effort | Medium |

## Selection requirements

The selected engine must:

- support durable step/workflow state;
- work cleanly with Python workers;
- permit idempotent external side effects;
- expose progress without putting large payloads in history;
- support cancellation, retries, timeouts, and concurrency limits;
- survive the defined fault suite;
- keep provider details out of core domain schemas;
- have an acceptable commercial/hosting/license posture;
- support a credible backup/export/migration plan;
- meet cost and operational staffing constraints.

## Consequences

### Positive

- avoids premature lock-in to an attractive but insufficient queue;
- tests the exact failure modes that matter for media workloads;
- keeps the domain model portable;
- allows managed service initially with a future exit path;
- makes workflow-engine replacement possible without rewriting Studio concepts.

### Negative

- requires implementing the same spike several times;
- delays provider-specific optimization;
- provider abstraction can hide useful features if made too generic;
- final selection still carries migration cost if requirements evolve.

## Alternative considered: custom Postgres queue/state machine

Rejected for initial implementation. Although possible, building leases, heartbeats, retries, cancellation, dependency resolution, versioning, visibility, and recovery would consume effort better spent on Ampersand audio intelligence. A custom engine may be reconsidered only if all candidates fail bounded requirements.

## Required follow-up

- define provider-neutral run/step/event schemas;
- build shared fault-injection test fixtures;
- implement Hatchet spike;
- implement Temporal spike;
- implement Prefect spike;
- record managed and self-host operational results;
- publish scoring report;
- accept a superseding provider-selection ADR;
- retain contract tests after selection so replacement remains possible.

## Decision deadline

Selection is required before Phase 4's end-to-end architecture proof. It is not required for the Audio Lab's earliest local batch runner.