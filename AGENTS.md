# Ampersand Agent Operating Guide

This file defines the default working rules for coding, research, review, deployment, and migration agents in this repository.

## 1. Read before working

Read, in order:

1. `docs/README.md`
2. `docs/MASTER_PLAN.md`
3. `docs/architecture/TARGET_ARCHITECTURE.md`
4. `docs/architecture/TECHNOLOGY_AND_ALGORITHM_DIRECTION.md`
5. `docs/roadmap/PHASED_ROADMAP.md`
6. the authority documents linked by the assigned GitHub issue
7. relevant ADRs

For hosting/deployment work, also read:

- `docs/deployment/CHATGPT_SITES_MIGRATION_PLAN.md`
- `docs/deployment/CHATGPT_SITES_PRIMARY_SOURCES.md`
- `docs/decisions/ADR-0006-CHATGPT-SITES-WEB-CONTROL-PLANE.md`

For algorithm/model work, also read:

- `docs/research/AUDIO_QUALITY_EVALUATION_PLAN.md`
- `docs/research/OSS_DEPENDENCY_AND_LICENSE_MATRIX.md`
- `docs/decisions/ADR-0003-DEPENDENCY-AND-MODEL-GATES.md`

For Auphonic research, also read:

- `docs/research/AUPHONIC_CAPABILITY_AND_RESEARCH_BOUNDARY.md`

## 2. Issue and branch discipline

- Work from one assigned GitHub issue with explicit acceptance criteria.
- Reference the issue in the branch name and pull request.
- Do not silently expand scope into another issue.
- Record material discoveries in the relevant issue immediately.
- Create or supersede an ADR when a material architecture decision changes.
- Keep pull requests reviewable; avoid mixing research, infrastructure, UI, and DSP changes unless the issue explicitly requires them together.
- Do not begin structural implementation from the planning branch until PR #15 is reviewed and merged or the owner explicitly authorizes otherwise.

Suggested branch form:

```text
issue-<number>/<short-purpose>
```

## 3. Non-negotiable product boundaries

- Original media is immutable.
- All processing is non-destructive, versioned, and reproducible.
- Every expensive step is independently checkpointed and idempotent.
- Provider-native output is normalized into Ampersand-owned schemas.
- Browser preview is not the authoritative long-form renderer.
- Heavy audio processing does not run inside ChatGPT Sites.
- Production user media does not enter the Audio Lab.
- User media is not used for model training by default.
- No model or dependency is production-approved because its repository merely says “open source.”
- No Auphonic output/service/derived learning may be used to benchmark, tune, evaluate, or design Ampersand without written permission covering that exact activity.

## 4. ChatGPT Sites deployment rules

ChatGPT Sites is the target host for:

- public pages;
- Studio UI;
- supported lightweight server/control behavior;
- approved access/authentication behavior;
- optional Site-local D1/R2 state after proof.

The following remain external:

- FFmpeg/native DSP;
- GPU inference;
- durable workflow orchestration;
- long-running jobs;
- model caches;
- large temporary processing;
- Audio Lab experiments.

Agents must:

- keep GitHub as source of truth;
- ensure the Sites build maps to a reviewed Git commit;
- use `.openai/hosting.json` only for supported project/binding identifiers;
- never store secrets in Git, prompts, attachments, client code, or `.openai/hosting.json`;
- save and review a Sites version before deploying;
- treat every deployment URL as production;
- keep current Google hosting available until #19 acceptance passes;
- make no DNS change unless #19 explicitly enters the approved cutover step;
- preserve MX, SPF, DKIM, and DMARC records;
- record Sites limitations discovered during beta rather than hiding them in one-off workarounds.

## 5. Model and dependency admission

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

## 6. Audio-quality rules

- Human listening is the final promotion gate.
- Objective metrics are diagnostic only.
- Loudness-match comparative listening assets.
- Include clean-input preservation.
- Test long-form continuity, not only short clips.
- Preserve no-op/bypass as a valid routing result.
- Report per-item failures and critical artifacts, not just mean scores.
- Never promote a processor from a README demo or paper leaderboard alone.

## 7. Security and privacy rules

- Use least-privilege identities and short-lived media access.
- Do not log transcript text, signed URLs, access tokens, speaker names, or raw media.
- Keep Lab, staging, and production data separated.
- Clean temporary media after success, failure, or cancellation.
- Test cross-workspace access failures.
- Deletion must cover source, intermediates, waveform, transcript, semantic map, embeddings, outputs, caches, and indexes.
- Do not send private media to a hosted processor until its data-use, retention, training, and deletion terms are approved.

## 8. Required deliverables for implementation issues

Unless the issue says otherwise, include:

- implementation;
- unit/contract tests;
- failure-path tests;
- updated schemas/manifests;
- documentation;
- runtime/cost notes where applicable;
- security/privacy impact;
- dependency/license updates;
- migration/rollback notes;
- evidence against every acceptance criterion.

## 9. Completion report

Every agent finishing work should leave a concise issue/PR report containing:

- what changed;
- files/components affected;
- tests and exact results;
- quality/security/license evidence;
- unresolved risks;
- migrations or secrets required;
- rollback procedure;
- next issue dependency;
- whether an ADR or planning document changed.

## 10. Stop conditions

Stop and report rather than guessing when:

- the requested domain or DNS provider is unknown;
- a Sites runtime capability is undocumented or fails the compatibility test;
- a model/checkpoint license is missing or ambiguous;
- production media rights/consent are unclear;
- a change would move heavy processing into Sites;
- a change would expose secrets or private media;
- a workflow retry could duplicate irreversible side effects;
- an Auphonic research step would cross the documented boundary;
- implementation would violate an accepted ADR.

Partial, well-documented evidence is preferable to an unreviewed workaround.