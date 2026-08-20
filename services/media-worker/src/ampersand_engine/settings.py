from __future__ import annotations

from typing import Literal

from ampersand_contracts import (
    ExportSettings,
    MasteringSettings,
    ProductionSettings,
    RecipeVersion,
    ResolvedProductionSettings,
    manifest_sha256,
)

from .hashing import sha256_text, stable_id

ProductionIntent = Literal["podcast", "natural_voice", "broadcast", "social_voice"]
SettingsSource = Literal["recipe", "template", "run_override"]
SettingPath = Literal[
    "mastering.target_integrated_lufs",
    "mastering.max_true_peak_dbtp",
    "mastering.target_loudness_range_lu",
    "export.wav",
    "export.mp3",
    "export.mp3_bitrate_kbps",
]

_SETTING_PATHS: tuple[SettingPath, ...] = (
    "mastering.target_integrated_lufs",
    "mastering.max_true_peak_dbtp",
    "mastering.target_loudness_range_lu",
    "export.wav",
    "export.mp3",
    "export.mp3_bitrate_kbps",
)


def default_production_settings(recipe: RecipeVersion) -> ProductionSettings:
    return ProductionSettings(
        mastering=MasteringSettings(
            target_integrated_lufs=recipe.target_integrated_lufs,
            max_true_peak_dbtp=recipe.max_true_peak_dbtp,
            target_loudness_range_lu=recipe.target_loudness_range_lu,
        ),
        export=ExportSettings(
            wav="wav" in recipe.output_formats,
            mp3="mp3" in recipe.output_formats,
            mp3_bitrate_kbps=192,
        ),
    )


def resolve_production_settings(
    recipe: RecipeVersion,
    *,
    settings: ProductionSettings | None = None,
    intent: ProductionIntent = "podcast",
    template_version_id: str | None = None,
    settings_source: SettingsSource = "recipe",
) -> ResolvedProductionSettings:
    if settings is None:
        if settings_source != "recipe":
            raise ValueError("non-recipe settings sources require an explicit complete settings value")
        selected = default_production_settings(recipe)
    else:
        selected = settings

    if settings_source == "template" and template_version_id is None:
        raise ValueError("template settings require template_version_id")
    if settings_source != "template" and template_version_id is not None:
        raise ValueError("template_version_id is valid only for template settings")

    settings_sha = manifest_sha256(selected)
    identity_hash = sha256_text(
        "|".join(
            (
                recipe.recipe_version_id,
                intent,
                template_version_id or "none",
                settings_source,
                settings_sha,
            )
        )
    )
    return ResolvedProductionSettings(
        resolved_settings_id=stable_id("resolved-settings", identity_hash),
        recipe_version_id=recipe.recipe_version_id,
        intent=intent,
        template_version_id=template_version_id,
        settings=selected,
        settings_sha256=settings_sha,
        field_provenance={path: settings_source for path in _SETTING_PATHS},
        warnings=(
            "Cleanup routing and Adaptive Leveler analysis remain shadow-only in this private beta; "
            "the executable controls affect deterministic final mastering and delivery encodes.",
        ),
    )
