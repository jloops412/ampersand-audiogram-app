# Ampersand V2 Target Architecture

**Status:** Accepted logical architecture; provider selections remain open where noted  
**Last verified:** 2026-08-18

## Architecture objective

Build a durable, provider-neutral media platform in which:

- source media is immutable;
- browser closure does not stop work;
- expensive processing steps are independently resumable;
- analysis and processing are separate;
- all decisions and artifacts are reproducible;
- processing providers can be replaced without changing the product domain model;
- CPU operation remains possible for the baseline;
- optional GPU workers accelerate approved models;
- the Audio Lab and customer Studio share contracts but keep research data isolated from production user data.

## Two-system model

```text
                 ┌──────────────────────────────┐
                 │      AMPERSAND AUDIO LAB     │
                 │ corpus · experiments ·       │
                 │ blinded listening · metrics  │
                 └──────────────┬───────────────┘
                                │ promotes approved
                                │ processors/recipes
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                     AMPERSAND STUDIO                         │
│ library · upload · production · compare · edit · export      │
└──────────────────────────────┬───────────────────────────────┘
                               │ shared versioned contracts
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                DATA / OBJECT / WORKFLOW CONTROL              │
│ Postgres-compatible DB · S3-compatible objects · events      │
│ durable workflow engine · access control · lifecycle         │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                     MEDIA WORKERS                            │
│ probe · canonicalize · waveform · analysis · ASR ·           │
│ enhancement · leveling · mastering · render · encode         │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│               VERSIONED ARTIFACTS AND PROVENANCE             │
│ source · intermediates · semantic map · transcript ·         │
│ master · outputs · reports · manifests · checksums            │
└──────────────────────────────────────────────────────────────┘
```

The Lab may use research-only processors that are not admitted to Studio. Production code must reject unapproved processor/model manifests.

## Recommended repository shape

The exact framework may evolve, but responsibilities should remain separated:

```text
ampersand/
├── apps/
│   ├── web/                     # Studio and Lab web surfaces
│   └── worker-control/          # optional thin trusted API/control plane
├── services/
│   ├── media-worker/            # Python/Rust/native media steps
│   └── render-worker/           # deterministic audio/video rendering
├── packages/
│   ├── contracts/               # domain schemas and generated clients
│   ├── edit-core/               # deterministic EDL/time mapping
│   ├── render-spec/             # shared preview/export description
│   ├── ui/                      # design system
│   └── test-fixtures/
├── lab/
│   ├── corpus-manifests/
│   ├── experiments/
│   ├── listening/
│   └── reports/
├── infra/
│   ├── containers/
│   ├── migrations/
│   ├── deployment/
│   └── sbom/
└── docs/
```

The current prototype can remain temporarily under a clearly marked legacy path or tag during refoundation.

## Core domain model

### Workspace

Ownership and access boundary.

Key fields:

- `id`
- `name`
- `plan`
- `retention_policy_id`
- `region`
- `created_at`

### Project

Optional grouping for productions, brand assets, episodes, clients, or events.

### Production

The durable user-facing unit of work.

Key fields:

- `id`
- `workspace_id`
- `project_id`
- `title`
- `status`
- `source_asset_id`
- `recipe_version_id`
- `current_run_id`
- `created_by`
- `created_at`
- `deleted_at`

A Production is not the job itself. It may have multiple reproducible runs.

### Asset

Any immutable uploaded or generated media/data object.

Key fields:

- `id`
- `workspace_id`
- `kind`
- `object_uri`
- `sha256`
- `size_bytes`
- `mime_type`
- `duration_ms`
- `channels`
- `sample_rate`
- `created_by_step_id`
- `retention_class`
- `encryption_key_ref`

Assets are content-addressed where practical. Replacing an asset means creating a new one.

### RecipeVersion

Immutable declarative processing intent.

Contains:

- supported input/use-case class;
- analysis requirements;
- routing policy version;
- processing graph;
- processor/model constraints;
- loudness/output targets;
- fallback/no-op rules;
- user-exposed controls;
- known limitations.

