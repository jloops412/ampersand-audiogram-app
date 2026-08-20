# Security, Privacy, and Data Governance

**Status:** Accepted baseline requirements; jurisdiction-specific legal review remains required  
**Last verified:** 2026-08-20

## Purpose

Ampersand processes recordings that may contain private conversations, names, contact information, emotional speeches, children, copyrighted music, client-event content, unpublished media, and biometric-adjacent voice characteristics. Security and privacy must be designed into the production model rather than added after audio quality work.

This document defines product and engineering requirements. It is not legal advice and does not replace counsel for privacy, consumer-protection, copyright, employment, recording-consent, accessibility, or sector-specific obligations.

## Core policy

### Default no-training rule

User media, transcripts, speakers, metadata, edits, ratings, and derived features are **not used to train, fine-tune, benchmark, or improve models by default**.

Any future data-contribution program must be:

- separate from ordinary service terms;
- explicit opt-in rather than bundled consent;
- specific about material, purpose, recipients, retention, and revocation;
- unavailable for recordings whose contributors cannot validly consent;
- auditable and reversible where technically and legally possible.

### Original media is immutable

The source asset is never overwritten. Processing creates derived assets with lineage and hashes. Users can delete the source and all derivatives according to policy.

### Least data, least time, least privilege

Collect only the data needed for the requested function, retain it only as long as stated, and expose it only to identities that require it.

## Data classes

| Class | Examples | Default handling |
|---|---|---|
| **Source media** | uploaded WAV, MP3, MP4, MOV | Private, encrypted, immutable, shortest practical retention |
| **Derived media** | canonical audio, enhanced stems, masters, clips | Private, encrypted, linked to source, lifecycle-controlled |
| **Sensitive text** | transcript, speaker names, shownotes, event details | Private, access-controlled, avoid logs/search indexes unless required |
| **Analysis data** | embeddings, speaker vectors, VAD, semantic map, defect labels | Treat as sensitive derivative; no cross-workspace reuse |
| **Operational metadata** | status, duration, codec, job timing | Workspace-scoped; minimize personal content |
| **Billing/usage metadata** | processed minutes, storage, plan | Retention may differ; do not include content unnecessarily |
| **Lab corpus** | consented references and degradations | Separate environment, documented rights, restricted research access |
| **Logs and telemetry** | errors, performance, traces | No raw media/transcripts/signed URLs/secrets by default |

## Consent and content rights

Before a real recording enters the Lab corpus, record:

- owner or controller of the recording;
- right to use it for commercial product research;
- consent status of identifiable speakers where required;
- restrictions on publication or sharing;
- whether minors or protected/private contexts are present;
- copyright status of included music or third-party media;
- allowed processors and external providers;
- retention and deletion date;
- whether excerpts may be used in internal listening tests;
- whether the material may ever appear in public demos.

A customer uploading media must represent that they have necessary rights and permissions. The product should provide plain-language reminders appropriate to recording and copyright concerns without pretending to determine legality automatically.

## Environment separation

### Production user data

- stored only in production-approved regions/providers;
- never copied into the Audio Lab;
- never used in development fixtures;
- accessible through workspace-scoped authorization;
- external processor use requires disclosed, approved data flow.

### Audio Lab data

- only rights-cleared corpus material;
- stored in a separate project/account/bucket/database where practical;
- researcher access is explicit and reviewed;
- no production customer credentials or live objects;
- public and private corpus items are labeled separately;
- experiment exports do not leak identifying metadata.

### Local development

- synthetic or explicitly approved fixtures only;
- no production database dumps;
- no production signed URLs;
- fixture package small enough to audit and remove.

The V0 listening harness adds these local-only controls:

