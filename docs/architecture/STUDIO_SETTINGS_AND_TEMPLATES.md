# Studio Settings and Reusable Template Architecture

**Status:** Accepted product/contract direction; implementation tracked by #25 and #31

**Last verified:** 2026-08-20
**Authority:** [ADR-0009](../decisions/ADR-0009-GOOGLE-HOSTING-RICH-STUDIO.md)

## Product rule

Ampersand supports two equally valid paths:

- **Quick start:** choose one of the intent shortcuts and run conservative recommended settings.
- **Configured production:** choose a built-in or workspace template, inspect rich settings, override any supported value, and optionally save the result as a reusable template.

The shortcuts reduce setup time. They do not hide or replace the actual settings model.

## Resolution model

Settings resolve in this order:

1. immutable `RecipeVersion` defaults and safety policy;
2. optional immutable `StudioTemplateVersion` values;
3. explicit per-production overrides;
4. engine validation, normalization, and capability checks;
5. immutable `ResolvedProductionSettings` snapshot and hash.

The engine consumes only the resolved snapshot. UI state is never an authoritative processing input. Defaults that were not changed are still expanded into the snapshot, so a future default change cannot alter an old run.

## Contract responsibilities

| Contract | Mutability | Responsibility |
|---|---:|---|
| `RecipeVersion` | Immutable | Admitted graph, processors, safe ranges, defaults, fallback/no-op policy, and supported controls |
| `ControlDefinition` | Immutable with recipe | Contract path, data type, units, allowed values/range, default, help, stage, expert flag, availability, and contraindications |
| `StudioTemplate` | Mutable catalog identity | Workspace ownership, name, description, current version, default/archive state |
| `StudioTemplateVersion` | Immutable | Base recipe version plus validated analysis, cleanup, leveler, mastering, transcript, render, and export selections |
| `ProductionSettingsOverride` | Immutable input | Only values explicitly changed for this production |
| `ResolvedProductionSettings` | Immutable run artifact | Fully expanded values, value provenance, schema/recipe/template versions, validation results, and content hash |

All IDs, versions, and hashes are provider-neutral Ampersand values.

## Settings surface

The Studio groups controls by outcome rather than exposing an unstructured wall of DSP terms.

| Group | Examples when admitted by the selected recipe |
|---|---|
| Intent and source | spoken word use case, language hint, mono/stereo handling, channel policy |
| Analysis | speech detection, speaker analysis, transcript, music/protected-content detection, analysis quality/cost mode |
| Cleanup | noise cleanup policy/strength, hum filtering, high-pass filtering, click/clipping protection, dereverb policy |
| Voice leveling | activation, comfort band, target range, maximum boost/cut, transition speed, speaker-aware behavior |
| Final master | integrated loudness target, maximum true peak, target loudness range, clean-input/no-op policy |
| Transcript and captions | language, speaker labels, caption segmentation/style, export formats |
| Audiogram and brand | aspect ratio, dimensions, background/brand assets, waveform style, captions, layout, frame rate |
| Export | WAV/MP3/video formats, sample rate/bit depth where safe, bitrate/codec profile, filenames and metadata |

The examples are not permission to create unsupported toggles. The selected recipe's `ControlDefinition` list is the source of truth. Unavailable controls remain visible only when an explanation materially helps; otherwise they are omitted.

## UX requirements

- Show the selected template and whether the current production differs from it.
- Provide Basic and Advanced views over the same contract fields; switching views must not lose values.
- Show units, safe ranges, recommended values, consequences, and why a control is unavailable.
- Support reset-to-template and reset-to-recipe separately.
- Summarize material differences before starting a run.
- Require explicit confirmation only for settings that meaningfully raise artifact, cost, privacy, or compatibility risk.
- Never silently coerce a value. Record normalization or rejection in the settings validation result.
- Make “run once with these settings” and “save as reusable template” separate actions.

## Template lifecycle

Workspace members with permission can:

- create from a built-in template, an existing workspace template version, or current production settings;
- name and describe a template;
- duplicate it;
- update it by creating a new immutable version;
- select a workspace default;
- archive and restore it without deleting historical references;
- export/import it through a versioned Ampersand document after validation.

Hard deletion is allowed only when no production/run references the template. Otherwise archive it. Future sharing across workspaces requires a separate authorization and brand-asset access design.

## Reproducibility and cache identity

The resolved settings hash participates in run idempotency and step cache keys alongside source, recipe, engine, dependency/model, and native-tool versions. Processing reports must show:

- recipe version;
- template and template version when used;
- material per-run overrides;
- complete resolved settings artifact/hash;
- validation warnings, fallbacks, protected regions, and no-op decisions.

Secrets, signed URLs, raw media, or transcript text never belong in a template/settings contract.

## Migration and compatibility

- Existing four-intent productions map each intent to an explicit built-in template version.
- An unknown or retired setting fails validation or follows a documented recipe migration; it is never silently dropped.
- Template schema migrations create a new immutable version and retain the original payload for audit/rollback.
- A worker rejects a snapshot whose schema, recipe, or required capability is unsupported.

## Implementation slices

1. Add versioned template, control-definition, override, and resolved-settings contracts plus JSON Schemas.
2. Add resolver/validation tests covering precedence, hashes, safe ranges, unavailable controls, and migration.
3. Add workspace template CRUD/version/archive authorization and durable storage.
4. Build schema-driven Basic/Advanced production settings and template management.
5. Attach the resolved snapshot to run creation, cache identity, and processing reports.
6. Map audiogram/render settings into the shared render specification in #27.
