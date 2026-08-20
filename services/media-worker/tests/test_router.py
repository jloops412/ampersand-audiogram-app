from __future__ import annotations

from typing import Literal

import pytest
from ampersand_contracts import (
    EvidenceProvenance,
    ObservationKind,
    ObservationUnit,
    ProcessingEligibility,
    ProcessingRouteOverride,
    ProcessingRouterSettings,
    RecipeVersion,
    SemanticMap,
    SemanticObservation,
    SemanticRegion,
    canonical_json_bytes,
)
from ampersand_engine.router import build_processing_router
from ampersand_engine.semantic_fusion import fuse_semantic_map
from pydantic import ValidationError

SECOND = 1_000_000
type ContentLabel = Literal["unknown", "speech", "silence", "music", "ambience", "noise", "mixed"]


def test_router_makes_clean_protect_bypass_filter_and_fallback_routes_explicit() -> None:
    semantic_map = _map(
        _region(0, "speech", ProcessingEligibility.ELIGIBLE, music=0.05, noise=0.05),
        _region(1, "silence", ProcessingEligibility.NO_OP, silence=0.96),
        _region(2, "music", ProcessingEligibility.PROTECT, music=0.98),
        _region(3, "unknown", ProcessingEligibility.PROTECT),
        _region(4, "speech", ProcessingEligibility.ELIGIBLE, music=0.05, noise=0.82),
        _region(5, "speech", ProcessingEligibility.ELIGIBLE, music=0.05, rumble=0.91),
        _region(6, "speech", ProcessingEligibility.ELIGIBLE, music=0.05, hum=0.93),
        _region(7, "speech", ProcessingEligibility.ELIGIBLE, music=0.05, clipping=0.90),
    )

    result = build_processing_router(semantic_map, run_id="run:router-categories", recipe=_recipe())
    regions = result.processing_plan.regions

    assert [region.action for region in regions] == [
        "level",
        "bypass",
        "protect",
        "protect",
        "level",
        "deterministic_filter",
        "deterministic_filter",
        "bypass",
    ]
    assert regions[0].processor_id == "processor:adaptive-leveler-shadow-v0"
    assert regions[5].processor_id == "processor:high-pass-shadow-v0"
    assert regions[6].processor_id == "processor:hum-notch-shadow-v0"
    assert "router:denoise-unavailable" in regions[4].warning_codes
    assert "router:clipping-unsupported" in regions[7].warning_codes
    assert all(region.planning_only for region in regions)
    assert result.report.production_audio_changed is False
    assert result.report.external_api_cost_usd == 0
    assert result.report.protected_region_count == 2
    assert result.report.bypassed_region_count == 2
    assert result.report.deterministic_filter_region_count == 2
    assert result.report.denoise_region_count == 0
    assert result.report.leveler_region_count == 2


def test_router_requires_music_evidence_and_recipe_admission_for_neural_route() -> None:
    missing_music = _map(_region(0, "speech", ProcessingEligibility.ELIGIBLE, noise=0.8))
    protected = build_processing_router(missing_music, run_id="run:missing-music", recipe=_recipe())
    assert protected.processing_plan.regions[0].action == "protect"
    assert protected.processing_plan.regions[0].reason_code == "router:protect-missing-music-evidence"

    noisy = _map(_region(0, "speech", ProcessingEligibility.ELIGIBLE, music=0.02, noise=0.8))
    settings = ProcessingRouterSettings(
        settings_id="router-settings:admitted-denoise",
        algorithm_version="0.1.0",
        speech_denoise_enabled=True,
        admitted_speech_denoise_processor_id="processor:admitted-denoiser-v1",
        admitted_speech_denoise_model_manifest_id="model:admitted-denoiser-v1",
    )
    blocked = build_processing_router(
        noisy,
        run_id="run:recipe-blocked",
        recipe=_recipe(allows_neural_processing=False),
        settings=settings,
    )
    assert blocked.processing_plan.regions[0].action == "level"
    assert "router:neural-disabled-by-recipe" in blocked.processing_plan.regions[0].warning_codes

    missing_model = build_processing_router(
        noisy,
        run_id="run:model-not-admitted",
        recipe=_recipe(allows_neural_processing=True).model_copy(update={"model_manifest_ids": ()}),
        settings=settings,
    )
    assert missing_model.processing_plan.regions[0].action == "level"
    assert "router:model-not-admitted-by-recipe" in missing_model.processing_plan.regions[0].warning_codes

    admitted = build_processing_router(
        noisy,
        run_id="run:recipe-admitted",
        recipe=_recipe(allows_neural_processing=True),
        settings=settings,
    )
    assert admitted.processing_plan.regions[0].action == "denoise"
    assert admitted.processing_plan.regions[0].processor_id == "processor:admitted-denoiser-v1"
    assert admitted.processing_plan.regions[0].parameters["proposed_strength"] == 0.25


