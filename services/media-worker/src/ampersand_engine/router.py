from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from itertools import pairwise
from typing import Literal

from ampersand_contracts import (
    ProcessingEligibility,
    ProcessingPlan,
    ProcessingRegion,
    ProcessingRouteDecision,
    ProcessingRouteOverride,
    ProcessingRouterReport,
    ProcessingRouterSettings,
    RecipeVersion,
    SemanticMap,
    SemanticRegion,
    manifest_sha256,
)

from .hashing import sha256_text, stable_id

ROUTER_ALGORITHM_VERSION = "0.1.0"
NO_OP_PROCESSOR_ID = "processor:no-op-v0"
LEVELER_PROCESSOR_ID = "processor:adaptive-leveler-shadow-v0"
HIGH_PASS_PROCESSOR_ID = "processor:high-pass-shadow-v0"
HUM_NOTCH_PROCESSOR_ID = "processor:hum-notch-shadow-v0"

type RouteAction = Literal["bypass", "protect", "deterministic_filter", "denoise", "level", "final_master"]
type RouteSource = Literal["recipe", "automatic", "user_override"]


@dataclass(frozen=True)
class ProcessingRouterResult:
    settings: ProcessingRouterSettings
    processing_plan: ProcessingPlan
    report: ProcessingRouterReport


@dataclass(frozen=True)
class _Route:
    action: RouteAction
    processor_id: str
    fallback_processor_id: str | None
    reason_code: str
    reason: str
    confidence: float
    parameters: dict[str, str | int | float | bool | None]
    warning_codes: tuple[str, ...] = ()
    source: RouteSource = "automatic"


_WARNING_TEXT = {
    "router:bandwidth-unsupported": (
        "Bandwidth-limited speech remains unprocessed until an admitted restoration path exists."
    ),
    "router:clipping-unsupported": (
        "Clipping evidence blocks cleanup/Leveler routing until a bounded repair path is admitted."
    ),
    "router:denoise-unavailable": (
        "Noise evidence was present, but no enabled and recipe-admitted speech denoiser was available."
    ),
    "router:deterministic-filter-disabled": (
        "Hum or rumble evidence was present while deterministic filter planning was disabled."
    ),
    "router:music-evidence-missing": (
        "Eligible speech remained protected because region-level music evidence was unavailable."
    ),
    "router:model-not-admitted-by-recipe": (
        "The configured denoiser model manifest is not admitted by this immutable recipe."
    ),
    "router:neural-disabled-by-recipe": (
        "An admitted denoiser was configured, but this immutable recipe forbids neural processing."
    ),
    "router:reverb-unsupported": (
        "Strong reverb evidence remains unprocessed until a bounded dereverberation path is admitted."
    ),
    "router:shadow-only": "Router V0 records candidates only; it does not alter production audio.",
}


def default_router_settings() -> ProcessingRouterSettings:
    return ProcessingRouterSettings(
        settings_id="router-settings:conservative-shadow-v0",
        algorithm_version=ROUTER_ALGORITHM_VERSION,
    )


