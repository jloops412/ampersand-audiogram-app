# ADR-0012: Ship Guided Processing, Large Uploads, and Audiograms in the Private Beta

- **Status:** Accepted
- **Date:** 2026-08-20
- **Decision owner:** Ampersand product owner
- **Tracks:** #24, #27, #31
- **Supersedes:** the temporary 30 MiB and one-at-a-time beta constraints recorded in ADR-0010 and ADR-0011

## Context

The owner validated the new Cloud Run baseline and requested a useful iteration loop now: single and batch source
selection, large WAV/MP3 and other FFmpeg-readable inputs, automatic settings that do not require loudness expertise,
metadata, and styled audiograms with optional artwork. Background-music removal and dereverberation remain important,
but presenting an ordinary global filter as either feature would create a false quality claim.

Cloud Run's writable container filesystem consumes instance memory and is not durable. The existing private Cloud
Storage bucket and mounted job records are durable, but routing large browser uploads through the control service would
still impose request and memory constraints.

## Decision

The private beta will:

- use four guided templates as safe starting points while keeping every executable setting visible and versioned;
- actively apply conservative deterministic rumble filtering, steady-noise reduction, compression, and final
  standards-based loudness/true-peak mastering;
- allow one file or a browser-selected batch, represented as independent productions and processed serially by the
  current one-instance runner;
- initiate a random, object-scoped Cloud Storage resumable-upload session on the authenticated control plane, then let
  the browser upload 8 MiB chunks directly to the private bucket;
- verify the completed object before creating a production and read that immutable source through the mounted bucket
  without first copying the whole file into `/tmp`;
- embed user-supplied output metadata in deliverables;
- render an optional full-duration H.264/AAC audiogram with an aspect ratio, waveform style, colors, copy, and optional
  background artwork selected in the Studio;
- keep browser-local versioned templates and an immutable resolved-settings snapshot for every production.

Upload session URLs are treated as short-lived bearer capabilities: they are returned only to the authenticated browser
and are never persisted or logged. New-object generation preconditions prevent a retry from replacing a live source.
Bucket CORS is restricted to the reviewed Cloud Run and Ampersand domain origins. Public access prevention remains
enabled, and the runtime identity retains only Storage Object User on the media bucket.

## Quality boundary

The active FFT denoiser is suitable only for conservative reduction of relatively steady background noise. The UI and
report must not call it background-music separation or dereverberation. Those features require separately admitted
models or algorithms, rights-cleared evaluation fixtures, clean-input preservation, blinded listening evidence, and a
fail-closed Router policy. The Adaptive Leveler and content-aware Router also remain shadow evidence until promoted.

## Consequences

The owner can test meaningful automatic mastering, metadata, batch flow, large sources, and visual output immediately.
The 1 GiB beta limit and serial runner prevent accidental multi-job resource contention; they are product constraints,
not format limits. A later durable workflow service must replace the continuously allocated single-instance runner before
multi-user scale, and audiogram caption timing, clip selection, richer motion, true music separation, and true dereverb
remain explicit follow-on work.