def test_router_fails_closed_on_explicit_semantic_conflict() -> None:
    provenance = EvidenceProvenance(
        provenance_id="provenance:router-conflict",
        provider_id="provider:router-conflict-fixture",
        provider_version="1.0.0",
        adapter_id="adapter:router-conflict-fixture",
        adapter_version="1.0.0",
        deterministic=True,
    )
    observations = tuple(
        SemanticObservation(
            observation_id=f"observation:router-conflict:{kind.value}",
            kind=kind,
            start_us=0,
            end_us=100_000,
            confidence=0.95,
            value=0.90,
            unit=ObservationUnit.PROBABILITY,
            provenance_ref=provenance.provenance_id,
        )
        for kind in (ObservationKind.SPEECH_PROBABILITY, ObservationKind.SILENCE_PROBABILITY)
    )
    semantic_map = fuse_semantic_map(
        semantic_map_id="semantic-map:router-conflict",
        source_asset_id="asset:router-conflict",
        duration_us=100_000,
        observations=observations,
        provenance_sources=(provenance,),
    )

    result = build_processing_router(semantic_map, run_id="run:router-conflict", recipe=_recipe())

    assert result.processing_plan.regions[0].action == "protect"
    assert result.processing_plan.regions[0].reason_code == "router:protect-conflict"


def test_safe_overrides_split_timeline_are_reversible_and_change_plan_identity() -> None:
    semantic_map = _map(
        SemanticRegion(
            region_id="semantic-region:whole",
            start_us=0,
            end_us=SECOND,
            content_label="speech",
            confidence=0.95,
            speech_probability=0.95,
            music_probability=0.02,
            noise_probability=0.05,
            protected=False,
            processing_eligibility=ProcessingEligibility.ELIGIBLE,
        )
    )
    before = canonical_json_bytes(semantic_map)
    baseline = build_processing_router(semantic_map, run_id="run:override", recipe=_recipe())
    override = ProcessingRouteOverride(
        override_id="route-override:safe-bypass",
        start_us=250_000,
        end_us=750_000,
        action="bypass",
        reason="The operator requested a reversible no-processing interval.",
    )
    changed = build_processing_router(
        semantic_map,
        run_id="run:override",
        recipe=_recipe(),
        overrides=(override,),
    )

    assert canonical_json_bytes(semantic_map) == before
    assert baseline.processing_plan.processing_plan_id != changed.processing_plan.processing_plan_id
    assert [(region.start_us, region.end_us, region.action) for region in changed.processing_plan.regions] == [
        (0, 250_000, "level"),
        (250_000, 750_000, "bypass"),
        (750_000, SECOND, "level"),
    ]
    assert changed.processing_plan.regions[1].source == "user_override"
    assert changed.report.override_ids == (override.override_id,)


def test_router_rejects_unsafe_configuration_and_overlapping_overrides() -> None:
    with pytest.raises(ValidationError, match="admitted processor"):
        ProcessingRouterSettings(
            settings_id="router-settings:invalid",
            algorithm_version="0.1.0",
            speech_denoise_enabled=True,
            admitted_speech_denoise_processor_id="processor:missing-model-manifest",
        )

    semantic_map = _map(_region(0, "speech", ProcessingEligibility.ELIGIBLE, music=0.01))
    first = ProcessingRouteOverride(
        override_id="route-override:first",
        start_us=0,
        end_us=75_000,
        action="protect",
        reason="First safe override.",
    )
    second = ProcessingRouteOverride(
        override_id="route-override:second",
        start_us=50_000,
        end_us=100_000,
        action="bypass",
        reason="Overlapping safe override.",
    )
    with pytest.raises(ValueError, match="cannot overlap"):
        build_processing_router(
            semantic_map,
            run_id="run:overlap",
            recipe=_recipe(),
            overrides=(second, first),
        )

    beyond = second.model_copy(update={"start_us": 100_000, "end_us": 200_000})
    with pytest.raises(ValueError, match="exceeds"):
        build_processing_router(
            semantic_map,
            run_id="run:beyond",
            recipe=_recipe(),
            overrides=(beyond,),
        )

    duplicate_first = first.model_copy(update={"start_us": 0, "end_us": 40_000})
    duplicate_second = first.model_copy(update={"start_us": 40_000, "end_us": 80_000})
    with pytest.raises(ValueError, match="must be unique"):
        build_processing_router(
            semantic_map,
            run_id="run:duplicate",
            recipe=_recipe(),
            overrides=(duplicate_second, duplicate_first),
        )


