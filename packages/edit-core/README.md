# Ampersand edit core

Dependency-free TypeScript contracts for deterministic single-source spoken-word cuts.

The package owns:

- non-negative safe-integer microseconds;
- non-empty half-open `[startUs, endUs)` ranges;
- canonical cut normalization and complementary kept ranges;
- source↔output mapping with explicit cut-seam bias;
- raw-transcript word selection without persisting transcript/provider payloads;
- immutable add-cut commands, replay, undo, and redo;
- strict versioned EDL serialization;
- deterministic FFmpeg audio filter plans.

It does not import WaveSurfer, React, Node APIs, provider SDKs, or media paths. Captions, chapters, overlays, multitrack,
speed changes, and Studio integration remain later contracts.

Run:

```bash
npm run edit-core:test
```

The test suite includes deterministic generated invariants and a real FFmpeg PCM render reproducibility check when
FFmpeg/ffprobe are available. See `docs/architecture/EDIT_CORE_V0.md` and ADR-0014 for the governing boundary.
