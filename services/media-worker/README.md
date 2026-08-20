# Ampersand media worker

This package is the first independent CPU media-engine baseline. It runs only against an explicitly supplied local file, performs no hosted processor calls, and emits canonical Ampersand manifests plus validated WAV and MP3 outputs.

The current graph includes Semantic Audio Map V0: deterministic R128 timeline measurements, an Ampersand-owned confidence-bounded VAD, provider adapters, conflict-preserving fusion, raw audit artifacts, and a local debug report. It still protects all regional processing and performs only final loudness mastering until the Adaptive Leveler and Processing Router pass their gates.

Run it from the repository root:

```bash
uv run --package ampersand-media-worker ampersand-engine process SOURCE --output NEW_DIRECTORY
```

Render its shadow Leveler envelope into a separate evaluation-only PCM24 candidate:

```bash
uv run --package ampersand-media-worker ampersand-engine render-leveler-candidate \
  EXACT_ANALYSIS_SOURCE \
  NEW_DIRECTORY/gain-envelope.json \
  --output NEW_EVALUATION_DIRECTORY
```

Use `NEW_DIRECTORY/artifacts/canonical.wav` as `EXACT_ANALYSIS_SOURCE` when the process run emitted a
`canonical-manifest.json`; otherwise use the immutable original source. This command never changes the normal master
path and deliberately skips final loudness normalization so the listening harness can prepare matched comparisons.

See [Leveler Gain Renderer V0](../../docs/architecture/LEVELER_GAIN_RENDERER_V0.md) for its deterministic artifacts,
fail-closed validation, privacy boundary, and production-promotion gates.