A mutable template identity points to immutable template versions. The four intent shortcuts select recommended built-in template versions; they are not the only configuration surface.

### ControlDefinition

Immutable recipe-owned metadata for one user-exposed setting:

- stable control and contract-path IDs;
- stage/outcome group;
- value type, units, allowed values/range, and default;
- Basic/Advanced presentation metadata;
- availability, capability requirements, contraindications, and risk/cost/privacy warnings;
- whether the value affects run/step cache identity.

No Studio control exists without a matching definition and engine field.

### StudioTemplate and StudioTemplateVersion

`StudioTemplate` is the mutable workspace catalog identity (name, description, current version, default/archive state). `StudioTemplateVersion` is immutable and records:

- template and version IDs;
- base `recipe_version_id`;
- validated analysis, cleanup, leveler, mastering, transcript/caption, render, and export choices;
- schema version and content hash;
- creator, creation time, and change summary.

Editing creates a new version. Built-in templates are copied before workspace customization. Archive preserves historical references.

### ResolvedProductionSettings

Fully expanded immutable run input created from recipe defaults, an optional template version, and explicit per-production overrides.

It records:

- schema, recipe, and optional template-version identity;
- every resolved value, including unchanged defaults;
- per-value provenance (recipe, template, or run override);
- validation normalizations, warnings, unavailable capabilities, and fallbacks;
- deterministic content hash.

The resolved hash participates in idempotency and cache keys. UI state never substitutes for this artifact, and later default/template edits cannot change an old run.

### ProductionRun

One execution of a source plus recipe and engine environment.

Key fields:

- `id`
- `production_id`
- `recipe_version_id`
- `resolved_settings_id`
- `resolved_settings_sha256`
- `engine_build_id`
- `status`
- `idempotency_key`
- `started_at`
- `completed_at`
- `cancel_requested_at`
- `failure_code`

### JobStep

One independently retryable/checkpointed operation.

Examples:

- media probe;
- canonical audio render;
- waveform peaks;
- loudness analysis;
- VAD;
- ASR;
- diarization;
- semantic classification;
- technical defect analysis;
- denoise;
- adaptive gain render;
- final master;
- output encode;
- transcript/caption export;
- audiogram render.

Key fields:

- `step_key`
- `input_manifest_hash`
- `provider`
- `provider_version`
- `model_manifest_id`
- `status`
- `attempt`
- `started_at`
- `completed_at`
- `output_manifest_id`
- `metrics`
- `failure`

### SemanticMap

Versioned timeline containing regions and observations.

Observation categories may include:

- speech probability;
- music probability;
- silence/ambience/noise;
- speaker;
- acoustic event;
- transcript word;
- loudness/peak envelope;
- clipping;
- noise profile;
- reverberation;
- bandwidth limitation;
- spectral balance;
- confidence and source provider.

Provider-native output is retained for audit, but product features consume Ampersand's normalized schema.

### ProcessingRegion

A half-open interval `[start_us, end_us)` with:

- processor selection;
- strength/parameters;
- reason;
- confidence;
- source: automatic, recipe, or user override;
- transition/crossfade policy;
- bypass state.

### Transcript

Versioned words, punctuation, speakers, confidence, and alignment. Edits do not mutate the raw provider result.

### EditDecisionList

Deterministic, serializable representation of cuts, kept ranges, captions, chapters, overlays, and clip exports.

The EDL must use integer microseconds or an equivalently precise rational time model and half-open intervals to avoid accumulating floating-point drift.

### Output

A user-deliverable artifact plus encoding and validation manifest.

### ModelManifest / DependencyManifest

Release-admission record defined in the dependency matrix.

### Experiment

Lab-only object linking corpus version, candidates, manifests, metrics, listening protocol, results, and decision.

## Provider contracts

### ObjectStore