def build_processing_router(
    semantic_map: SemanticMap,
    *,
    run_id: str,
    recipe: RecipeVersion,
    settings: ProcessingRouterSettings | None = None,
    overrides: Sequence[ProcessingRouteOverride] = (),
) -> ProcessingRouterResult:
    """Build one deterministic, auditable, shadow-only regional processing plan."""

    selected_settings = settings or default_router_settings()
    if selected_settings.algorithm_version != ROUTER_ALGORITHM_VERSION:
        raise ValueError(f"unsupported Processing Router algorithm: {selected_settings.algorithm_version}")
    ordered_overrides = _validated_overrides(overrides, duration_us=semantic_map.duration_us)
    settings_sha = manifest_sha256(selected_settings)
    semantic_sha = manifest_sha256(semantic_map)
    recipe_sha = manifest_sha256(recipe)
    override_sha = sha256_text("|".join(manifest_sha256(override) for override in ordered_overrides))
    plan_identity = sha256_text(
        "|".join(
            (
                run_id,
                semantic_sha,
                recipe_sha,
                settings_sha,
                override_sha,
                ROUTER_ALGORITHM_VERSION,
            )
        )
    )
    plan_id = stable_id("processing-plan", plan_identity)

    processing_regions: list[ProcessingRegion] = []
    decisions: list[ProcessingRouteDecision] = []
    override_cursor = 0
    for semantic_region in semantic_map.regions:
        while (
            override_cursor < len(ordered_overrides)
            and ordered_overrides[override_cursor].end_us <= semantic_region.start_us
        ):
            override_cursor += 1
        region_overrides: list[ProcessingRouteOverride] = []
        candidate_index = override_cursor
        while (
            candidate_index < len(ordered_overrides)
            and ordered_overrides[candidate_index].start_us < semantic_region.end_us
        ):
            candidate_override = ordered_overrides[candidate_index]
            if candidate_override.end_us > semantic_region.start_us:
                region_overrides.append(candidate_override)
            candidate_index += 1

        boundaries = {semantic_region.start_us, semantic_region.end_us}
        for candidate_override in region_overrides:
            boundaries.add(max(semantic_region.start_us, candidate_override.start_us))
            boundaries.add(min(semantic_region.end_us, candidate_override.end_us))
        local_override_index = 0
        for start_us, end_us in pairwise(sorted(boundaries)):
            while (
                local_override_index < len(region_overrides)
                and region_overrides[local_override_index].end_us <= start_us
            ):
                local_override_index += 1
            selected_override = (
                region_overrides[local_override_index]
                if local_override_index < len(region_overrides)
                and region_overrides[local_override_index].start_us <= start_us
                and region_overrides[local_override_index].end_us >= end_us
                else None
            )
            route = (
                _override_route(selected_override)
                if selected_override is not None
                else _semantic_route(semantic_region, settings=selected_settings, recipe=recipe)
            )
            segment_identity = sha256_text(
                "|".join(
                    (
                        plan_id,
                        semantic_region.region_id,
                        str(start_us),
                        str(end_us),
                        route.action,
                        route.processor_id,
                        route.reason_code,
                        selected_override.override_id if selected_override is not None else "automatic",
                    )
                )
            )
            processing_region_id = stable_id("processing-region", segment_identity)
            transition_us = min(selected_settings.transition_us, (end_us - start_us) // 2)
            processing_region = ProcessingRegion(
                processing_region_id=processing_region_id,
                start_us=start_us,
                end_us=end_us,
                action=route.action,
                processor_id=route.processor_id,
                confidence=round(route.confidence, 6),
                reason_code=route.reason_code,
                reason=route.reason,
                parameters=route.parameters,
                fallback_processor_id=route.fallback_processor_id,
                warning_codes=route.warning_codes,
                transition_us=transition_us,
                source=route.source,
                planning_only=True,
            )
            decision = ProcessingRouteDecision(
                decision_id=stable_id("route-decision", segment_identity),
                processing_region_id=processing_region_id,
                semantic_region_ids=(semantic_region.region_id,),
                action=route.action,
                processor_id=route.processor_id,
                fallback_processor_id=route.fallback_processor_id,
                reason_code=route.reason_code,
                reason=route.reason,
                confidence=round(route.confidence, 6),
                parameters=route.parameters,
                warning_codes=route.warning_codes,
            )
            processing_regions.append(processing_region)
            decisions.append(decision)

    plan = ProcessingPlan(
        processing_plan_id=plan_id,
        run_id=run_id,
        recipe_version_id=recipe.recipe_version_id,
        semantic_map_id=semantic_map.semantic_map_id,
        duration_us=semantic_map.duration_us,
        regions=tuple(processing_regions),
        global_steps=(
            "processing-router-v0-shadow",
            "adaptive-leveler-shadow",
            "two-pass-loudness-master",
            "output-validation",
        ),
    )
    plan_sha = manifest_sha256(plan)
    counts = Counter(decision.action for decision in decisions)
    warning_codes = {code for decision in decisions for code in decision.warning_codes}
    warning_codes.add("router:shadow-only")
    report = ProcessingRouterReport(
        processing_router_report_id=stable_id(
            "router-report",
            sha256_text(f"{plan_sha}|{settings_sha}|{override_sha}|{ROUTER_ALGORITHM_VERSION}"),
        ),
        run_id=run_id,
        semantic_map_id=semantic_map.semantic_map_id,
        recipe_version_id=recipe.recipe_version_id,
        settings_id=selected_settings.settings_id,
        settings_sha256=settings_sha,
        algorithm_version=ROUTER_ALGORITHM_VERSION,
        processing_plan_id=plan.processing_plan_id,
        processing_plan_sha256=plan_sha,
        decisions=tuple(decisions),
        override_ids=tuple(override.override_id for override in ordered_overrides),
        protected_region_count=counts["protect"],
        bypassed_region_count=counts["bypass"],
        deterministic_filter_region_count=counts["deterministic_filter"],
        denoise_region_count=counts["denoise"],
        leveler_region_count=counts["level"],
        warnings=tuple(_WARNING_TEXT[code] for code in sorted(warning_codes)),
    )
    return ProcessingRouterResult(settings=selected_settings, processing_plan=plan, report=report)


def _validated_overrides(
    overrides: Sequence[ProcessingRouteOverride],
    *,
    duration_us: int,
) -> tuple[ProcessingRouteOverride, ...]:
    ordered = tuple(sorted(overrides, key=lambda item: (item.start_us, item.end_us, item.override_id)))
    if len({override.override_id for override in ordered}) != len(ordered):
        raise ValueError("processing-route override IDs must be unique")
    previous_end = 0
    for override in ordered:
        if override.end_us > duration_us:
            raise ValueError(f"processing-route override {override.override_id} exceeds the Semantic Map duration")
        if override.start_us < previous_end:
            raise ValueError("processing-route overrides cannot overlap")
        previous_end = override.end_us
    return ordered


def _override_route(override: ProcessingRouteOverride) -> _Route:
    action: RouteAction = override.action
    return _Route(
        action=action,
        processor_id=NO_OP_PROCESSOR_ID,
        fallback_processor_id=NO_OP_PROCESSOR_ID,
        reason_code=f"router:user-{override.action}",
        reason=override.reason,
        confidence=1.0,
        parameters={"override_id": override.override_id, "planning_mode": "shadow", "wet_mix": 0.0},
        source="user_override",
    )


def _semantic_route(
    region: SemanticRegion,
    *,
    settings: ProcessingRouterSettings,
    recipe: RecipeVersion,
) -> _Route:
    if region.conflict_ids:
        return _protect_route(
            region,
            reason_code="router:protect-conflict",
            reason="Conflicting Semantic Map evidence fails closed to source protection.",
        )
    if region.content_label in {"music", "ambience", "mixed"}:
        return _protect_route(
            region,
            reason_code=f"router:protect-{region.content_label}",
            reason=f"Protected {region.content_label} content retains its intended dynamics.",
        )
    if region.processing_eligibility is ProcessingEligibility.NO_OP or region.content_label == "silence":
        return _bypass_route(
            region,
            reason_code="router:no-op-content",
            reason="Silence or explicit no-op content bypasses regional processing.",
        )
    if region.processing_eligibility is ProcessingEligibility.PROTECT or region.protected:
        return _protect_route(
            region,
            reason_code="router:protect-semantic-policy",
            reason="The Semantic Map marks this content protected or unsupported.",
        )
    if (
        region.content_label != "speech"
        or region.confidence < settings.minimum_region_confidence
        or region.speech_probability is None
        or region.speech_probability < settings.minimum_speech_probability
    ):
        return _protect_route(
            region,
            reason_code="router:protect-uncertain",
            reason="Speech/content confidence is below the conservative routing threshold.",
        )
    if region.silence_probability is not None and region.silence_probability > settings.maximum_silence_probability:
        return _bypass_route(
            region,
            reason_code="router:bypass-silence-risk",
            reason="Silence probability is too high for speech-region processing.",
        )
    if settings.require_music_evidence_for_processing and region.music_probability is None:
        return _protect_route(
            region,
            reason_code="router:protect-missing-music-evidence",
            reason="Music evidence is unavailable, so this otherwise eligible speech region remains protected.",
            warning_codes=("router:music-evidence-missing",),
        )
    if region.music_probability is not None and region.music_probability > settings.maximum_music_probability:
        return _protect_route(
            region,
            reason_code="router:protect-speech-over-music",
            reason="Music overlap exceeds the preservation threshold.",
        )
    if region.ambience_probability is not None and region.ambience_probability > settings.maximum_ambience_probability:
        return _protect_route(
            region,
            reason_code="router:protect-ambience",
            reason="Ambience confidence exceeds the preservation threshold.",
        )
    if region.overlap_probability is not None and region.overlap_probability > settings.maximum_overlap_probability:
        return _protect_route(
            region,
            reason_code="router:protect-overlap",
            reason="Overlapping speech/content exceeds the safe processing threshold.",
        )
    if region.clipping_probability is not None and region.clipping_probability > settings.maximum_clipping_probability:
        return _bypass_route(
            region,
            reason_code="router:bypass-clipping",
            reason="Clipping evidence requires a separately admitted repair path.",
            warning_codes=("router:clipping-unsupported",),
        )
    if region.reverb_probability is not None and region.reverb_probability > settings.maximum_reverb_probability:
        return _bypass_route(
            region,
            reason_code="router:bypass-reverb",
            reason="Strong reverb requires a separately admitted regional dereverberation path.",
            warning_codes=("router:reverb-unsupported",),
        )
    if (
        region.bandwidth_limit_probability is not None
        and region.bandwidth_limit_probability > settings.maximum_bandwidth_limit_probability
    ):
        return _bypass_route(
            region,
            reason_code="router:bypass-bandwidth-limit",
            reason="Bandwidth-limited speech requires a separately admitted restoration path.",
            warning_codes=("router:bandwidth-unsupported",),
        )
    if region.hum_probability is not None and region.hum_probability >= settings.minimum_hum_probability_for_filter:
        if settings.deterministic_filters_enabled:
            return _filter_route(
                region,
                processor_id=HUM_NOTCH_PROCESSOR_ID,
                reason_code="router:candidate-hum-notch",
                reason="Confident hum evidence selects a bounded deterministic notch-filter candidate.",
                parameters={
                    "fundamental_hz": "detect_50_or_60",
                    "maximum_notch_depth_db": 9.0,
                    "maximum_harmonics": 3,
                },
                evidence_probability=region.hum_probability,
            )
        return _level_route(region, warning_codes=("router:deterministic-filter-disabled",))
    if (
        region.rumble_probability is not None
        and region.rumble_probability >= settings.minimum_rumble_probability_for_filter
    ):
        if settings.deterministic_filters_enabled:
            return _filter_route(
                region,
                processor_id=HIGH_PASS_PROCESSOR_ID,
                reason_code="router:candidate-high-pass",
                reason="Confident rumble evidence selects a bounded deterministic high-pass candidate.",
                parameters={
                    "cutoff_hz": settings.high_pass_cutoff_hz,
                    "slope_db_per_octave": settings.high_pass_slope_db_per_octave,
                },
                evidence_probability=region.rumble_probability,
            )
        return _level_route(region, warning_codes=("router:deterministic-filter-disabled",))
    if (
        region.noise_probability is not None
        and region.noise_probability >= settings.minimum_noise_probability_for_denoise
    ):
        if (
            settings.speech_denoise_enabled
            and settings.admitted_speech_denoise_processor_id is not None
            and settings.admitted_speech_denoise_model_manifest_id is not None
        ):
            if recipe.allows_neural_processing:
                if settings.admitted_speech_denoise_model_manifest_id not in recipe.model_manifest_ids:
                    return _level_route(region, warning_codes=("router:model-not-admitted-by-recipe",))
                return _Route(
                    action="denoise",
                    processor_id=settings.admitted_speech_denoise_processor_id,
                    fallback_processor_id=NO_OP_PROCESSOR_ID,
                    reason_code="router:candidate-admitted-speech-denoise",
                    reason="Eligible noisy speech selects the configured admitted denoiser at conservative strength.",
                    confidence=round(
                        min(region.confidence, region.speech_probability, region.noise_probability),
                        6,
                    ),
                    parameters={
                        "planning_mode": "shadow",
                        "model_manifest_id": settings.admitted_speech_denoise_model_manifest_id,
                        "proposed_strength": settings.denoise_strength,
                        "proposed_wet_mix": settings.denoise_strength,
                    },
                )
            return _level_route(region, warning_codes=("router:neural-disabled-by-recipe",))
        return _level_route(region, warning_codes=("router:denoise-unavailable",))
    return _level_route(region)


def _protect_route(
    region: SemanticRegion,
    *,
    reason_code: str,
    reason: str,
    warning_codes: tuple[str, ...] = (),
) -> _Route:
    return _Route(
        action="protect",
        processor_id=NO_OP_PROCESSOR_ID,
        fallback_processor_id=NO_OP_PROCESSOR_ID,
        reason_code=reason_code,
        reason=reason,
        confidence=region.confidence,
        parameters={"planning_mode": "shadow", "wet_mix": 0.0},
        warning_codes=warning_codes,
    )


def _bypass_route(
    region: SemanticRegion,
    *,
    reason_code: str,
    reason: str,
    warning_codes: tuple[str, ...] = (),
) -> _Route:
    return _Route(
        action="bypass",
        processor_id=NO_OP_PROCESSOR_ID,
        fallback_processor_id=NO_OP_PROCESSOR_ID,
        reason_code=reason_code,
        reason=reason,
        confidence=region.confidence,
        parameters={"planning_mode": "shadow", "wet_mix": 0.0},
        warning_codes=warning_codes,
    )


def _level_route(region: SemanticRegion, *, warning_codes: tuple[str, ...] = ()) -> _Route:
    speech_probability = region.speech_probability or 0.0
    return _Route(
        action="level",
        processor_id=LEVELER_PROCESSOR_ID,
        fallback_processor_id=NO_OP_PROCESSOR_ID,
        reason_code="router:candidate-adaptive-leveler",
        reason="Confident speech is eligible for the separately evaluated Adaptive Leveler shadow candidate.",
        confidence=round(min(region.confidence, speech_probability), 6),
        parameters={"activation_mode": "shadow", "planning_mode": "shadow", "wet_mix": 0.0},
        warning_codes=warning_codes,
    )


def _filter_route(
    region: SemanticRegion,
    *,
    processor_id: str,
    reason_code: str,
    reason: str,
    parameters: dict[str, str | int | float | bool | None],
    evidence_probability: float,
) -> _Route:
    return _Route(
        action="deterministic_filter",
        processor_id=processor_id,
        fallback_processor_id=NO_OP_PROCESSOR_ID,
        reason_code=reason_code,
        reason=reason,
        confidence=round(min(region.confidence, evidence_probability), 6),
        parameters={"planning_mode": "shadow", "proposed_wet_mix": 1.0, **parameters},
    )
