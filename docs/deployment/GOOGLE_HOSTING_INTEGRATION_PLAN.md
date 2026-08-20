# Existing Google Hosting Integration Plan

**Status:** Deferred until owner connection and integration readiness

**Last verified:** 2026-08-20
**Authority:** [ADR-0009](../decisions/ADR-0009-GOOGLE-HOSTING-RICH-STUDIO.md)

## Current rule

Ampersand's already deployed Google-hosted site remains the production destination. Preserve it. The exact Google service, project, repository linkage, build, storage, identity, secrets, and domain configuration are currently unknown and must not be guessed from legacy source or Google AI Studio exports.

No step in this document authorizes a live publish, secret change, data migration, domain change, or deployment deletion.

## When this work starts

Begin only when:

- the owner says Ampersand has reached the Google integration stage;
- the owner connects or explicitly opens the relevant Google account/project;
- the engine/control contracts needed by the Studio slice are reviewed;
- a rollback target can be identified before any production publish.

## Read-only discovery

First record, without exposing secret values:

- Google product(s), project ID/name, region, billing account boundary, and environment names;
- production URL, preview/staging URLs, domain and DNS ownership;
- source repository/branch and current deployed commit if available;
- build/runtime versions, build command, output directory, deployment trigger, and service account;
- identity/authentication, database/object storage, queues/events, and upload flow;
- environment-variable and secret **names**, access policy, rotation owner, and runtime bindings;
- logs, metrics, alerts, budgets, quotas, retention, deletion, backups, and rollback behavior;
- whether Google AI Studio material is source, an export, a prototype, or unrelated cross-project content.

Write findings into a deployment inventory tied to a GitHub issue and reviewed commit. Quarantine code/assets that cannot be attributed to Ampersand.

## Integration sequence

1. Reconcile the deployed source with GitHub; never overwrite unique live code blindly.
2. Extract Ampersand-only changes from any mixed Google AI Studio export and verify ownership/licensing.
3. Establish preview/staging deploys from a reviewed Git commit.
4. Bind only the minimum environment and secret names required by that slice.
5. Connect the Google-hosted Studio to versioned Ampersand APIs and independently deployable workers.
6. Test authentication, cross-workspace denial, resumable upload, callbacks, retry/idempotency, browser reopen, deletion, and private artifact access.
7. Add release smoke checks, observable step/run IDs, alerts, budgets, and a documented rollback command/path.
8. Publish production only after the owner approves the exact target and rollback.
9. Connect the custom domain only after release-readiness and email/DNS preservation checks pass.

## Required handoff evidence

- exact Google target and deployed Git SHA;
- build/publish/rollback procedure;
- required configuration and secret names, never values;
- staging and production smoke results;
- data/storage/retention/deletion map;
- logs, alerts, budgets, and incident owner;
- domain/DNS changes and rollback when that later step occurs.
