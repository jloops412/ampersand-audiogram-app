# Ampersand media worker

This package is the first independent CPU media-engine baseline. It runs only against an explicitly supplied local file, performs no hosted processor calls, and emits canonical Ampersand manifests plus validated WAV and MP3 outputs.

The current graph includes Semantic Audio Map V0, a conservative Processing Router V0 shadow plan, and Adaptive
Leveler V0 shadow planning: deterministic R128 timeline measurements, an Ampersand-owned confidence-bounded VAD,
provider adapters, conflict-preserving fusion, raw audit artifacts, explicit regional reasons/fallbacks, and local debug
reports. It still applies no regional processor or Leveler gain and performs only final loudness mastering until the
separate promotion gates pass.

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

See [Processing Router V0](../../docs/architecture/PROCESSING_ROUTER_V0.md) for the settings snapshot, conservative
policy, safe overrides, admission boundary, and machine-readable decision report.
