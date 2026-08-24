# Local Engine CLI

**Status:** Issues #21/#22 foundation + Processing Router/Adaptive Leveler V0 shadow planning and Leveler evaluation rendering
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

Use an explicit complete settings manifest for the controls admitted into the private beta:

```json
{
  "schema_version": "1.0.0",
  "mastering": {
    "target_integrated_lufs": -18.0,
    "max_true_peak_dbtp": -1.5,
    "target_loudness_range_lu": 12.0
  },
  "export": {
    "wav": true,
    "mp3": true,
    "mp3_bitrate_kbps": 192
  }
}
```

```bash
uv run --package ampersand-media-worker ampersand-engine process \
  /tmp/ampersand-fixture.wav \
  --output /tmp/ampersand-production-custom \
  --intent natural_voice \
  --settings /absolute/path/to/settings.json \
  --settings-source run_override
```

The engine validates the safe ranges, resolves a stable settings identity/hash, includes that snapshot in the run
fingerprint, and writes `resolved-settings.json`. `--settings-source template` additionally requires an immutable
`--template-version-id`.

For controlled Leveler, protection, channel, degradation, and long-form inputs, generate the versioned corpus separately:

```bash
uv run ampersand-generate-corpus /tmp/ampersand-fixture-corpus
```

See [Synthetic Fixture Corpus V0](../research/SYNTHETIC_FIXTURE_CORPUS_V0.md). Generated voice-shaped controls are technical fixtures, not substitutes for rights-cleared human speech or listening tests.

Prepare and serve a local blinded experiment separately:

```bash
uv run ampersand-listening prepare /absolute/path/to/experiment.json --output /tmp/listening-session
uv run ampersand-listening serve /tmp/listening-session
```

See [Blinded Listening and Regression Harness V0](../research/BLINDED_LISTENING_HARNESS_V0.md). The harness accepts
immutable candidate masters and never activates the shadow Leveler inside the production graph.

Make one shadow envelope audible as a separately labeled evaluation artifact:

```bash
uv run --package ampersand-media-worker ampersand-engine render-leveler-candidate \
  /absolute/path/to/exact-analysis-source.wav \
  /tmp/ampersand-production/gain-envelope.json \
  --output /tmp/ampersand-leveler-candidate
```

Use the pipeline's `artifacts/canonical.wav` as the exact analysis source when it exists. The command applies no final
loudness stage and never changes `master.wav`; its `candidate.wav` must go through blinded loudness matching. See
[Leveler Gain Renderer V0](../architecture/LEVELER_GAIN_RENDERER_V0.md).

## Deterministic graph

1. Validate the local file and normalize ffprobe metadata.
2. Hash the immutable source bytes with SHA-256.
3. Canonicalize once to 48 kHz float PCM only when necessary.
4. Measure program loudness and true peak.
5. Stream decoded PCM into a custom multiresolution min/max peak pyramid.
6. Measure 100 ms momentary/short-term loudness and frame true peak with FFmpeg `ebur128`; zero-pad only a final
   partial analysis hop, record that bounded padding, and normalize coverage back to the exact source duration.
7. Run Ampersand's first-party, confidence-bounded energy/spectral VAD on a 16 kHz analysis stream with the same
   disclosed final-partial-hop coverage policy.
8. Preserve checksummed provider-native frames separately and normalize them through provider-neutral adapters.
9. Fuse a full-coverage Semantic Map V0 with soft probabilities, provenance, optional-provider failures, and explicit conflicts.
10. Emit a local debug HTML report while protecting uncertain or unsupported content.
11. Build a deterministic, full-coverage Processing Router V0 shadow plan with reasons, fallbacks, and safe overrides.
12. Emit versioned router settings/report artifacts without applying regional cleanup to production audio.
13. Plan a deterministic Adaptive Leveler V0 shadow envelope from reliable, unprotected speech evidence.
14. Emit versioned Leveler settings/statistics and a sample-time linear Gain Envelope, without rendering it.
15. Keep short-term compression separate and every regional processor candidate shadow-only pending promotion gates.
16. Resolve and persist the exact mastering/export settings attached to the run.
17. Run two-pass final loudness normalization using those executable settings.
18. Produce the selected metadata-stripped 24-bit WAV and/or configured-bitrate MP3 masters.
19. Probe, measure, checksum, and validate outputs.
20. Emit Production, ProductionRun, JobStep, OutputManifest, and ProcessingReport records.

## Reproducibility envelope

Stable IDs and canonical JSON derive from:

- source SHA-256;
- immutable recipe serialization;
- complete resolved settings, intent, provenance, and immutable template-version identity when present;
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

The local graph implements Processing Router V0 and Adaptive Leveler V0 **planning in shadow mode**. A standalone
evaluation command can render the Leveler envelope for blind testing, but the pipeline deliberately renders no regional
processor or Leveler candidate into the master. The bootstrap VAD cannot reliably separate music from speech, so the
router fails closed to protection when region-level music evidence is unavailable. Only standards-based final loudness
mastering currently affects production output.

Checkpoint-backed VAD, ASR, diarization, reliable music classification, advanced defect detection, denoise, production
activation of the sample-accurate gain renderer, short-term compression, speaker-aware EQ, active Router execution,
and audiogram rendering remain open. Human listening and no-click render evidence are mandatory before active Leveler
or processor promotion.

## Dependency and license impact

- Pydantic: MIT; strict contract validation;
- NumPy: BSD-3-Clause; streaming waveform aggregation;
- FFmpeg: system/native dependency whose exact build and distribution obligations require the admission process in issue #12;
- pytest, Ruff, and mypy: development-only gates.

No model or checkpoint is downloaded or admitted. The VAD is first-party deterministic DSP using the already admitted NumPy execution path.

## Migration and rollback

The V2 packages are additive and do not import the legacy runtime. Semantic Map `1.0.0` placeholders upgrade explicitly through `read_semantic_map()`; unsupported versions fail closed. Rollback can disable the V0 analysis stage and keep the protected placeholder without touching source or master media. Generated production directories can be deleted without touching their original source.

See [Semantic Audio Map V0](../architecture/SEMANTIC_AUDIO_MAP_V0.md) for evidence/fusion details,
[Processing Router V0](../architecture/PROCESSING_ROUTER_V0.md) for regional policy and promotion boundaries,
[Adaptive Leveler V0](../architecture/ADAPTIVE_LEVELER_V0.md) for the control law and promotion boundary, and
[Leveler Gain Renderer V0](../architecture/LEVELER_GAIN_RENDERER_V0.md) plus
[Blinded Listening and Regression Harness V0](../research/BLINDED_LISTENING_HARNESS_V0.md) for local evaluation.
