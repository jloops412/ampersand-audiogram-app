# Publish the Ampersand V1 Private Beta on Google Cloud

**Target project:** `gen-lang-client-0564514768`

**New service:** `ampersand-v1-beta`

**Recommended region:** `us-east1`

**Source:** `jloops412/ampersand-audiogram-app`, reviewed `main` branch, root `Dockerfile`

**Status:** ready after the issue #24 branch passes GitHub checks and is merged
**Legacy deployments:** deprecated; clean up separately after this service passes smoke testing

This is the fastest safe route to a useful beta: GitHub pushes build a container through Cloud Build and deploy a new
Cloud Run revision. This service becomes the active Ampersand baseline.

## What this beta actually does

- uploads and durably preserves a source file;
- offers four quick starts plus real per-run mastering and delivery controls;
- saves reusable template versions in this browser;
- runs Ampersand's independent FFmpeg/Python analysis and deterministic final mastering;
- saves exact settings/provenance, waveform data, report, WAV/MP3 outputs, and job state;
- supports progress, browser return, retry after restart, A/B listening, downloads, and deletion.

Processing Router and Adaptive Leveler results are shadow analysis only. Neural cleanup, transcription, and audiogram
rendering are deliberately not represented as active. Direct uploads are limited to 30 MiB in this checkpoint.

## 1. Publish a reviewed Git commit first

Do not connect Cloud Run to an uncommitted workspace. The issue branch should be pushed, opened as a pull request, pass
the **V2 engine** GitHub workflow (including its container build), and be merged into `main`. Record the merge SHA.

Cloud Build will deploy future `main` pushes automatically. Do not merge or deploy while a beta production is queued or
running; this single-instance checkpoint does not yet have a permanent distributed workflow coordinator.

## 2. Prepare the Google project

