# Ampersand Agent Operating Guide

This file defines the default working rules for coding, research, review, and release agents in this repository.

## 1. Current owner directive

**Build the actual Ampersand product.**

The owner's existing Google-hosted deployment remains Ampersand's production web destination. Preserve it until the owner connects the relevant Google account/project at the integration stage; do not guess the Google product, mutate the live deployment, publish, wire secrets, or change DNS beforehand. The OpenAI Sites checkpoint is a non-production design/reference artifact, not the deployment target.

Build the Studio and independent engine together, but do not move FFmpeg, native DSP, GPU inference, durable long-running workflows, or authoritative rendering into the browser or lightweight web runtime. The four current intent choices are quick starts only: the real Studio must expose rich supported per-production settings and reusable, immutable-versioned templates. Every run stores the exact resolved settings used.

The active execution authority is:

- `docs/build/IMPLEMENTATION_EXECUTION_PLAN.md`
- foundation epic #14

## 2. Read before working

Read, in order:

1. `docs/build/IMPLEMENTATION_EXECUTION_PLAN.md`
2. `docs/README.md`
3. `docs/MASTER_PLAN.md`
4. `docs/architecture/TARGET_ARCHITECTURE.md`
5. `docs/architecture/TECHNOLOGY_AND_ALGORITHM_DIRECTION.md`
6. the authority documents linked by the assigned GitHub issue
7. relevant ADRs, especially ADR-0009 (which supersedes ADR-0008's hosting destination)

For algorithm/model work, also read:

- `docs/research/AUDIO_QUALITY_EVALUATION_PLAN.md`
- `docs/research/OSS_DEPENDENCY_AND_LICENSE_MATRIX.md`
- `docs/decisions/ADR-0003-DEPENDENCY-AND-MODEL-GATES.md`
- the Auphonic public reconstruction/evidence documents relevant to the assigned capability.

For Auphonic research, also read:

- `docs/research/AUPHONIC_CAPABILITY_AND_RESEARCH_BOUNDARY.md`

## 3. Issue and branch discipline

- Work from one assigned GitHub issue with explicit acceptance criteria.
- Reference the issue in the branch name and pull request.
- Do not silently expand scope into another issue.
- Record material discoveries in the relevant issue immediately.
- Create or supersede an ADR when a material architecture decision changes.
- Keep pull requests reviewable; avoid mixing unrelated UI, infrastructure, model, and DSP work.
- Do not begin structural implementation from the planning branch until PR #15 is reviewed and merged or the owner explicitly authorizes otherwise.

Suggested branch form:

```text
issue-<number>/<short-purpose>
```

## 4. Build priority

Agents should prioritize this sequence:

1. #3 — V2 workspace/refoundation and #12 — dependency/model admission manifests;
2. #21 — core contracts and runnable local processing CLI;
3. #22 — Semantic Audio Map V0;
4. #6 — deterministic mastering and Adaptive Leveler V0;
5. #4/#5 — rights-cleared fixtures and minimal quality harness;
6. #7/#8 — enhancement and speech-understanding providers;
7. #23 — Processing Router V0;
8. #24 — durable singletrack engine;
9. #25/#26/#31 — rich Studio, templates, A/B comparison, and report;
10. #18 — adapt the existing Google web/control boundary after the owner connects it;
11. #13 — one-hour end-to-end proof;
12. #27 — deterministic audiogram renderer.

Studio product work proceeds with the engine. Google publishing/management and domain/DNS work remain deferred until the owner connects the existing deployment at the integration stage.

## 5. Non-negotiable product boundaries

- Original media is immutable.
- All processing is non-destructive, versioned, and reproducible.
- Every expensive step is independently checkpointed and idempotent.
- Provider-native output is normalized into Ampersand-owned schemas.
- Browser preview is not the authoritative long-form renderer.
- Production user media does not enter the Audio Lab.
- User media is not used for model training by default.
- No model or dependency is production-approved because its repository merely says “open source.”
- No Auphonic output/service/derived learning may be used to benchmark, tune, evaluate, or design Ampersand without written permission covering that exact activity.
- No fake UI control may exist without a corresponding recipe/engine field.
- Four intent cards may choose defaults, but must never be the only configuration surface.
- Per-production overrides resolve to a complete immutable settings snapshot before a run starts.
- Reusable template edits create new versions; old runs and template versions remain reproducible.
- Clean, protected, uncertain, and unsupported content must be allowed to remain no-op/bypassed.

## 6. What Ampersand owns

Do not outsource or collapse these into provider-specific logic:

- Semantic Audio Map;
- Processing Router;
- Adaptive Leveler;
- processing recipes;
- conservative speaker-aware EQ decisions;
- quality/fallback policy;
- Studio explanations and report;
- provenance and reproducibility.

Dependencies execute bounded work behind adapters; they do not define the product model.

## 7. Model and dependency admission

Before adding a candidate:

- pin the exact source commit/tag/package;
- pin the exact model/checkpoint and hash;
- archive code and model licenses separately;
- verify commercial hosted use and redistribution;
- record attribution and notices;
- document training-data/gated-access terms where available;
- scan transitive native dependencies and vulnerabilities;
- record CPU/GPU/runtime requirements;
- run the approved quality and clean-preservation tests;
- document contraindications and rollback;
- update the dependency/model manifest.

Lab-only artifacts must be technically blocked from production recipes.

## 8. Audio-quality rules

- Human listening is the final promotion gate.
- Objective metrics are diagnostic only.
- Loudness-match comparative listening assets.
- Include clean-input preservation.
- Test long-form continuity, not only short clips.
- Preserve no-op/bypass as a valid routing result.
- Report per-item failures and critical artifacts, not just mean scores.
- Never promote a processor from a README demo or paper leaderboard alone.
- The minimal Lab should support current build decisions; do not expand research infrastructure endlessly before implementation.

## 9. Security and privacy rules

- Use least-privilege identities and short-lived media access.
- Do not log transcript text, signed URLs, access tokens, speaker names, or raw media.
- Keep Lab, staging, and production data separated.
- Clean temporary media after success, failure, or cancellation.
- Test cross-workspace access failures.
- Deletion must cover source, intermediates, waveform, transcript, semantic map, embeddings, outputs, caches, and indexes.
- Do not send private media to a hosted processor until its data-use, retention, training, and deletion terms are approved.

## 10. Required deliverables for implementation issues

Unless the issue says otherwise, include:

- working implementation;
- unit/contract tests;
- failure-path tests;
- updated schemas/manifests;
- documentation;
- runtime/cost notes where applicable;
- security/privacy impact;
- dependency/license updates;
- migration/rollback notes where relevant;
- evidence against every acceptance criterion;
- a runnable path from a clean checkout.

## 11. Completion report

Every agent finishing work should leave a concise issue/PR report containing:

- what changed;
- files/components affected;
- commands to run it;
- tests and exact results;
- quality/security/license evidence;
- unresolved risks;
- migrations or secrets required;
- rollback procedure;
- next issue dependency;
- whether an ADR or planning document changed.

## 12. Stop conditions

Stop and report rather than guessing when:

- a model/checkpoint license is missing or ambiguous;
- production media rights/consent are unclear;
- a change would expose secrets or private media;
- a workflow retry could duplicate irreversible side effects;
- an Auphonic research step would cross the documented boundary;
- implementation would violate an accepted ADR;
- a provider-specific schema would become the permanent product schema;
- a feature would require global processing where the router should be regional/protective;
- work mutates the Google deployment before the owner connects it, drifts into DNS cutover, recreates the heavy engine inside the web runtime, or treats a hosting shell as a substitute for the assigned product issue.

Partial, well-documented working implementation is preferable to more speculative planning.