def test_one_hour_plan_is_full_coverage_and_deterministic() -> None:
    regions = tuple(
        SemanticRegion(
            region_id=f"semantic-region:hour:{index:04d}",
            start_us=index * SECOND,
            end_us=(index + 1) * SECOND,
            content_label="speech" if index % 2 == 0 else "silence",
            confidence=0.95,
            speech_probability=0.90 if index % 2 == 0 else 0.02,
            silence_probability=0.03 if index % 2 == 0 else 0.96,
            music_probability=0.02 if index % 2 == 0 else None,
            noise_probability=0.10 if index % 2 == 0 else None,
            protected=index % 2 == 1,
            processing_eligibility=(ProcessingEligibility.ELIGIBLE if index % 2 == 0 else ProcessingEligibility.NO_OP),
        )
        for index in range(3_600)
    )
    semantic_map = SemanticMap(
        semantic_map_id="semantic-map:one-hour-router",
        source_asset_id="asset:one-hour-router",
        duration_us=3_600 * SECOND,
        analysis_hop_us=SECOND,
        regions=regions,
    )

    first = build_processing_router(semantic_map, run_id="run:one-hour-router", recipe=_recipe())
    second = build_processing_router(semantic_map, run_id="run:one-hour-router", recipe=_recipe())

    assert canonical_json_bytes(first.processing_plan) == canonical_json_bytes(second.processing_plan)
    assert canonical_json_bytes(first.report) == canonical_json_bytes(second.report)
    assert len(first.processing_plan.regions) == 3_600
    assert first.processing_plan.regions[0].start_us == 0
    assert first.processing_plan.regions[-1].end_us == 3_600 * SECOND
    assert first.report.leveler_region_count == 1_800
    assert first.report.bypassed_region_count == 1_800


def _map(*regions: SemanticRegion) -> SemanticMap:
    return SemanticMap(
        semantic_map_id="semantic-map:router-fixture",
        source_asset_id="asset:router-fixture",
        duration_us=regions[-1].end_us,
        analysis_hop_us=100_000,
        regions=regions,
    )


def _region(
    index: int,
    label: ContentLabel,
    eligibility: ProcessingEligibility,
    *,
    speech: float | None = None,
    silence: float | None = None,
    music: float | None = None,
    noise: float | None = None,
    rumble: float | None = None,
    hum: float | None = None,
    clipping: float | None = None,
) -> SemanticRegion:
    return SemanticRegion(
        region_id=f"semantic-region:router:{index}",
        start_us=index * 100_000,
        end_us=(index + 1) * 100_000,
        content_label=label,
        confidence=0.95,
        speech_probability=(0.92 if label == "speech" else speech),
        silence_probability=silence,
        music_probability=music,
        noise_probability=noise,
        rumble_probability=rumble,
        hum_probability=hum,
        clipping_probability=clipping,
        protected=eligibility is not ProcessingEligibility.ELIGIBLE,
        processing_eligibility=eligibility,
    )


def _recipe(*, allows_neural_processing: bool = False) -> RecipeVersion:
    return RecipeVersion(
        recipe_version_id="recipe:router-test:1.0.0",
        slug="router-test",
        recipe_version="1.0.0",
        display_name="Router test",
        description="Deterministic processing-router unit-test recipe.",
        analysis_steps=("semantic-map-v0",),
        processing_steps=("processing-router-v0-shadow", "adaptive-leveler-shadow", "final-master"),
        target_integrated_lufs=-16,
        max_true_peak_dbtp=-1,
        target_loudness_range_lu=11,
        output_formats=("wav", "mp3"),
        allows_neural_processing=allows_neural_processing,
        model_manifest_ids=("model:admitted-denoiser-v1",) if allows_neural_processing else (),
    )
