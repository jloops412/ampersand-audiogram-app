# Historical ChatGPT Sites Primary-Source Notes

**Status:** Reference-only after [ADR-0009](../decisions/ADR-0009-GOOGLE-HOSTING-RICH-STUDIO.md); not an active deployment destination.

**Status:** Active deployment-source register  
**Last verified:** 2026-08-18  
**Policy:** Re-verify before the compatibility spike, every public deployment, and custom-domain cutover because Sites is in public beta.

## Official sources

### Creating and managing ChatGPT Sites

- https://help.openai.com/en/articles/20001339

Verified points:

- Sites creates, previews, publishes, shares, and manages interactive websites and lightweight apps.
- Sites availability and controls depend on plan/workspace and rollout.
- Every deployment URL is a production URL.
- A version should be saved and reviewed before deployment.
- Custom domains can be connected where available using DNS records supplied by Sites.
- Public/workspace/restricted access options depend on account/workspace settings.
- Some frameworks, private networks, databases, background services, and hosting patterns may be unsupported.
- Sites does not support data or inference residency at launch.
- Sites must not process Protected Health Information or raw payment-card data.
- Public Sites and forms require review of personal-data collection and applicable privacy obligations.

### ChatGPT Sites developer guide

- https://learn.chatgpt.com/docs/sites
- canonical developer redirect observed from https://developers.openai.com/codex/sites

Verified points:

- Sites can start from a prompt or a compatible existing local project.
- GitHub/local source remains usable; Sites management occurs through ChatGPT web/desktop rather than a standalone CLI management interface.
- `.openai/hosting.json` stores project linkage and optional D1/R2 binding names.
- Hosted secrets and environment values belong in Site settings, not `.openai/hosting.json`, prompts, attachments, or source.
- For local source projects, a saved Sites version is associated with the Git commit used for the build.
- Saving a version and deploying a version are separate stages.
- D1 is available for durable relational data in supported Site shapes.
- R2 is available for file/object storage in supported Site shapes.
- The documented D1 storage limit is 10 GB; R2 is documented as having no fixed storage limit, subject to plan/beta limits.
- Public Sites can optionally use Sign in with ChatGPT.
- Sites forwards authenticated email and an optional full name to server code through documented request headers; authorization must remain server-side.
- Hosted environment changes require redeployment of the approved saved version.
- Custom domains may use an owned apex domain or subdomain where available.
- Analytics are built in for supported non-Enterprise-owned Sites.
- Plan-specific public-beta usage limits can affect Site creation, storage, or public availability.

## Planning interpretation

The official documentation supports using Sites for:

- the Ampersand web application;
- lightweight server behavior;
- public/restricted access;
- optional identity-aware features;
- compatible durable Site state/files;
- versioned hosted releases;
- custom-domain hosting.

It does **not** establish that Sites is appropriate for:

- FFmpeg batch execution;
- GPU inference;
- durable long-running media workflows;
- multi-hour background processing;
- private-network worker clusters;
- large temporary processing volumes.

Therefore ADR-0006 keeps heavy processing external unless later official documentation and an implementation spike prove otherwise.

## Facts that must be checked in the product UI rather than assumed from docs

- current limits for the owner's exact plan/workspace;
- whether custom domains are enabled for that workspace;
- available access modes;
- analytics availability;
- supported project/framework shape;
- D1/R2 provisioning and external access behavior;
- Sites deployment/build logs and version IDs;
- exact DNS records provided for the owner's domain;
- any new beta restrictions, usage charges, or residency behavior.

## Change-control rule

When official documentation changes materially:

1. record the new verification date;
2. update the migration plan and ADR-0006;
3. update affected GitHub issues;
4. do not silently rely on the new behavior in production;
5. create a compatibility/regression test before changing the deployment boundary.
