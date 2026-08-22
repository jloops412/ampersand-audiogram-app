from __future__ import annotations

from typing import Literal

from ampersand_contracts import (
    AudiogramSettings,
    CleanupSettings,
    ExportSettings,
    MasteringSettings,
    OutputMetadataSettings,
    ProductionSettings,
    RecipeVersion,
    ResolvedProductionSettings,
    manifest_sha256,
)

from .hashing import sha256_text, stable_id

ProductionIntent = Literal["podcast", "natural_voice", "broadcast", "social_voice"]
SettingsSource = Literal["recipe", "template", "run_override"]
SettingPath = Literal[
    "cleanup.noise_reduction",
    "cleanup.rumble_filter",
    "cleanup.hum_reduction",
    "cleanup.declip",
    "cleanup.noise_gate",
    "cleanup.deesser",
    "cleanup.voice_enhancement",
    "cleanup.compression",
    "mastering.target_integrated_lufs",
    "mastering.max_true_peak_dbtp",
    "mastering.target_loudness_range_lu",
    "metadata.artist",
    "metadata.album",
    "metadata.genre",
    "metadata.date",
    "metadata.comment",
    "metadata.copyright",
    "metadata.track_number",
    "audiogram.enabled",
    "audiogram.spec_version",
    "audiogram.aspect_ratio",
    "audiogram.waveform_style",
    "audiogram.waveform_scale",
    "audiogram.waveform_position",
    "audiogram.waveform_width_percent",
    "audiogram.waveform_height_percent",
    "audiogram.waveform_opacity",
    "audiogram.background_mode",
    "audiogram.background_fit",
    "audiogram.background_dim",
    "audiogram.background_color",
    "audiogram.waveform_color",
    "audiogram.text_color",
    "audiogram.text_align",
    "audiogram.headline_size_percent",
    "audiogram.subtitle_size_percent",
    "audiogram.headline",
    "audiogram.subtitle",
    "audiogram.frame_rate",
    "audiogram.render_quality",
    "export.wav",
    "export.mp3",
    "export.mp3_bitrate_kbps",
]

_SETTING_PATHS: tuple[SettingPath, ...] = (
    "cleanup.noise_reduction",
    "cleanup.rumble_filter",
    "cleanup.hum_reduction",
    "cleanup.declip",
    "cleanup.noise_gate",
    "cleanup.deesser",
    "cleanup.voice_enhancement",
    "cleanup.compression",
    "mastering.target_integrated_lufs",
    "mastering.max_true_peak_dbtp",
    "mastering.target_loudness_range_lu",
    "metadata.artist",
    "metadata.album",
    "metadata.genre",
    "metadata.date",
    "metadata.comment",
    "metadata.copyright",
    "metadata.track_number",
    "audiogram.enabled",
    "audiogram.spec_version",
    "audiogram.aspect_ratio",
    "audiogram.waveform_style",
    "audiogram.waveform_scale",
    "audiogram.waveform_position",
    "audiogram.waveform_width_percent",
    "audiogram.waveform_height_percent",
    "audiogram.waveform_opacity",
    "audiogram.background_mode",
    "audiogram.background_fit",
    "audiogram.background_dim",
    "audiogram.background_color",
    "audiogram.waveform_color",
    "audiogram.text_color",
    "audiogram.text_align",
    "audiogram.headline_size_percent",
    "audiogram.subtitle_size_percent",
    "audiogram.headline",
    "audiogram.subtitle",
    "audiogram.frame_rate",
    "audiogram.render_quality",
    "export.wav",
    "export.mp3",
    "export.mp3_bitrate_kbps",
)


def default_production_settings(recipe: RecipeVersion) -> ProductionSettings:
    return ProductionSettings(
        cleanup=CleanupSettings(),
        mastering=MasteringSettings(
            target_integrated_lufs=recipe.target_integrated_lufs,
            max_true_peak_dbtp=recipe.max_true_peak_dbtp,
            target_loudness_range_lu=recipe.target_loudness_range_lu,
        ),
        metadata=OutputMetadataSettings(),
        audiogram=AudiogramSettings(),
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
            "The selected deterministic cleanup, repair, voice-tone, and compression controls are applied globally "
            "before final mastering. They are conservative V1 baselines, not neural restoration; review gates, "
            "strong de-essing, declipping, and tone changes against the original.",
            "True background-music separation, dereverberation, and Adaptive Leveler rendering remain protected "
            "until their model, listening, and promotion gates pass.",
        ),
    )
