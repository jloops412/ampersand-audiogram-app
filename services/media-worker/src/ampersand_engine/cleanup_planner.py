from __future__ import annotations

from collections.abc import Iterable
from typing import Literal, cast

from ampersand_contracts import (
    CleanupEvidenceSummary,
    CleanupPlan,
    CleanupPlannerSettings,
    CleanupSettings,
    CleanupStageDecision,
    ObservationKind,
    ProcessingEligibility,
    SemanticMap,
    SemanticObservation,
    manifest_sha256,
)

from .hashing import sha256_text, stable_id

type CleanupDecision = Literal["candidate", "manual", "protect", "no_op"]
type CleanupStage = Literal[
    "declip",
    "rumble_filter",
    "hum_reduction",
    "noise_reduction",
    "noise_gate",
    "deesser",
    "voice_enhancement",
    "compression",
]
type CandidateStage = Literal["rumble_filter", "hum_reduction", "noise_reduction"]

_STAGE_ORDER: tuple[CleanupStage, ...] = (
    "declip",
    "rumble_filter",
    "hum_reduction",
    "noise_reduction",
    "noise_gate",
    "deesser",
    "voice_enhancement",
    "compression",
)


def default_cleanup_planner_settings() -> CleanupPlannerSettings:
    return CleanupPlannerSettings()


def build_cleanup_plan(
    semantic_map: SemanticMap,
    *,
    run_id: str,
    requested_settings: CleanupSettings,
    planner_settings: CleanupPlannerSettings | None = None,
) -> CleanupPlan:
    """Resolve global cleanup without promoting uncalibrated detection into production audio.

    Smart V0.3 emits evidence-backed candidate stages, but its versioned activation
    mode is protect-only. Manual mode remains the explicit executable override.
    """

    policy = planner_settings or default_cleanup_planner_settings()
    semantic_hash = manifest_sha256(semantic_map)
    requested_hash = manifest_sha256(requested_settings)
    evidence = _summarize_evidence(semantic_map, semantic_hash=semantic_hash, policy=policy)
    identity = sha256_text(
        "|".join(
            (
                run_id,
                semantic_map.semantic_map_id,
                semantic_hash,
                requested_hash,
                manifest_sha256(policy),
            )
        )
    )
    plan_id = stable_id("cleanup-plan", identity)

    if requested_settings.mode == "manual":
        stages = _enabled_stages(requested_settings)
        decisions = _manual_stage_decisions(requested_settings)
        return _plan(
            cleanup_plan_id=plan_id,
            run_id=run_id,
            semantic_map=semantic_map,
            policy=policy,
            evidence=evidence,
            requested_settings=requested_settings,
            resolved_settings=requested_settings,
            decision="manual",
            stage_decisions=decisions,
            reason_codes=("cleanup:manual-override",),
            reasons=(
                "Applied the operator-selected deterministic cleanup controls without automatic rewriting."
                if stages
                else "Manual cleanup was selected with every control off, so cleanup was bypassed.",
            ),
            warnings=(
                "Manual cleanup is global and can alter music, ambience, breaths, transients, and source tone; "
                "compare the result with the immutable original.",
            )
            if stages
            else (),
        )

    smart_off = CleanupSettings(mode="smart")
    stale_request_warning = (
        "Smart mode ignored stored manual cleanup values and resolved a new protect-only plan."
        if _enabled_stages(requested_settings)
        else None
    )

    if not evidence.music_evidence_available:
        return _protected_plan(
            cleanup_plan_id=plan_id,
            run_id=run_id,
            semantic_map=semantic_map,
            policy=policy,
            evidence=evidence,
            requested_settings=requested_settings,
            settings=smart_off,
            reason_code="cleanup:protect-missing-music-evidence",
            reason="Protected the source because no full-coverage music-classifier evidence was available.",
            warning=stale_request_warning,
        )

    if evidence.conflict_count:
        return _protected_plan(
            cleanup_plan_id=plan_id,
            run_id=run_id,
            semantic_map=semantic_map,
            policy=policy,
            evidence=evidence,
            requested_settings=requested_settings,
            settings=smart_off,
            reason_code="cleanup:protect-conflicting-evidence",
            reason="Protected the source because reliable semantic observations conflict.",
            warning=stale_request_warning,
        )

    if (
        evidence.maximum_music_probability is not None
        and evidence.maximum_music_probability > policy.maximum_music_probability
    ):
        return _protected_plan(
            cleanup_plan_id=plan_id,
            run_id=run_id,
            semantic_map=semantic_map,
            policy=policy,
            evidence=evidence,
            requested_settings=requested_settings,
            settings=smart_off,
            reason_code="cleanup:protect-music",
            reason="Protected the source because music evidence exceeded the versioned policy ceiling.",
            warning=stale_request_warning,
        )

    if evidence.protected_region_count:
        return _protected_plan(
            cleanup_plan_id=plan_id,
            run_id=run_id,
            semantic_map=semantic_map,
            policy=policy,
            evidence=evidence,
            requested_settings=requested_settings,
            settings=smart_off,
            reason_code="cleanup:protect-uncertain-content",
            reason=(
                f"Protected the source because {evidence.protected_region_count} region(s) were uncertain, mixed, "
                "or otherwise ineligible for a global cleanup chain."
            ),
            warning=stale_request_warning,
        )

    stage_decisions = _smart_candidate_decisions(evidence, policy)
    candidates = tuple(
        cast(CandidateStage, decision.stage) for decision in stage_decisions if decision.disposition == "candidate"
    )
    if not candidates:
        return _plan(
            cleanup_plan_id=plan_id,
            run_id=run_id,
            semantic_map=semantic_map,
            policy=policy,
            evidence=evidence,
            requested_settings=requested_settings,
            resolved_settings=smart_off,
            decision="no_op",
            stage_decisions=stage_decisions,
            reason_codes=("cleanup:no-op-no-candidate",),
            reasons=("No normalized defect evidence crossed the versioned candidate thresholds.",),
            warnings=_warnings(stale_request_warning),
        )

    return _plan(
        cleanup_plan_id=plan_id,
        run_id=run_id,
        semantic_map=semantic_map,
        policy=policy,
        evidence=evidence,
        requested_settings=requested_settings,
        resolved_settings=smart_off,
        decision="candidate",
        stage_decisions=stage_decisions,
        reason_codes=tuple(f"cleanup:candidate-{stage.replace('_', '-')}" for stage in candidates),
        reasons=(
            f"Recorded protect-only cleanup candidates: {', '.join(candidates)}. "
            "No candidate changed production audio.",
        ),
        warnings=_warnings(
            stale_request_warning,
            "Candidate stages remain inactive until detector provenance, clean-preservation, and listening gates pass.",
        ),
    )


