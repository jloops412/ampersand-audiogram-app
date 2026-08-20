# Ampersand contracts

`python/` contains the strict Pydantic source of truth. `schema/` contains generated runtime-neutral JSON Schemas for the Studio, control plane, workers, and future SDK generation.

Every top-level contract carries an explicit schema version, rejects unknown fields, uses integer microseconds, and uses half-open intervals for regions. Core issue-21 contracts remain `1.0.0`; Semantic Audio Map V0 uses `1.1.0` with an explicit reader migration from the protected `1.0.0` placeholder.

Provider-native responses are checksummed and retained separately. Product behavior consumes normalized observations whose provenance references deduplicated provider/adapter/version records. Conflicts remain explicit rather than being flattened into one categorical answer.

Regenerate schemas with:

```bash
uv run --package ampersand-media-worker ampersand-engine schemas --output packages/contracts/schema
```
