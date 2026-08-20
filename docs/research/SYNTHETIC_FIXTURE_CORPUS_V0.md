# Synthetic Fixture Corpus V0

**Status:** Automated Audio Lab foundation; real rights-cleared recordings and listening evidence remain open

**Issues:** #4 and #5

**Corpus version:** `0.1.0`

**Generator version:** `0.2.0`

**Runtime/cost:** local CPU, standard library PCM generation, $0 external API cost

## Purpose

The corpus creates deterministic, disposable test audio that can expose engine mistakes before private human recordings enter the Lab. Every waveform is generated from documented mathematical functions. It contains no linguistic performance, identifiable voice, customer media, copied composition, model output, Auphonic service/output, credential, or network dependency.

## Default controls

The development and validation set covers:

- digital silence;
- tone and known impulses;
- independent stereo channels;
- clean voice-shaped controls;
- one-speaker ±8 dB level steps;
- two synthetic speaker profiles at different levels;
- breath-, whisper-, laughter-, applause-, and transient-like controls;
- original harmonic music-only, speech-over-music, pause, and unaccompanied regions;
- deterministic HVAC-like noise, 60/120 Hz hum, echo-train reverb, hard clipping, narrowband quantization, and an abrupt noise-environment transition;
- an opt-in one-hour repeating two-speaker/silence/music/noise durability stream generated with bounded memory.

Generated WAV files are not committed. The one-hour artifact is opt-in so routine development and CI do not create a large binary.

## Manifests and lineage

`FixtureAssetManifest` and `FixtureCorpusManifest` are strict provider-neutral contracts with exported JSON Schemas. They record:

- corpus/generator version and deterministic generation command;
- audio SHA-256, size, duration, sample rate, channels, sample width, and MIME type;
- source, rights, consent, customer/personal data, and copyrighted-music status;
- development, validation, or promotion-withheld partition and visibility;
- session/speaker groups;
- clean/degraded relationship, parent ID/hash, transforms, parameters, and fixed seeds;
- expected region timing/role/protection and controlled relative levels;
- permitted environments/processors, retention class, and deletion policy.

The corpus contract rejects duplicate IDs/files, missing or cross-partition parents, parent-hash mismatch, unsafe synthetic rights flags, invalid region timelines, and inconsistent hidden-test visibility. Generation refuses overwrite and atomically renames a complete temporary corpus into place.

## Reproducibility

Two generations with the same catalog/version serialize byte-identical WAV and JSON files. Tests verify every audio hash and byte size, standalone manifests versus the corpus manifest, clean/degraded lineage, exact PCM shape, silence, stereo independence, expected level ratios, explicit hidden generation, one-hour cycle repetition, and overwrite/unknown-ID failures.

On 2026-08-20, the full one-hour generator smoke check produced a valid `115,200,044`-byte PCM16 WAV and validated corpus manifest in `0.53` wall-clock seconds in the development container. This demonstrates the repeated-block generation path; it is not representative engine-processing runtime/memory evidence and cannot satisfy the Leveler promotion gate by itself.

## Privacy and governance boundary

The source package may represent all partition semantics so code paths can be tested, but public generator code cannot create a genuinely hidden promotion set. Real hidden material belongs outside Git in a segregated, access-controlled Audio Lab. Production customer media is prohibited from this package and excluded from default Lab use.

Real recordings require the consent, rights, processor-permission, retention, deletion, restricted-storage, and no-training records defined in [Security, Privacy, and Data Governance](../SECURITY_PRIVACY_AND_DATA_GOVERNANCE.md).

## What this can and cannot prove

These controls can prove deterministic I/O, timeline decisions, relative gain behavior, silence/noise/music protection, channel preservation, clipping/peak handling, transition bounds, artifact lineage, and long-form pipeline durability.

They cannot prove naturalness, intelligibility, word preservation, speaker identity, emotional preservation, denoise quality, music quality, or listener preference. Adaptive Leveler activation and processor promotion still require separately rights-cleared speech/music fixtures, loudness-matched blinded comparisons, no-click listening, clean-input preservation, and representative one-hour runtime/memory evidence.

## Commands

```bash
uv run ampersand-generate-corpus /tmp/ampersand-corpus

uv run ampersand-generate-corpus /tmp/ampersand-long-form \
  --partition development \
  --include-long-form

uv run ampersand-generate-corpus /tmp/ampersand-selected \
  --fixture fixture:level-steps-development \
  --fixture fixture:protected-music-development
```

All destinations must be new directories.