```text
create_resumable_upload()
complete_upload()
get_signed_read_url()
open_worker_stream()
put_artifact()
head_object()
delete_object()
apply_retention()
```

Must support S3-compatible or equivalently portable access and checksums.

### WorkflowEngine

```text
start_run(production_run)
schedule_step(step, idempotency_key)
checkpoint(step, output_manifest)
report_progress(step, event)
request_cancel(run)
retry_step(step)
resume_run(run)
```

The domain model must not expose Hatchet-, Temporal-, Prefect-, or provider-specific IDs as its primary identity.

### AnalysisProvider

```text
capabilities()
analyze(input_asset, requested_outputs, runtime_profile)
normalize_provider_result(raw_result) -> SemanticMapFragment
```

Examples: VAD, ASR, diarization, acoustic classification, defect analysis.

### AudioProcessor

```text
capabilities()
validate_input(region, context)
process(input_asset, region_plan, parameters, runtime_profile)
produce_processing_report()
```

Each processor declares:

- supported sample rates/channels/languages/content;
- CPU/GPU requirements;
- deterministic/non-deterministic behavior;
- latency and memory profile;
- contraindications;
- license-approved deployment modes;
- model manifest.

### QualityMetric

```text
applicability(reference, candidate, metadata)
score(reference, candidate)
explain_limitations()
```

No quality metric can directly promote a processor.

### Renderer

Consumes an immutable render specification and assets to produce preview-compatible and delivery outputs.

Browser preview and server export should share:

- coordinate system;
- aspect ratio;
- timing;
- captions;
- waveform data;
- fonts/brand assets;
- layer ordering;
- animation parameters.

The browser must not be the authoritative long-form export engine.

## Canonical processing DAG

```text
UPLOAD
  ↓
VALIDATE + PROBE
  ↓
SOURCE MANIFEST + IMMUTABLE STORAGE
  ↓
CANONICAL WORKING AUDIO (only when needed)
  ├───────────────┬────────────────┬─────────────────┐
  ↓               ↓                ↓                 ↓
WAVEFORM       LOUDNESS        SPEECH/ASR       SEMANTICS/DEFECTS
  └───────────────┴────────────────┴─────────────────┘
                          ↓
                    SEMANTIC MAP
                          ↓
                 PROCESSING ROUTER
                          ↓
      ┌───────────────────┼────────────────────┐
      ↓                   ↓                    ↓
CLASSIC DSP        SPEECH ENHANCEMENT     REGIONAL BYPASS
      └───────────────────┼────────────────────┘
                          ↓
                  ADAPTIVE LEVELER
                          ↓
                ADAPTIVE EQ/FILTERING
                          ↓
                FINAL LOUDNESS MASTER
                          ↓
          ┌───────────────┼──────────────────┐
          ↓               ↓                  ↓
         WAV             MP3           REPORT/DATA OUTPUTS
```

Independent branches may run concurrently. A failed transcript must not force denoise or loudness analysis to repeat.

## Idempotency and reproducibility

A step idempotency key should be derived from:

- normalized input asset hashes;
- step implementation version;
- model/checkpoint hash;
- parameter hash;
- runtime-relevant deterministic flags;
- output schema version.

A completed matching step may be reused only when access, retention, and privacy policy permit it.

Non-deterministic models must record:

- seed where controllable;
- runtime and device;
- library versions;
- model hash;
- determinism limitations.

## Artifact contract

Each step produces a small JSON manifest plus one or more immutable objects.

A manifest includes:

- schema version;
- source and parent artifact hashes;
- producer step and run;
- code/model/container versions;
- timestamps and duration;
- checksums;
- warnings;
- measurements;
- output object references;
- privacy/retention class.

Large binary media must not be embedded in workflow-engine event histories or database rows.

## Runtime profiles

### CPU baseline

Required for:

- probe and validation;
- waveform generation;
- loudness and peak analysis;
- deterministic DSP;
- baseline VAD;
- final mastering and encoding;
- potentially quantized ASR where viable.

