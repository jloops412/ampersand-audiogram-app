# Ampersand media worker

This package is the first independent CPU media-engine baseline. It runs only against an explicitly supplied local file, performs no hosted processor calls, and emits canonical Ampersand manifests plus validated WAV and MP3 outputs.

The current graph intentionally protects unknown content and performs only final loudness mastering. Content analysis, enhancement, routing, and the Adaptive Leveler arrive through later issues after their quality and admission gates pass.

Run it from the repository root:

```bash
uv run --package ampersand-media-worker ampersand-engine process SOURCE --output NEW_DIRECTORY
```
