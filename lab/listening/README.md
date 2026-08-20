# Listening tests

The V0 localhost harness prepares deterministic, loudness-matched, opaque WAV options; supports Original/A/B preference
and clean-input preservation; stores scores privately; and reveals identities only after permanent session close.

```bash
uv run ampersand-listening prepare /absolute/path/to/experiment.json --output /tmp/listening-session
uv run ampersand-listening serve /tmp/listening-session
```

Generated audio and private sessions remain outside Git. Human listening is the final quality gate; objective metrics
are diagnostic only and V0 reports cannot promote a processor automatically.

See [Blinded Listening and Regression Harness V0](../../docs/research/BLINDED_LISTENING_HARNESS_V0.md).
