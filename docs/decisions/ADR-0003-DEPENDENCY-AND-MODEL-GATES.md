# ADR-0003: Dependency and Model Admission Gates

- **Status:** Accepted
- **Date:** 2026-08-18
- **Decision owners:** Ampersand engineering, security, quality, and release governance

## Context

Ampersand can avoid rebuilding large portions of media infrastructure by using open-source software, pretrained models, managed services, and standards-based tools. However:

- repository code and model weights may use different licenses;
- a project-level license may not cover every downloaded checkpoint;
- training data or model cards may impose additional terms;
- native and codec dependencies may change distribution obligations;
- permissively licensed projects may be too young or unreliable;
- gated models may require user agreements and attribution;
- a model may be legally usable but fail privacy, quality, cost, or security requirements;
- copyleft tools may be acceptable as isolated subprocesses in some architectures but require deliberate legal analysis;
- projects can change licenses between versions.

## Decision

No dependency, model, checkpoint, hosted processor, or managed service enters a production path solely because it is described as open source, free, state of the art, or popular.

Every production component requires an admission record covering:

1. exact version and artifact hash;
2. source provenance;
3. code license;
4. model/checkpoint license;
5. training-data or gated-access terms when available;
6. attribution, notice, source, and redistribution obligations;
7. hosted-use and commercial-use permission;
8. transitive native dependencies;
9. security and supply-chain review;
10. runtime/device/cost profile;
11. Ampersand quality evaluation;
12. privacy/data-flow review;
13. known failure modes and contraindications;
14. rollback and replacement path;
15. approving pull request or ADR.

Production manifests are allowlisted. Lab-only and unverified components must be technically prevented from running against production user media.

## Consequences

### Positive

- reduces licensing and supply-chain surprises;
- separates attractive research from shippable product;
- makes builds reproducible;
- permits model rollback and processor replacement;
- provides a defensible third-party notice/SBOM process;
- forces quality and privacy to be evaluated with licensing, not afterward.

### Negative

- slows adoption of new models;
- requires continuing license/model-card review;
- may reject technically excellent projects;
- requires storage of license texts, hashes, manifests, and notices;
- some candidates will need legal review before a spike can proceed.

## Admission states

- **Unreviewed:** may not be downloaded into trusted production environments.
- **Lab candidate:** approved for a defined internal rights-cleared experiment only.
- **Production candidate:** legal/security gates pass; quality/reliability gate pending.
- **Approved:** admitted for a bounded role, recipe, runtime, and version.
- **Deprecated:** no new productions; migration/rollback active.
- **Revoked:** blocked because of security, legal, quality, privacy, or integrity concerns.

## Copyleft rule

GPL, AGPL, LGPL, source-available, and noncommercial dependencies are not automatically rejected, but they require explicit architecture and legal review.

Automated contributors must not:

- paste or translate reference-only/copyleft source into proprietary modules;
- assume subprocess isolation resolves all obligations;
- copy implementations from a project whose current license is unclear;
- download arbitrary model weights at runtime;
- omit attribution because a dependency is server-side;
- silently change a pinned model to `latest`.

## Model acquisition rule

Model assets must be fetched during an approved build/release process or from an internal verified registry. Runtime workers should not fetch mutable unverified checkpoints directly from public URLs.

The registry record includes:

- artifact hash;
- model card;
- license snapshot;
- source URL;
- conversion/quantization provenance;
- expected tensor/config files;
- malware/supply-chain scan;
- supported runtime versions.

## Required follow-up

- maintain [OSS Dependency and License Matrix](../research/OSS_DEPENDENCY_AND_LICENSE_MATRIX.md);
- create machine-readable dependency/model manifest schema;
- add SBOM generation;
- add third-party notice generation;
- enforce approved model registry in worker images;
- add CI check that production recipes reference only approved manifests;
- archive license/model-card snapshots with release records;
- schedule re-verification before every public release.

## Review trigger

Review this ADR when:

- Ampersand begins distributing desktop binaries or on-device models;
- a major dependency changes license;
- a hosted-only service is introduced;
- model training/fine-tuning begins;
- a legal interpretation changes the acceptable copyleft boundary;
- a production component is found to have unclear provenance.