def _protected_plan(
    *,
    cleanup_plan_id: str,
    run_id: str,
    semantic_map: SemanticMap,
    policy: CleanupPlannerSettings,
    evidence: CleanupEvidenceSummary,
    requested_settings: CleanupSettings,
    settings: CleanupSettings,
    reason_code: str,
    reason: str,
    warning: str | None,
) -> CleanupPlan:
    stage_decisions = tuple(
        CleanupStageDecision(
            stage=stage,
            disposition="protected",
            reason_code=reason_code,
            reason="The whole-source protect decision prevented this stage from becoming a candidate.",
        )
        for stage in _STAGE_ORDER
    )
    return _plan(
        cleanup_plan_id=cleanup_plan_id,
        run_id=run_id,
        semantic_map=semantic_map,
        policy=policy,
        evidence=evidence,
        requested_settings=requested_settings,
        resolved_settings=settings,
        decision="protect",
        stage_decisions=stage_decisions,
        reason_codes=(reason_code,),
        reasons=(reason,),
        warnings=_warnings(warning, "Smart Cleanup made no audio changes; final mastering still ran."),
    )


def _plan(
    *,
    cleanup_plan_id: str,
    run_id: str,
    semantic_map: SemanticMap,
    policy: CleanupPlannerSettings,
    evidence: CleanupEvidenceSummary,
    requested_settings: CleanupSettings,
    resolved_settings: CleanupSettings,
    decision: CleanupDecision,
    stage_decisions: tuple[CleanupStageDecision, ...],
    reason_codes: tuple[str, ...],
    reasons: tuple[str, ...],
    warnings: tuple[str, ...] = (),
) -> CleanupPlan:
    stages = _enabled_stages(resolved_settings)
    candidates = tuple(
        cast(CandidateStage, stage_decision.stage)
        for stage_decision in stage_decisions
        if stage_decision.disposition == "candidate"
    )
    return CleanupPlan(
        cleanup_plan_id=cleanup_plan_id,
        run_id=run_id,
        semantic_map_id=semantic_map.semantic_map_id,
        mode=resolved_settings.mode,
        decision=decision,
        planner_settings_id=policy.settings_id,
        planner_settings_sha256=manifest_sha256(policy),
        planner_settings=policy,
        evidence=evidence,
        requested_settings=requested_settings,
        requested_settings_sha256=manifest_sha256(requested_settings),
        resolved_settings=resolved_settings,
        resolved_settings_sha256=manifest_sha256(resolved_settings),
        applied_stages=stages,
        candidate_stages=candidates,
        stage_decisions=stage_decisions,
        reason_codes=reason_codes,
        reasons=reasons,
        warnings=warnings,
        production_audio_changed=bool(stages),
    )


