# Experiments

Reproducible candidate configurations, exact manifests, seeds, and evaluation commands belong here. Candidate media
does not: keep generated or restricted audio in the governed local corpus/session store.

Author experiments against the generated `ListeningExperimentManifest` schema. Candidate paths must be relative to the
manifest directory, hashes must match immutable archived bytes, candidates compared by one item must name the same
source fixture, and evaluation prompts must not disclose candidate identities or filenames.

Preparation is the validation and materialization command:

```bash
uv run ampersand-listening prepare /absolute/path/to/experiment.json --output /tmp/listening-session
```

Research results cannot silently promote a production component. See
[Blinded Listening and Regression Harness V0](../../docs/research/BLINDED_LISTENING_HARNESS_V0.md).