### Optional consumer GPU

Used for approved ASR, diarization, denoise, or restoration models when available.

### Managed GPU worker

Used for models whose memory/performance profile exceeds local hardware. The design must:

- upload only explicitly authorized assets;
- pin region/provider;
- encrypt transport and storage;
- support zero/short retention where available;
- record provider terms and data use;
- fall back or queue safely when unavailable.

No product promise may assume undisclosed local GPU hardware.

## Replit-compatible development boundary

The web application and lightweight control plane may be developed or deployed through Replit-compatible workflows. Heavy media processing must remain separately deployable because it may require:

- native FFmpeg builds;
- long-running durable jobs;
- large temporary storage;
- CPU-intensive processing;
- optional CUDA/GPU runtimes;
- model caches measured in gigabytes.

This separation lets Replit remain a useful interface/deployment environment without coupling core audio quality to one interactive web container.

## Environments

### Local developer

- small fixture corpus only;
- mock or local object store;
- local Postgres/workflow option;
- CPU processors by default;
- secrets isolated from source control.

### Audio Lab

- segregated rights-cleared corpus;
- experiment registry;
- optional GPU runners;
- no production user media;
- no Auphonic output;
- restricted researcher access.

### Staging

- synthetic and consented test media;
- production-like workflow/storage;
- destructive fault injection;
- retention/deletion tests;
- no unapproved models.

### Production

- only admitted manifests;
- least-privilege identities;
- immutable audit trail;
- automated lifecycle policies;
- user-visible deletion controls;
- documented incident response.

## Security boundaries

- Browser receives short-lived scoped upload/read authorization, never worker credentials.
- Workers receive only the source objects needed for the assigned step.
- Workspace isolation is enforced in the database and object layer.
- Media URLs are non-public by default.
- Secrets are stored in a secret manager, not the database or job payload.
- Logs must not contain transcript text, signed URLs, credentials, or raw media bytes by default.
- Temporary files are created in per-job directories and wiped after completion/failure.
- User media is never used for model training unless a separate explicit opt-in program is created.

See [Security, Privacy, and Data Governance](../SECURITY_PRIVACY_AND_DATA_GOVERNANCE.md).

## Observability

### Operational

- run/step state;
- queue delay;
- processing real-time factor;
- CPU/GPU/memory/storage;
- retries and failures;
- orphan assets;
- workflow checkpoint/resume;
- output validation.

### Quality

- recipe and processor versions;
- loudness/peak before and after;
- processor warnings;
- no-op/bypass percentage;
- user A/B selection where voluntarily recorded;
- artifact reports;
- recipe rollback rate;
- clean-preservation regression status.

### Cost

- compute per processed hour;
- storage and egress;
- model cold-start overhead;
- retranscription/reprocessing avoided by checkpoint reuse.

## Open provider decisions

The following remain open and require spikes:

- managed versus self-hosted Postgres/Auth/Storage;
- Supabase versus another provider/control-plane composition;
- Hatchet versus Temporal versus Prefect for durable media workflows;
- WaveSurfer versus Peaks for the long-form timeline;
- waveform peak generator avoiding unnecessary GPL distribution complexity;
- WhisperX composition versus newer joint ASR/diarization models;
- CPU and managed-GPU runtime providers;
- deterministic edit-core adaptation versus original implementation.

## Architecture proof

The architecture is considered proven when one one-hour rights-cleared source can:

1. upload resumably;
2. create an immutable source manifest;
3. execute probe, waveform, loudness, VAD, transcript, enhancement, leveler, master, and two output encodes as independently checkpointed steps;
4. survive browser closure;
5. survive deliberate termination after at least two completed expensive steps;
6. resume without repeating those steps;
7. expose progress and understandable failure state;
8. produce deterministic manifests and validated outputs;
9. support same-position Original/Master playback;
10. delete source, intermediates, outputs, and metadata according to policy.

A beautiful UI is not part of this proof. Reliability and domain-contract integrity are.
