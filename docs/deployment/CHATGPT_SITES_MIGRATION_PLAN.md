# ChatGPT Sites Migration and Custom-Domain Plan

**Status:** Accepted deployment direction; implementation remains gated by compatibility and data-flow spikes  
**Last verified:** 2026-08-18  
**Target:** move Ampersand's current Google-hosted web experience to ChatGPT Sites, then connect the owner's existing domain

## Executive decision

Ampersand will target **ChatGPT Sites as the hosted web and lightweight control-plane experience**, while keeping long-running audio processing, FFmpeg, model inference, durable workflows, and other heavy media workers outside the Sites runtime.

This is a deliberate split:

```text
CUSTOM DOMAIN
      │
      ▼
CHATGPT SITES
├── public product/marketing pages
├── authenticated Studio UI
├── production library and status views
├── upload initiation and progress UI
├── waveform/transcript/compare UI
├── lightweight server routes
├── hosted configuration/secrets
└── optional Site-local D1/R2 state after compatibility proof
      │
      ▼
AMPERSAND CONTROL API / DURABLE WORKFLOW
├── production authorization
├── object-upload authorization
├── durable run/step state
├── job orchestration
├── progress events
└── signed worker access
      │
      ▼
EXTERNAL MEDIA WORKERS
├── FFmpeg / libebur128
├── waveform peak generation
├── VAD / ASR / diarization
├── enhancement / restoration
├── Ampersand Leveler / router
├── mastering / validation
└── server-side audiogram rendering
```

ChatGPT Sites is **not** the planned runtime for GPU models, long-lived queues, FFmpeg batch processing, or other background services.

## Official Sites facts shaping this plan

As of the verification date, OpenAI documents that ChatGPT Sites:

- can create, host, refine, and share websites, web apps, and games;
- can prepare and publish a compatible existing local project;
- links a local source project to hosted Sites through `.openai/hosting.json`;
- associates a saved version with the Git commit used for a local-project build;
- separates **save a version** from **deploy a version**;
- treats every deployment URL as a production deployment;
- supports hosted environment variables and secrets in Site settings;
- can provide D1 relational storage and R2 object storage for supported Site shapes;
- supports public, workspace, and selected-user access patterns where available;
- can provide optional Sign in with ChatGPT for public Sites;
- can connect an owned apex domain or subdomain where custom domains are available;
- may not support some frameworks, private networks, databases, background services, or hosting patterns;
- is in public beta with plan-specific limits that may change;
- does not support data or inference residency at launch.

Primary official sources:

- https://help.openai.com/en/articles/20001339
- https://learn.chatgpt.com/docs/sites

## Architectural boundary

### What belongs in ChatGPT Sites

- landing and product-information pages;
- authenticated or identity-aware Studio interface;
- production/project browsing;
- recipe and output configuration;
- resumable-upload initiation and client progress;
- status polling or event-stream consumption;
- waveform, transcript, semantic-map, and A/B views;
- regional override editing;
- customer-visible processing reports;
- download-link presentation;
- lightweight, short-running server handlers supported by Sites;
- optional D1/R2 use only after the compatibility spike proves the required access, lifecycle, security, and portability.

### What must remain outside Sites

- FFmpeg and native media-tool execution;
- long-running or background processing;
- durable job orchestration and retries;
- GPU inference and model caches;
- large temporary working directories;
- processor/model registry;
- long-lived private network dependencies;
- large binary payloads in Site request/response paths;
- authoritative master rendering;
- workflow event histories;
- Lab corpus and evaluation infrastructure.

### What remains deliberately open

- whether Sites D1 becomes the canonical production metadata store or only Site-local state;
- whether Sites R2 becomes canonical media storage or a presentation/upload layer;
- whether external Ampersand services can securely access Site-managed R2/D1 in all required workflows;
- whether Sign in with ChatGPT is the first public identity system, an optional convenience, or not used;
- which exact current Google-hosting product is being replaced;
- the final apex domain or subdomain;
- whether the custom domain initially points directly to the Studio or to a public landing page with the Studio on a subdomain.

No agent should resolve these open decisions by assumption.

## Source-of-truth and deployment model

GitHub remains the source-of-truth repository for Ampersand source and planning.

The intended release flow is:

```text
GitHub branch / pull request
        ↓
reviewed commit on release branch
        ↓
ChatGPT Sites compatibility/build review
        ↓
SAVE VERSION — creates a reviewable deployment candidate tied to Git commit
        ↓
owner/agent verifies preview, source changes, migrations, access, secrets, and data flow
        ↓
DEPLOY VERSION — publishes the approved production URL
        ↓
smoke tests on Sites URL
        ↓
custom-domain promotion or rollback
```

Because every Sites deployment URL is production, agents must not deploy merely to obtain a preview. They must save a version first and deploy only an approved candidate.

## Required repository changes

### Project layout

The refoundation should make the Sites-hosted application separable from external workers:

