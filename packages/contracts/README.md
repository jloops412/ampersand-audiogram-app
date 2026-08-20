# Ampersand contracts

`python/` contains the strict Pydantic source of truth. `schema/` contains generated runtime-neutral JSON Schemas for the Studio, control plane, workers, and future SDK generation.

Every top-level contract carries `schema_version: 1.0.0`, rejects unknown fields, uses integer microseconds, and uses half-open intervals for regions. Provider-native responses are retained separately and normalized before they enter these contracts.

Regenerate schemas with:

```bash
uv run --package ampersand-media-worker ampersand-engine schemas --output packages/contracts/schema
```
