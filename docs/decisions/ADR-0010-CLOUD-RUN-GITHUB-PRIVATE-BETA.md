# ADR-0010: Cloud Run + GitHub Private-Beta Checkpoint

- **Status:** Accepted beta baseline; superseded in legacy-preservation details by ADR-0011
- **Date:** 2026-08-20
- **Issues:** #24, #18, #25, #26, #31
- **Supersedes:** no production-hosting decision

## Context

The owner requested a useful V1 beta without waiting for the full singletrack release and identified Google Cloud project
`gen-lang-client-0564514768`. The owner proposed Google Cloud's GitHub-backed **Deploy a web service** path. Ampersand
had earlier hosted prototypes, but the owner later confirmed they are not the product foundation for this fresh build.

The current engine can independently probe, analyze, build waveform/semantic/router/Leveler-shadow artifacts, perform
standards-based two-pass mastering, validate outputs, and emit reports. Active cleanup, production Adaptive Leveler,
transcript, and audiogram rendering have not passed their promotion gates.

## Decision

Prepare a new service named `ampersand-v1-beta` for continuous deployment from the GitHub repository's reviewed `main`
branch using the root `Dockerfile` and Cloud Build.

For this checkpoint:

- one container serves the React Studio/control API and invokes the independently packaged Python media engine;
- one private Cloud Storage bucket is mounted at `/data/ampersand` for immutable sources, job records, reports, and
  completed outputs;
- uploads and FFmpeg working artifacts use instance-local `/tmp` storage before durable results are copied to the mount;
- the runner processes one job at a time and the Cloud Run service is limited to one instance;
- a strong beta token stored in Secret Manager protects every media/control API; the outer Cloud Run URL may be publicly
  reachable so an ordinary browser can reach that application gate;
- instance-based billing and one minimum instance are used for unattended background processing during the test window;
- direct browser uploads are capped at 30 MiB because the current HTTP/1 Cloud Run request limit is 32 MiB;
- user-created templates are browser-local for this checkpoint, while every executed run stores its complete immutable
  settings identity and hash;
- legacy deployments are outside this build and may be removed later through a separately scoped cleanup;
- custom-domain work remains deferred.

This does not select the permanent workflow engine. Durable queues, direct resumable object uploads, workspace identity,
server-side template catalogs, multi-instance coordination, GPU/model workers, and production retention policy remain
provider-neutral follow-on work.

## Why this is acceptable

- it gets real owner feedback on an end-to-end independent engine rather than a mock interface;
- GitHub becomes the reviewed source and Cloud Build provides repeatable image deployment;
- the service has a Cloud Run revision rollback path and becomes the new build baseline;
- one instance matches the beta runner's explicit serialization and avoids unsupported shared-file write concurrency;
- local working I/O avoids treating Cloud Storage FUSE as a high-performance POSIX scratch disk;
- feature labels preserve the listening/admission gates instead of presenting shadow processors as finished.

## Costs and limitations

- a minimum instance with instance-based billing incurs ongoing compute charges even when no production is running;
- Cloud Storage FUSE is not fully POSIX-compliant and provides no multi-writer file locking;
- Cloud Run instances can still restart; a running job becomes `interrupted` and can be retried from its durable source;
- 30 MiB is suitable for initial tests and shorter/compressed programs, not the final long-form upload experience;
- browser-local templates are not shared across devices or users;
- only deterministic final mastering and selected delivery encodes affect production audio in this checkpoint.

## Promotion or rollback

Promote this decision from provisional only after a reviewed commit builds, the new service passes the documented smoke
test, a restart/retry succeeds, deletion is verified, and Cloud Logging exposes no secret or private path.

Rollback sends traffic to the previous known-good revision of this Cloud Run service or pauses it. Legacy deployment
cleanup is independent and must not be combined with a beta rollback. Scale the beta minimum instance to zero when the
test window is paused to stop continuous compute allocation.

## Primary Google references

- [Continuous deployment from a repository](https://docs.cloud.google.com/run/docs/continuous-deployment)
- [Cloud Run billing/CPU allocation](https://docs.cloud.google.com/run/docs/configuring/billing-settings)
- [Cloud Storage volume mounts](https://docs.cloud.google.com/run/docs/configuring/services/cloud-storage-volume-mounts)
- [Cloud Run quotas and request limits](https://docs.cloud.google.com/run/quotas)
- [Cloud Run secrets](https://docs.cloud.google.com/run/docs/configuring/services/secrets)