```text
apps/
└── web/                        # ChatGPT Sites-compatible UI/control surface

services/
├── control-api/                # optional external trusted API boundary
├── media-worker/               # CPU/GPU processing
└── render-worker/              # deterministic visual/audio render

packages/
├── contracts/                  # shared schemas and generated clients
├── ui/
├── render-spec/
└── edit-core/

.openai/
└── hosting.json                # generated/provisioned Sites linkage; no secrets
```

### Configuration

- provide `.env.example` with names only;
- never commit secret values;
- keep hosted secrets in Sites settings;
- record which settings require redeployment;
- keep external worker secrets outside Sites unless a server-side Site route requires them;
- use separate staging and production credentials;
- do not expose worker credentials or storage-wide keys to browser code.

### Compatibility contract

The web app must have a documented command or build path producing Sites-compatible deployment artifacts. Site compatibility must be treated as a tested contract, not an undocumented manual fix.

## Phase 1 — Audit the current Google-hosted deployment

Before migration, establish exactly what exists today.

Inventory:

- current public and preview URLs;
- exact Google product hosting the app;
- branch/commit currently deployed;
- build command and output directory;
- Node/runtime assumptions;
- environment-variable names and secret owners;
- Auphonic credentials and any other third-party credentials;
- storage/database dependencies;
- domain/DNS records currently pointing to Google;
- analytics and monitoring;
- redirects, canonical URLs, sitemap, robots, and metadata;
- current user data and retention obligations;
- rollback method;
- screenshots and functional acceptance baseline.

Do not shut down Google hosting during this phase.

### Audit exit criteria

- one immutable deployment manifest identifies the current system;
- all secrets are rotated or accounted for;
- all domain/DNS records are recorded;
- current functionality has a smoke-test checklist;
- data export and rollback are understood;
- no production data is lost or silently abandoned.

## Phase 2 — ChatGPT Sites compatibility spike

Create a minimal Sites-compatible branch from the V2 web shell and prove:

1. build from the GitHub-tracked local project;
2. `.openai/hosting.json` provisioning without secrets;
3. save-version behavior tied to a known Git commit;
4. deploy only after saved-version review;
5. hosted environment variables and secret rotation;
6. public and restricted access modes;
7. optional Sign in with ChatGPT behavior, including server-side authorization;
8. outbound calls from Site server routes to the external Ampersand control API;
9. CORS, cookies, headers, CSRF, rate limits, timeouts, and error handling;
10. upload initiation to the selected object store without routing multi-GB audio through a short-running Site handler;
11. progress/status updates after browser closure and reopen;
12. private output downloads using short-lived authorization;
13. long-form waveform UI and transcript loading;
14. production deletion request initiation;
15. analytics and operational visibility appropriate to the beta.

### D1/R2 sub-spike

Independently test:

- D1 schema/migration workflow;
- D1 10 GB limit implications;
- R2 file upload and retrieval;
- external worker access requirements;
- signed/private access;
- object lifecycle and deletion;
- checksums and resumability;
- export/exit portability;
- costs/usage limits shown for the owner's plan;
- no data-residency requirement conflicts.

Until this passes, canonical production metadata and audio objects remain behind provider-neutral external Postgres/S3-compatible interfaces.

### Compatibility spike exit criteria

- a saved version can be reviewed without updating the live deployment;
- deployed Site is associated with a known Git commit;
- no secret appears in Git, prompts, attachments, client code, or `.openai/hosting.json`;
- external control API authentication works server-side;
- a representative large upload avoids Site request-body bottlenecks;
- one production can be started, closed, reopened, monitored, and downloaded;
- access and deletion tests pass;
- unsupported runtime assumptions are recorded;
- a fallback host remains available.

## Phase 3 — Separate the V2 web/control plane from processing

Agents should implement provider-neutral boundaries before moving the domain:

- `ProductionApiClient` for Site → control API;
- `UploadSession` for resumable direct upload;
- `ProductionEvent` schema for progress;
- `SignedAssetAccess` for private playback/download;
- `IdentityContext` independent of one auth provider;
- `SiteRuntimeAdapter` for Sites identity, environment, D1, and R2 bindings;
- `DeploymentManifest` containing Git commit, Sites version, API version, migration version, and active custom domain.

No UI component may call a model or worker directly.

## Phase 4 — Parallel Sites deployment

Deploy the Sites version on its generated production URL while Google hosting remains live.

Validate:

- functional parity against the recorded smoke-test baseline;
- responsive desktop/mobile behavior;
- upload and processing continuity;
- authentication and private-media access;
- output downloads;
- domain-independent absolute URLs;
- redirects and canonical metadata;
- privacy disclosures;
- public-content rights;
- rate limiting and abuse controls;
- error pages and degraded-mode behavior;
- analytics;
- support and rollback procedure.