- bind only to loopback and load no third-party web assets;
- expose only the opaque public session and explicitly whitelisted listening WAV paths;
- keep experiment identity, source/region metadata, scores, and state under the private session tree;
- reveal identities only after permanent session close;
- use pseudonymous listener IDs and prohibit names, emails, or customer identifiers in the UI guidance;
- bound JSON requests, disable response caching, omit request logs, and integrity-check the closed report;
- make the generated session directory the deletion unit while leaving archived candidate masters immutable.

These controls make synthetic/local pilot work safer; they do not authorize restricted real recordings without the
rights, access, encryption, retention, and deletion controls required elsewhere in this document.

The evaluation-only Leveler renderer uses the same local boundary. It hashes the immutable source before/after,
restricts FFmpeg decode protocols to local file/pipe, writes decoded float PCM only inside a temporary build directory,
deletes that temporary before atomic publication, refuses overwrite, and sends nothing externally. Its candidate and
runtime report inherit the source's privacy/retention class and remain outside Git.

Processing Router V0 consumes only normalized Semantic Map, recipe, settings, and safe override contracts. Its plan and
report contain timeline decisions, probabilities, processor/manifest IDs, reasons, parameters, hashes, and warnings—not
local source paths, signed URLs, credentials, transcript text, or provider-native payloads. V0 performs no network or
model operation and cannot force an unadmitted processor through a user override.

## Identity and access control

Requirements:

- workspace-based tenancy;
- role-based authorization;
- row-level and object-level isolation;
- short-lived signed media access;
- separate browser, control-plane, and worker identities;
- workers scoped to assigned objects and steps;
- administrative access protected by strong authentication and audit logging;
- no shared global customer-service credentials;
- revocation propagated quickly;
- periodic access review.

Authorization tests must include cross-workspace object-ID guessing and signed-URL replay.

## Encryption and secrets

- TLS for all data in transit;
- encryption at rest through the selected providers;
- per-environment secret management;
- no secrets in source, workflow payloads, client bundles, or logs;
- rotate provider tokens and signing keys;
- separate model-registry/download credentials from user-media credentials;
- encrypt local temporary volumes where practical;
- securely remove temporary working directories after success, failure, or cancellation.

## Upload and object safety

- direct resumable upload with scoped authorization;
- server-side verification of declared type versus actual container/codec;
- file-size, duration, and decompression-resource limits;
- malware scanning where appropriate;
- reject executable/polyglot content that is not needed;
- normalize filenames and never use user filenames as filesystem paths;
- object keys generated by the service;
- checksum validation;
- quarantine before processing when validation is incomplete;
- cleanup abandoned multipart/TUS uploads.

FFmpeg and media probes should run with resource limits and in hardened containers because malformed media can exercise complex native parsers.

## Processor and model-provider governance

For every local or hosted processor, record:

- media and metadata sent;
- region and subprocessors;
- retention and deletion terms;
- whether provider data may be used for model improvement;
- human-review possibility;
- training opt-out;
- security certifications where relevant;
- breach-notification terms;
- contract/DPA status;
- supported deletion mechanism;
- model and service version.

A hosted processor that reserves broad training rights is not production-approved for private customer media without an explicit product/legal decision and clear user disclosure.

## Speaker embeddings and voice identity

Speaker embeddings and diarization outputs can enable linking or recognition even when the product only intends anonymous speaker separation.

Rules:

- use anonymous production-scoped speaker IDs by default;
- do not build cross-production voice identity or biometric recognition in V1;
- do not retain raw provider embeddings longer than necessary;
- avoid exposing embeddings through APIs;
- user-entered speaker names are metadata, not verified identity;
- deletion removes associated embeddings and indexes;
- any future cross-production speaker feature requires a separate privacy/security ADR.

## Transcripts and generated text

- transcripts may contain more searchable personal information than the source waveform;
- search indexes must remain workspace-scoped;
- transcript snippets must not appear in logs, analytics, notification previews, or support tools by default;
- generated summaries/shownotes must be labeled as generated and editable;
- hallucination and speaker-attribution uncertainty must be represented;
- deletion must remove transcript, captions, embeddings, summaries, and search indexes;
- exports must not silently include private metadata.