def _summarize_evidence(
    semantic_map: SemanticMap,
    *,
    semantic_hash: str,
    policy: CleanupPlannerSettings,
) -> CleanupEvidenceSummary:
    music_available = "adapter:music-classifier-unavailable" not in semantic_map.unavailable_adapters and all(
        region.music_probability is not None for region in semantic_map.regions
    )
    hum_fundamental = _resolved_mains_frequency(
        semantic_map.observations,
        minimum_probability=policy.minimum_hum_probability_for_candidate,
    )
    return CleanupEvidenceSummary(
        semantic_map_sha256=semantic_hash,
        duration_us=semantic_map.duration_us,
        region_count=len(semantic_map.regions),
        protected_region_count=sum(
            region.processing_eligibility is ProcessingEligibility.PROTECT
            or region.content_label not in {"speech", "silence"}
            for region in semantic_map.regions
        ),
        conflict_count=len(semantic_map.conflicts),
        music_evidence_available=music_available,
        stationary_noise_evidence_available=_has_stationary_noise_evidence(
            semantic_map.observations,
            minimum_probability=policy.minimum_noise_probability_for_candidate,
        ),
        maximum_music_probability=_maximum(region.music_probability for region in semantic_map.regions),
        maximum_noise_probability=_maximum(region.noise_probability for region in semantic_map.regions),
        maximum_rumble_probability=_maximum(region.rumble_probability for region in semantic_map.regions),
        maximum_hum_probability=_maximum(region.hum_probability for region in semantic_map.regions),
        maximum_clipping_probability=_maximum(region.clipping_probability for region in semantic_map.regions),
        resolved_hum_fundamental_hz=hum_fundamental,
    )


def _smart_candidate_decisions(
    evidence: CleanupEvidenceSummary,
    policy: CleanupPlannerSettings,
) -> tuple[CleanupStageDecision, ...]:
    decisions: list[CleanupStageDecision] = [
        CleanupStageDecision(
            stage="declip",
            disposition="protected",
            measured_probability=evidence.maximum_clipping_probability,
            reason_code="cleanup:protect-declip-unadmitted",
            reason="Automatic declipping is disabled because no admitted clipping detector and listening gate exist.",
        )
    ]
    decisions.append(
        _candidate_decision(
            stage="rumble_filter",
            measured=evidence.maximum_rumble_probability,
            threshold=policy.minimum_rumble_probability_for_candidate,
            evidence_ready=True,
            missing_reason="No normalized rumble probability crossed the candidate threshold.",
        )
    )
    decisions.append(
        _candidate_decision(
            stage="hum_reduction",
            measured=evidence.maximum_hum_probability,
            threshold=policy.minimum_hum_probability_for_candidate,
            evidence_ready=evidence.resolved_hum_fundamental_hz is not None,
            missing_reason="Hum requires threshold evidence plus one consistent 50 Hz or 60 Hz fundamental.",
        )
    )
    decisions.append(
        _candidate_decision(
            stage="noise_reduction",
            measured=evidence.maximum_noise_probability,
            threshold=policy.minimum_noise_probability_for_candidate,
            evidence_ready=evidence.stationary_noise_evidence_available,
            missing_reason="Generic noise probability is insufficient; stationary-noise evidence is required.",
        )
    )
    for stage in ("noise_gate", "deesser", "voice_enhancement", "compression"):
        decisions.append(
            CleanupStageDecision(
                stage=stage,
                disposition="protected",
                reason_code=f"cleanup:protect-{stage.replace('_', '-')}-manual-only",
                reason="This stage is manual-only in Smart Cleanup V0.3.",
            )
        )
    return tuple(decisions)