Run the Sites deployment in parallel long enough to complete the agreed acceptance suite. The exact observation window should be recorded in the migration issue rather than assumed here.

## Phase 5 — Custom-domain cutover

The final domain is intentionally represented as `<AMPERSAND_DOMAIN>` until the owner records it in the migration issue.

### DNS preflight

- record current DNS zone and export it where possible;
- identify apex versus subdomain target;
- reduce TTL in advance where the provider permits;
- preserve email-related MX, SPF, DKIM, and DMARC records;
- do not replace the whole DNS zone to change web hosting;
- obtain the exact DNS records from Sites settings;
- verify certificate/domain status before traffic promotion where supported;
- confirm canonical URLs and redirect policy;
- prepare rollback values.

### Recommended domain shape

Choose explicitly between:

- `<AMPERSAND_DOMAIN>` for the public product and Studio together;
- `app.<AMPERSAND_DOMAIN>` for Studio and the apex for marketing;
- another recorded subdomain strategy.

The decision must consider future APIs, worker callbacks, status pages, docs, and email records.

### Cutover sequence

1. freeze unrelated production changes;
2. save and review the final Sites version;
3. deploy the approved version;
4. run smoke tests on the generated Sites URL;
5. add the custom domain in Sites settings;
6. apply only the exact DNS records Sites provides;
7. wait for verification and TLS readiness;
8. test apex/subdomain, `www`, redirects, auth, upload, API calls, playback, and downloads;
9. monitor errors and processing starts;
10. keep Google hosting available as rollback until exit criteria pass;
11. retire Google hosting only through a separate cleanup checklist.

### Cutover exit criteria

- custom domain resolves consistently;
- TLS is valid;
- intended redirect/canonical behavior works;
- email DNS is unchanged;
- user authentication and private media remain secure;
- production create/process/download/delete smoke tests pass;
- the deployed Sites version and Git commit are recorded;
- rollback procedure has been tested or dry-run;
- old Google hosting is not retired prematurely.

## Phase 6 — Google-host retirement

After cutover acceptance:

- export final deployment configuration and logs needed for records;
- remove or rotate Google-host-specific credentials;
- disable old public traffic or replace it with an intentional redirect where supported;
- verify no background process, database, storage bucket, or scheduler is still required;
- preserve legally/operationally required data;
- remove abandoned secrets and service accounts;
- update README, runbooks, status references, and incident response;
- record cost changes;
- keep source and deployment manifests in GitHub.

## Authentication recommendation

Do not make a final auth decision solely because Sites supports Sign in with ChatGPT.

The compatibility spike must compare:

- public Site with no account for marketing content;
- optional Sign in with ChatGPT;
- external identity provider or existing auth;
- workspace-restricted internal environments.

The Ampersand domain model should use its own stable user/workspace IDs. Email or Sites-provided headers may be identity inputs, but must not become the only permanent authorization model.

## Data and privacy constraints

- ChatGPT Sites does not support data or inference residency at launch;
- Sites must not process Protected Health Information or raw payment-card data;
- private audio may contain sensitive personal content even when it is not PHI;
- production audio, transcripts, speaker data, and semantic maps require explicit retention/deletion behavior;
- Site logs and analytics must not contain transcripts, signed media URLs, or secrets;
- public beta limits and availability must be monitored;
- the migration must preserve Ampersand's default no-training policy for customer media;
- the Audio Lab remains separate from Sites production data.

## Release and rollback manifests

Every Sites release should record:

```json
{
  "git_commit": "...",
  "sites_project_id": "...",
  "saved_version_id": "...",
  "deployment_url": "...",
  "custom_domain": "...",
  "deployment_time": "...",
  "web_schema_version": "...",
  "control_api_version": "...",
  "database_migration_version": "...",
  "worker_recipe_manifest_version": "...",
  "rollback_version_id": "..."
}
```

Do not commit secret values in this manifest.

## Agent rules

Agents working on this migration must:

- treat GitHub as source of truth;
- link changes to the migration issues and this document;
- preserve the external-worker boundary;
- avoid putting binary media into Git;
- avoid committing `.env` values;
- never deploy an unreviewed working tree;
- save a Sites version before deployment;
- record the Git commit used by the saved version;
- avoid DNS changes until the domain-cutover issue explicitly enters the approved cutover step;
- preserve Google hosting and rollback until acceptance criteria pass;
- record all unsupported Sites runtime behavior discovered during the spike;
- update this plan or its ADR when official Sites behavior changes during beta.

## Definition of migration complete

The migration is complete only when:

- the supported Ampersand web/control experience is running on ChatGPT Sites;
- the deployed version maps to a reviewed Git commit;
- the custom domain is connected and validated;
- external processing workers operate independently and reliably;
- private-media access, retention, and deletion pass;
- the old Google-hosting dependency is retired without data loss;
- rollback and release manifests exist;
- repository documentation names ChatGPT Sites as the active web host and identifies the external processing plane.