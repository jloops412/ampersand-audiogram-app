# Ampersand synthetic fixture corpus

This package generates deterministic PCM16 WAV controls from mathematical functions. It contains no recorded speech, customer media, copied music, model output, or hosted-processor output.

## Generate the default corpus

```bash
uv sync --all-packages --dev
uv run ampersand-generate-corpus /tmp/ampersand-fixture-corpus
```

The default command creates the development and validation partitions but omits the optional one-hour artifact and the promotion-withheld partition. It refuses to overwrite an existing directory and atomically publishes:

```text
corpus-manifest.json
audio/*.wav
manifests/*.manifest.json
```

Every asset records its hash, byte size, media shape, source/rights/consent status, partition, visibility, session/speaker grouping, known regions, parent hash, transforms and seeds, generator version, processor/environment permissions, retention class, and deletion policy. Degraded variants and their clean parent are always emitted into the same partition.

Generate explicit controls with repeatable `--fixture` options:

```bash
uv run ampersand-generate-corpus /tmp/ampersand-level-tests \
  --fixture fixture:level-steps-development \
  --fixture fixture:protected-music-development
```

Generate the bounded-memory one-hour continuity control only when needed:

```bash
uv run ampersand-generate-corpus /tmp/ampersand-long-form \
  --partition development \
  --include-long-form
```

The historical `ampersand-generate-fixture` command remains as a compact local-engine smoke input.

## Important boundary

Voice-shaped mathematical signals can verify determinism, gain movement, transition timing, silence/music protection, channel handling, clipping diagnostics, pipeline durability, and manifest lineage. They cannot establish naturalness, intelligibility, speech identity preservation, denoise quality, or listener preference. Those promotion gates require separately governed, access-controlled, rights-cleared real recordings and blinded listening under issues #4 and #5.

The `hidden_test` label in this source package is a governance/control-path test, not a claim that public generator code creates a secret promotion set. Genuine hidden promotion material must live outside Git in the segregated Audio Lab.
