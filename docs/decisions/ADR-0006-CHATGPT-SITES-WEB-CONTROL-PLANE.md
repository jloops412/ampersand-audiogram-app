# ADR-0006: ChatGPT Sites Hosts the Web and Lightweight Control Plane; Media Processing Remains External

- **Status:** Accepted deployment direction; implementation gated by compatibility spike
- **Date:** 2026-08-18
- **Decision owners:** Ampersand product, platform engineering, and deployment governance

## Context

The current Ampersand prototype is hosted through a Google environment that has not yet been fully inventoried. The owner intends to move the web experience to ChatGPT Sites and then connect an existing custom domain.

ChatGPT Sites can host compatible existing projects, save reviewable versions associated with Git commits, deploy production versions, manage secrets, provide optional D1/R2 durable data and file storage, support several access/authentication patterns, and connect owned custom domains where available.

However, official documentation also states that some frameworks, private networks, databases, background services, and hosting patterns are unsupported. Ampersand's intended audio engine requires long-running workflows, native FFmpeg execution, large temporary files, CPU/GPU workers, model caches, retries, and durable job orchestration.

## Decision

Use **ChatGPT Sites as the target host for Ampersand's public web experience, Studio UI, and supported lightweight server/control functions**.

Do **not** use ChatGPT Sites as the authoritative runtime for:

- long-running audio jobs;
- FFmpeg/native DSP workers;
- GPU inference;
- workflow orchestration;
- model registries and caches;
- large temporary processing data;
- Audio Lab experiments.

The web application communicates with an external provider-neutral control API and durable processing plane through versioned contracts.

D1 and R2 are optional candidates rather than automatic canonical stores. They may be adopted for bounded roles only after the Sites compatibility spike verifies external access, lifecycle, security, portability, and privacy requirements.

GitHub remains the source of truth. A Sites saved version must map to a reviewed Git commit before deployment.

## Consequences

### Positive

- aligns deployment with the owner's intended ChatGPT Sites/custom-domain destination;
- uses Sites-managed hosting, versioning, access controls, environment values, and domain connection;
- preserves proper infrastructure for CPU/GPU and long-running audio work;
- avoids trying to force media workers into an unsupported lightweight web runtime;
- maintains source-controlled releases and reviewable version candidates;
- supports future migration because worker and storage contracts remain provider-neutral;
- separates public web availability from processor scaling.

### Negative

- the product has at least two deployment planes;
- identity, authorization, CORS, event delivery, and upload flows cross a hosting boundary;
- D1/R2 may not be suitable as canonical stores, creating additional provider decisions;
- public-beta limits and changing capabilities create platform risk;
- every deployment URL is production, requiring stricter save/review/deploy discipline;
- custom-domain and analytics availability vary by plan/workspace;
- no data/inference residency at launch may exclude some future customer requirements.

## Alternatives considered

### Run the entire audio platform in ChatGPT Sites

Rejected. Official documentation warns that background services and some hosting patterns are unsupported, while Ampersand requires native media processing, long jobs, GPU inference, durable retries, and large temporary workspaces.

### Keep Google hosting indefinitely

Rejected as the target direction because it conflicts with the owner's intended migration. Google hosting remains the rollback source until Sites cutover criteria pass.

### Move everything to a conventional cloud host instead

Deferred as the fallback architecture. The provider-neutral contracts preserve this option if Sites compatibility, beta limits, privacy requirements, or economics become unacceptable.

### Use Sites only as a static marketing page

Rejected as unnecessarily narrow. Sites should be evaluated for the full supported Studio/control experience while processing remains external.

## Required implementation constraints

- The web app lives in a separable `apps/web` boundary.
- Heavy workers have no dependency on Sites internals.
- Browser code never receives worker or storage-wide credentials.
- Large audio uploads use direct resumable object-store flows rather than passing through short-running Site handlers.
- Authentication maps into stable Ampersand user/workspace IDs.
- Site-specific identity, D1, R2, and environment bindings are implemented behind `SiteRuntimeAdapter`-style interfaces.
- `.openai/hosting.json` contains linkage/binding names only and no secrets.
- Hosted secrets are configured through Sites settings and changes require approved redeployment.
- A saved version is reviewed before deployment.
- Release manifests record Git commit, Sites version, deployment URL, domain, API version, and rollback version.
- Google hosting remains available until domain-cutover acceptance passes.

## Compatibility spike requirements

Before this ADR is considered operationally proven, issue work must verify:

- compatible build artifacts from the existing/refounded project;
- Sites project provisioning and Git-commit linkage;
- save-versus-deploy workflow;
- environment variables and secrets;
- external API calls and server-side authorization;
- resumable direct uploads;
- progress/status after browser closure;
- private playback/download;
- access and Sign in with ChatGPT options;
- D1/R2 suitability and exit path;
- custom-domain preflight;
- plan-specific beta limits;
- fallback deployment.

## Review triggers

Revisit this ADR when:

- ChatGPT Sites exits beta or materially changes runtime/storage limits;
- background workers or native media execution become officially supported;
- Ampersand requires data residency;
- Sites cannot support the Studio compatibility proof;
- plan limits or economics threaten production availability;
- the external-processing boundary creates unacceptable latency or security risk;
- the owner chooses a different hosting destination.

A change requires a superseding ADR and an updated migration plan.