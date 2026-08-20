# Local Engine CLI

**Status:** Issues #21 and #22 deterministic foundation + Semantic Audio Map V0
**Runtime:** local CPU, FFmpeg/ffprobe, Python 3.12
**External API cost:** $0

## Purpose

The CLI proves Ampersand's independent media graph and contracts without a hosted processor, credential, browser lifetime, or provider-native domain model. It accepts one rights-cleared local audio file and writes derived artifacts into a new directory while leaving the source bytes untouched.

## Run

```bash
uv sync --all-packages --dev
uv run ampersand-generate-fixture /tmp/ampersand-fixture.wav
uv run --package ampersand-media-worker ampersand-engine process \
  /tmp/ampersand-fixture.wav \
  --output /tmp/ampersand-production
```

The output path must not exist. The engine refuses to overwrite it and publishes no partial directory when a step fails.

## Deterministic graph

1. Validate the local file and normalize ffprobe metadata.
2. Hash the immutable source bytes with SHA-256.
3. Canonicalize once to 48 kHz float PCM only when necessary.
4. Measure program loudness and true peak.
5. Stream decoded PCM into a custom multiresolution min/max peak pyramid.
6. Measure 100 ms momentary/short-term loudness and frame true peak with FFmpeg `ebur128`.
7. Run Ampersand's first-party, confidence-bounded energy/spectral VAD on a 16 kHz analysis stream.
8. Preserve checksummed provider-native frames separately and normalize them through provider-neutral adapters.
9. Fuse a full-coverage Semantic Map V0 with soft probabilities, provenance, optional-provider failures, and explicit conflicts.
10. Emit a local debug HTML report while protecting uncertain or unsupported content.
11. Emit a Processing Plan and unity Gain Envelope; regional processing stays protected until the Leveler/Router activate.
12. Run two-pass final loudness normalization.
13. Produce metadata-stripped 24-bit WAV and 192 kb/s MP3 masters.
14. Probe, measure, checksum, and validate outputs.
15. Emit Production, ProductionRun, JobStep, OutputManifest, and ProcessingReport records.

## Reproducibility envelope

Stable IDs and canonical JSON derive from:

- source SHA-256;
- immutable recipe serialization;
- engine build ID;
- exact FFmpeg and ffprobe version strings.

Repeated runs with the same inputs and native build must produce byte-identical JSON manifests and media hashes. The same recipe on a different admitted FFmpeg build may produce different binary hashes; the recorded build provenance makes that difference explicit.

Wall-clock timestamps, absolute local paths, random IDs, credentials, and temporary-directory names are excluded from deterministic manifests.

## Validation thresholds

- WAV duration differs from source by no more than 10 ms;
- MP3 duration differs from source by no more than 120 ms;
- integrated WAV loudness is within ±0.35 LU of the recipe target;
- WAV true peak is at or below the recipe ceiling plus a 0.20 dB measurement tolerance;
- both outputs contain a readable audio stream and have recorded SHA-256 hashes.

These are technical gates, not a human audio-quality promotion. Listening evidence remains mandatory before a cleanup or Leveler recipe ships.

## Privacy and security

- only an existing local regular file is accepted;
- FFmpeg protocols are restricted to local file and pipe access;
- no hosted processor, model download, token, transcript, or network credential is used;
- original bytes are never edited or replaced;
- temporary build directories are removed after failure;
- output manifests contain portable artifact paths, not absolute source paths;
- generated synthetic fixtures contain no recorded person or customer media.

## Current limitation

The local graph now implements Semantic Map V0 and a conservative first-party VAD. It does not yet implement checkpoint-backed VAD, ASR, diarization, reliable music classification, advanced defect detection, denoise, the Adaptive Leveler, speaker-aware EQ, the Processing Router, or audiogram rendering. The VAD cannot reliably separate music from speech, so unsupported/uncertain content remains protected and only standards-based final loudness mastering affects audio. Those limits are repeated in the emitted report.

## Dependency and license impact

- Pydantic: MIT; strict contract validation;
- NumPy: BSD-3-Clause; streaming waveform aggregation;
- FFmpeg: system/native dependency whose exact build and distribution obligations require the admission process in issue #12;
- pytest, Ruff, and mypy: development-only gates.

No model or checkpoint is downloaded or admitted. The VAD is first-party deterministic DSP using the already admitted NumPy execution path.

## Migration and rollback

The V2 packages are additive and do not import the legacy runtime. Semantic Map `1.0.0` placeholders upgrade explicitly through `read_semantic_map()`; unsupported versions fail closed. Rollback can disable the V0 analysis stage and keep the protected placeholder without touching source or master media. Generated production directories can be deleted without touching their original source.

See [Semantic Audio Map V0](../architecture/SEMANTIC_AUDIO_MAP_V0.md) for contract, fusion, safety, storage, and provider-adapter details.
