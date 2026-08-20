# Existing Google Hosting Integration Plan

**Status:** New Cloud Run baseline selected; legacy cleanup follows beta verification

**Last verified:** 2026-08-20
**Authority:** [ADR-0009](../decisions/ADR-0009-GOOGLE-HOSTING-RICH-STUDIO.md)

## Current rule

The owner identified project `gen-lang-client-0564514768` and selected the new GitHub-to-Cloud Run V1 beta as
Ampersand's fresh hosted baseline. Older Google/OpenAI deployments are deprecated and no longer need to be reconciled
into the product.

The reviewed [V1 beta publish guide](./GOOGLE_V1_BETA_PUBLISH.md) creates that baseline. Legacy resource deletion remains
a separate explicit operation after smoke testing so unrelated storage, secrets, domains, and billing dependencies are
not removed accidentally.

## When legacy cleanup starts

Legacy inventory and cleanup begins only when:

- `ampersand-v1-beta` has deployed from reviewed `main`;
- the release smoke test passes;
- a known-good Cloud Run revision exists for rollback;
- the owner approves the exact legacy resources to delete.

The issue #24 private-beta checkpoint is governed by ADR-0010 and ADR-0011 and proceeds before cleanup.

## Read-only legacy inventory

After the new beta is verified, record without exposing secret values:

- Google product(s), project ID/name, region, billing account boundary, and environment names;
- production URL, preview/staging URLs, domain and DNS ownership;
- source repository/branch and current deployed commit if available;
- build/runtime versions, build command, output directory, deployment trigger, and service account;
- identity/authentication, database/object storage, queues/events, and upload flow;
- environment-variable and secret **names**, access policy, rotation owner, and runtime bindings;
- logs, metrics, alerts, budgets, quotas, retention, deletion, backups, and rollback behavior;
- whether Google AI Studio material is source, an export, a prototype, or unrelated cross-project content.

Write findings into a deployment inventory tied to a GitHub issue and reviewed commit. Quarantine code/assets that cannot be attributed to Ampersand.

## Baseline and cleanup sequence

1. Deploy `ampersand-v1-beta` from reviewed GitHub `main`.
2. Bind only the minimum runtime identity, private bucket, and secret required by the beta.
3. Test authentication, upload, processing, retry/idempotency, browser reopen, deletion, and private artifact access.
4. Add release smoke checks, observable step/run IDs, alerts, budgets, and a documented rollback path.
5. Inventory legacy services, storage, databases, secrets, domains, and billing dependencies read-only.
6. Present exact cleanup targets to the owner and delete only approved deprecated resources.
7. Connect the custom domain only after release-readiness and email/DNS preservation checks pass.

## Required handoff evidence

- exact Google target and deployed Git SHA;
- build/publish/rollback procedure;
- required configuration and secret names, never values;
- staging and production smoke results;
- data/storage/retention/deletion map;
- logs, alerts, budgets, and incident owner;
- domain/DNS changes and rollback when that later step occurs.