## Retention and deletion

The product must expose clear retention behavior before launch.

Recommended classes:

- **temporary upload fragments:** hours to a few days;
- **working intermediates:** delete soon after output completion unless required for editing/retry;
- **source and outputs:** user-controlled within plan limits;
- **failed-job temporary objects:** automated short retention;
- **operational logs:** content-free and time-bounded;
- **billing records:** minimal and retained only as required;
- **Lab corpus:** governed by its consent/license record.

Deletion requirements:

- user can delete a production and request complete derived deletion;
- database state, object storage, waveform data, transcript, embeddings, temporary objects, caches, and search indexes are covered;
- deletion events are idempotent and auditable;
- backups have documented expiry rather than false instant-erasure claims;
- legal hold, if ever supported, is explicit and exceptional;
- account deletion handles orphan projects and shared workspaces safely.

## Logging and observability

Allowed by default:

- opaque production/run/step IDs;
- status and error codes;
- sizes/durations rounded where appropriate;
- model/runtime versions;
- performance and resource metrics;
- content-free validation warnings.

Disallowed by default:

- raw transcript text;
- source filenames where unnecessary;
- signed URLs;
- access tokens;
- API keys;
- full object paths exposed across tenants;
- audio samples;
- speaker names;
- user-entered descriptions;
- model-provider raw responses containing content.

Debug content capture requires an explicit, time-limited, access-controlled procedure and customer permission when production media is involved.

## Product transparency

Users should be able to see:

- where their media is stored and processed at a useful level;
- which optional third-party/AI processing is enabled;
- retention and deletion behavior;
- whether humans may access media for support;
- whether any data is used for training;
- how to disable optional AI features;
- how to download source and outputs;
- how to delete productions and accounts;
- known limitations of transcript/speaker inference.

## Incident response baseline

Before public launch:

- assign security incident roles;
- maintain provider contacts and credential-rotation procedures;
- define media-access investigation workflow;
- test revocation and object lockdown;
- preserve content-minimized audit evidence;
- define user-notification decision process;
- document backup restore and deletion implications;
- run a tabletop scenario for cross-tenant exposure and leaked signed URLs.

## Threat scenarios for staging tests

- upload authorization reused for another workspace;
- user changes object key or production ID;
- signed read URL is leaked or replayed;
- worker receives a broader bucket credential than required;
- malicious media causes resource exhaustion;
- job cancellation leaves media in temp storage;
- failed deletion leaves waveform/transcript/embedding artifacts;
- support operator accesses content without an audit trail;
- model provider retains media contrary to expected policy;
- logs capture transcript text or tokens;
- browser cache/service worker retains private audio after logout;
- public audiogram accidentally references the private original URL.

## Release gates

Security/privacy approval requires:

- [ ] data-flow diagram current;
- [ ] subprocessors/providers registered;
- [ ] code and model manifests approved;
- [ ] tenancy tests pass;
- [ ] object authorization tests pass;
- [ ] retention jobs tested;
- [ ] production deletion tested end-to-end;
- [ ] temporary-file cleanup tested after kill/cancel/failure;
- [ ] logs scanned for content/secrets;
- [ ] no-training policy implemented and documented;
- [ ] user-facing privacy/retention copy reviewed;
- [ ] incident response and backup policy documented;
- [ ] jurisdiction-specific counsel review scheduled/completed as required.

## Open policy decisions

- default source retention period and plan limits;
- whether users may choose processing region;
- whether local-only processing is offered later;
- support-access consent workflow;
- external GPU/model provider selection;
- enterprise DPA and data-residency requirements;
- handling of shared projects and client invitations;
- public-link behavior and expiration;
- age/minor restrictions for contributed Lab data;
- whether any anonymized product analytics may include semantic categories.

These decisions must be resolved before the corresponding feature is released, not assumed by implementation.
