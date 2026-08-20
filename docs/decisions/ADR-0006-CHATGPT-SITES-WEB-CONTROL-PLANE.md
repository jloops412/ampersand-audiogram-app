# ADR-0006: ChatGPT Sites Web/Worker Boundary

- **Status:** Superseded as an execution plan by ADR-0007
- **Date:** 2026-08-18
- **Superseded by:** [ADR-0007: Build the Product First; Defer Hosting Migration Work](./ADR-0007-BUILD-FIRST-HOSTING-DEFERRED.md)

## Historical decision

The owner intends to publish the completed Ampersand web experience through ChatGPT Sites and connect an owned domain.

This ADR recorded a sound architectural boundary:

- a lightweight web host may serve the Studio UI and supported request/response behavior;
- FFmpeg, native DSP, GPU inference, durable workflows, long-running jobs, model caches, large temporary processing, and the Audio Lab should remain independently deployable;
- GitHub should remain source of truth;
- secrets must not be committed;
- the browser should not become the authoritative long-form processor or renderer.

## What was superseded

The earlier version expanded the hosting intention into a dedicated compatibility spike, Google-host audit, D1/R2 evaluation, migration epic, and domain-cutover gate.

The owner clarified that this over-prioritized hosting before the actual product existed. Issues #16–#20 were therefore closed as not planned for the current phase.

## Current rule

Use the web/worker separation as a portability requirement while building the engine and Studio. Do not spend current engineering effort proving ChatGPT Sites, auditing Google hosting, or planning DNS.

When Ampersand reaches a publishable build, create a fresh release issue to:

1. publish the compatible web experience to ChatGPT Sites;
2. configure required secrets/environment values;
3. validate the completed product;
4. connect the owner's domain;
5. retire old hosting safely.

That later release task must not block the active implementation plan.