Open the [project dashboard](https://console.cloud.google.com/welcome?project=gen-lang-client-0564514768), confirm the
project selector says `gen-lang-client-0564514768`, and confirm billing is enabled.

Enable these APIs if Google does not enable them during setup:

- Cloud Run Admin API;
- Cloud Build API;
- Developer Connect API;
- Artifact Registry API;
- Secret Manager API;
- Cloud Storage API.

Google documents the required roles and automatic GitHub/Cloud Build trigger in
[continuous deployment from a repository](https://docs.cloud.google.com/run/docs/continuous-deployment).

## 3. Create the private media bucket

In [Cloud Storage](https://console.cloud.google.com/storage/browser?project=gen-lang-client-0564514768), create:

- name: `gen-lang-client-0564514768-ampersand-beta-media`;
- location type: **Region**;
- region: **us-east1**;
- storage class: **Standard**;
- access control: **Uniform**;
- public access prevention: **Enforced**;
- hierarchical namespace and object versioning: **Off**;
- soft delete: **Off** for this private test-media bucket.

Cloud Storage enables seven-day soft delete by default. Turning it off here makes the confirmed Studio delete action
actually remove private test media instead of retaining a recoverable hidden copy. This is irreversible. If recovery is
more important for a later production policy, revisit that explicitly. See Google's
[soft-delete documentation](https://docs.cloud.google.com/storage/docs/soft-delete) and
[bucket creation guide](https://docs.cloud.google.com/storage/docs/creating-buckets).

Never make this bucket public.

## 4. Create the runtime identity and beta key

In **IAM & Admin → Service Accounts**, create:

- name: `ampersand-beta-runner`;
- email: `ampersand-beta-runner@gen-lang-client-0564514768.iam.gserviceaccount.com`.

On the media bucket's **Permissions** tab, grant that service account **Storage Object User**. Do not grant public or
project-wide storage access.

In [Secret Manager](https://console.cloud.google.com/security/secret-manager?project=gen-lang-client-0564514768), create
a secret named `ampersand-beta-token`. Put a long random access key in version 1 and retain that key in your password
manager; it is what you will type into the Studio gate.

Grant the runtime service account **Secret Manager Secret Accessor** on this secret only. Google recommends Secret
Manager rather than plain environment variables for sensitive values; see
[Configure secrets for Cloud Run](https://docs.cloud.google.com/run/docs/configuring/services/secrets).

## 5. Connect GitHub with “Deploy a web service”

Open [Cloud Run](https://console.cloud.google.com/run?project=gen-lang-client-0564514768), choose **Services**, then
**Connect repository** / **Deploy a web service**.

1. Select **Developer Connect** and choose **Set up with Developer Connect**.
2. Authenticate the GitHub connection if prompted.
3. Grant it access to `jloops412/ampersand-audiogram-app` only.
4. Choose branch `main`.
5. Choose build type **Dockerfile** and Dockerfile path `/Dockerfile` (repository root).
6. Click **Save** in the Developer Connect panel.
7. Set service name `ampersand-v1-beta` and region `us-east1`.
8. Select **Allow public access**. The URL must be browser-reachable; Ampersand's strong beta key still gates every
   media/control API. Do not use this mode for a public multi-user launch.
9. Expand **Containers, Networking, Security** and apply the settings below before creating the service.

## 6. Apply the required Cloud Run settings

### Container

| Setting | Value |
|---|---:|
| Container port | `8080` |
| CPU | `1` |
| Memory | `2 GiB` |
| Request timeout | `3600 seconds` |
| Maximum requests per container | `20` |
| Execution environment | second generation / automatic |

Add ordinary environment variables:

| Name | Value |
|---|---|
| `AMPERSAND_DATA_DIR` | `/data/ampersand` |
| `AMPERSAND_WORK_DIR` | `/tmp/ampersand-work` |
| `AMPERSAND_MAX_UPLOAD_BYTES` | `31457280` |

Under **Variables & Secrets**, reference secret `ampersand-beta-token`, version **1**, as environment variable
`AMPERSAND_BETA_TOKEN`. Pinning the version makes a rotation a deliberate new revision.

### Volume

Under **Volumes**, mount a **Cloud Storage bucket**:

- bucket: `gen-lang-client-0564514768-ampersand-beta-media`;
- mount path: `/data/ampersand`;
- read-only: **Off**;
- mount options: `uid=10001,gid=10001`.

Cloud Run volume mounts are not fully POSIX filesystems and do not provide multi-writer locking. Ampersand therefore
uses the mount only for durable records/assets and performs FFmpeg working I/O under `/tmp`. The fixed UID/GID matches
the non-root container user. See Google's
[Cloud Storage volume-mount guide](https://docs.cloud.google.com/run/docs/configuring/services/cloud-storage-volume-mounts).

### Identity, CPU, and scaling

- service account: `ampersand-beta-runner@gen-lang-client-0564514768.iam.gserviceaccount.com`;
- billing/CPU allocation: **Instance-based billing** (formerly “CPU always allocated”);
- service-level minimum instances: `1` while the private beta is available for processing;
- service-level maximum instances: `1`.

The runner returns a job ID before FFmpeg finishes. Instance-based billing plus one minimum instance keeps CPU available
for that background task. It incurs continuous compute cost. When testing is paused and no job is queued/running, set
the service-level minimum to `0`; set it back to `1` before processing. Google explains this behavior in
[Cloud Run billing settings](https://docs.cloud.google.com/run/docs/configuring/billing-settings) and
[minimum instances](https://docs.cloud.google.com/run/docs/configuring/min-instances).

Create the service. The first Cloud Build can take several minutes because it installs FFmpeg, the Python engine, and the
Studio/control dependencies.

## 7. Run the release smoke test

Do not call the beta usable until every item passes:

1. Open the new `run.app` URL and confirm the beta-key gate appears.
2. Enter the exact key stored in Secret Manager.
3. Confirm **Productions** loads and no legacy service credential is requested.
4. Upload a short rights-cleared WAV/MP3/M4A under 30 MiB.
5. Select each quick start at least once and confirm its visible settings change.
6. Modify a setting, save a reusable template, and launch one production.
7. Confirm queued → running → ready, then refresh the browser and reopen the production.
8. Compare Original/Master at the same play position.
9. Download every selected format and the JSON report.
10. Confirm the report's resolved-settings ID/hash and `$0.00` external API cost.
11. Delete the production, confirm it disappears after refresh, and verify its live objects are gone from the bucket.
12. In Cloud Logging, confirm no beta key, source path, or private media bytes appear in application logs.

Then test recovery: start another short production, deploy/restart only after it is safe to interrupt, confirm the job is
shown as **Interrupted**, and use **Retry without re-uploading**.

## 8. Normal publishing and rollback

After setup, each reviewed merge to `main` triggers Cloud Build and a new Cloud Run revision. Before merging, verify the
beta has no queued/running production. After deployment, repeat at least the gate, upload, process, A/B, download, reload,
and delete checks.

To roll back: open **Cloud Run → ampersand-v1-beta → Revisions → Manage traffic**, send 100% traffic to the previous
known-good revision, and run the smoke test. If the beta must be stopped, set minimum instances to `0`. Inventory and
delete deprecated deployments only in a later explicit cleanup; do not delete the project, beta bucket, or domain as
part of rollback.

## Intentionally next, not hidden

- direct resumable upload to private object storage for large/long-form audio;
- durable queue/workflow execution that scales to zero between jobs;
- server-side workspace identity and shared template catalog;
- admitted active Adaptive Leveler and conservative cleanup;
- transcription, captions, and deterministic professional audiogram rendering;
- one-hour recovery/listening proof, budgets/alerts, retention automation, and then custom-domain readiness.