def _candidate_decision(
    *,
    stage: CandidateStage,
    measured: float | None,
    threshold: float,
    evidence_ready: bool,
    missing_reason: str,
) -> CleanupStageDecision:
    crosses_threshold = measured is not None and measured >= threshold and evidence_ready
    return CleanupStageDecision(
        stage=stage,
        disposition="candidate" if crosses_threshold else "skipped",
        measured_probability=measured,
        candidate_threshold=threshold,
        reason_code=(
            f"cleanup:candidate-{stage.replace('_', '-')}"
            if crosses_threshold
            else f"cleanup:skip-{stage.replace('_', '-')}"
        ),
        reason=(
            "Normalized evidence crossed the versioned protect-only candidate threshold."
            if crosses_threshold
            else missing_reason
        ),
    )


def _manual_stage_decisions(settings: CleanupSettings) -> tuple[CleanupStageDecision, ...]:
    enabled = set(_enabled_stages(settings))
    return tuple(
        CleanupStageDecision(
            stage=stage,
            disposition="applied" if stage in enabled else "skipped",
            reason_code=(
                f"cleanup:manual-apply-{stage.replace('_', '-')}"
                if stage in enabled
                else f"cleanup:manual-skip-{stage.replace('_', '-')}"
            ),
            reason=(
                "The operator explicitly enabled this deterministic global stage."
                if stage in enabled
                else "The operator left this deterministic global stage off."
            ),
        )
        for stage in _STAGE_ORDER
    )


def _enabled_stages(settings: CleanupSettings) -> tuple[CleanupStage, ...]:
    enabled = {
        "declip": settings.declip,
        "rumble_filter": settings.rumble_filter,
        "hum_reduction": settings.hum_reduction != "off",
        "noise_reduction": settings.noise_reduction != "off",
        "noise_gate": settings.noise_gate != "off",
        "deesser": settings.deesser != "off",
        "voice_enhancement": settings.voice_enhancement != "off",
        "compression": settings.compression != "off",
    }
    return tuple(stage for stage in _STAGE_ORDER if enabled[stage])


def _has_stationary_noise_evidence(
    observations: Iterable[SemanticObservation],
    *,
    minimum_probability: float,
) -> bool:
    return any(
        observation.kind is ObservationKind.NOISE_PROBABILITY
        and observation.confidence >= 0.60
        and isinstance(observation.value, (int, float))
        and not isinstance(observation.value, bool)
        and float(observation.value) >= minimum_probability
        and observation.attributes.get("noise_class") == "stationary"
        for observation in observations
    )


def _resolved_mains_frequency(
    observations: Iterable[SemanticObservation],
    *,
    minimum_probability: float,
) -> Literal[50, 60] | None:
    frequencies: list[int] = []
    for observation in observations:
        if observation.kind is not ObservationKind.HUM_PROBABILITY or observation.confidence < 0.60:
            continue
        if (
            isinstance(observation.value, bool)
            or not isinstance(observation.value, (int, float))
            or float(observation.value) < minimum_probability
        ):
            continue
        value = observation.attributes.get("fundamental_hz")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        nearest = 50 if abs(float(value) - 50.0) <= 1.0 else 60 if abs(float(value) - 60.0) <= 1.0 else None
        if nearest is not None:
            frequencies.append(nearest)
    if not frequencies or len(set(frequencies)) != 1:
        return None
    return 50 if frequencies[0] == 50 else 60


def _maximum(values: Iterable[float | None]) -> float | None:
    present = tuple(value for value in values if value is not None)
    return max(present) if present else None


def _warnings(*values: str | None) -> tuple[str, ...]:
    return tuple(value for value in values if value is not None)
