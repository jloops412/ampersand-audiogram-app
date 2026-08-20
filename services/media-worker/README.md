# Ampersand media worker

This package is the first independent CPU media-engine baseline. It runs only against an explicitly supplied local file, performs no hosted processor calls, and emits canonical Ampersand manifests plus validated WAV and MP3 outputs.

The current graph includes Semantic Audio Map V0: deterministic R128 timeline measurements, an Ampersand-owned confidence-bounded VAD, provider adapters, conflict-preserving fusion, raw audit artifacts, and a local debug report. It still protects all regional processing and performs only final loudness mastering until the Adaptive Leveler and Processing Router pass their gates.

Run it from the repository root:

```bash
uv run --package ampersand-media-worker ampersand-engine process SOURCE --output NEW_DIRECTORY
```
