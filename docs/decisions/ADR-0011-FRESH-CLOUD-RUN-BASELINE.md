# ADR-0011: Make the New Cloud Run Service the Ampersand Baseline

- **Status:** Accepted
- **Date:** 2026-08-20
- **Decision owner:** Ampersand product owner
- **Tracks:** #24, #18, #25, #26
- **Supersedes:** ADR-0009's pre-existing-deployment preservation/integration requirement and ADR-0010's isolation-only framing

## Context

The owner confirmed that the earlier Google and OpenAI deployments do not need to be preserved as Ampersand's active
product foundation. The reviewed V1 beta in this repository is the intended fresh start and must be published quickly so
real testing can guide continued engine and Studio work.

## Decision

The Cloud Run service `ampersand-v1-beta`, continuously deployed from reviewed GitHub `main` in project
`gen-lang-client-0564514768`, becomes Ampersand's active hosted baseline.

- The root `Dockerfile`, V2 Studio, control API, and independent engine in this repository are authoritative.
- Older Google/OpenAI deployments are deprecated and must not constrain implementation or release decisions.
- Legacy cloud resources may be inventoried and deleted after the new service passes its smoke test, but deletion is a
  separate explicit operation so storage, domains, billing, or unrelated resources are not removed accidentally.
- The custom domain remains deferred until the beta is useful and stable enough to promote.
- Engine quality gates remain unchanged: shadow Leveler/Router output is not presented as active cleanup, and admitted
  processing still requires independent listening and safety evidence.

## Consequences

This removes deployment-reconciliation work from the critical path and lets every reviewed merge advance one hosted
product. It also makes Cloud Run revision history the immediate rollback boundary. The beta's one-instance filesystem
runner, 30 MiB upload cap, browser-local templates, and continuously allocated instance remain temporary constraints,
not permanent architecture.

## Release and cleanup boundary

First publish and smoke-test the new service. Only afterward, inventory legacy services, buckets, databases, secrets,
domains, and billing dependencies; present exact deletion targets to the owner; and remove only explicitly approved
resources. A failed beta deployment must be rolled back within the new Cloud Run service, not by reviving an old product
architecture.
