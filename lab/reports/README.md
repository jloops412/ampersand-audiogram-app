# Lab reports

The V0 harness writes a canonical `report.json` after session close. It contains raw scores, delayed identity/source
reveals, per-candidate descriptive summaries, objective diagnostics, runtime/cost, uncertainty, and warnings. Private
candidate paths and listening WAVs remain in the generated session and outside Git.

V0 reports are pilot evidence only. A promotion or rejection record requires the later formal panel, applicable
statistics, per-item failure review, and named human approval. Objective diagnostics never auto-promote a candidate.

See [Blinded Listening and Regression Harness V0](../../docs/research/BLINDED_LISTENING_HARNESS_V0.md).
