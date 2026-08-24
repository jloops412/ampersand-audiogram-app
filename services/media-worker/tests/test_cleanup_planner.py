from __future__ import annotations

import pytest
from ampersand_contracts import (
    CleanupPlan,
    CleanupPlannerSettings,
    CleanupSettings,
    EvidenceProvenance,
    ObservationKind,
    ObservationUnit,
    ProcessingEligibility,
    SemanticMap,
    SemanticObservation,
    SemanticRegion,
    manifest_sha256,
)
from ampersand_engine.cleanup_planner import build_cleanup_plan


def test_smart_cleanup_fails_closed_without_music_evidence() -> None:
    semantic_map = _semantic_map(
        music_probability=None,
        unavailable_adapters=("adapter:music-classifier-unavailable",),
    )

    plan = build_cleanup_plan(
        semantic_map,
        run_id="run:missing-music",
        requested_settings=CleanupSettings(mode="smart"),
    )

    assert plan.decision == "protect"
    assert plan.reason_codes == ("cleanup:protect-missing-music-evidence",)
    assert not plan.applied_stages
    assert not plan.candidate_stages
    assert plan.production_audio_changed is False
    assert plan.evidence.semantic_map_sha256 == manifest_sha256(semantic_map)


def test_smart_cleanup_preserves_clean_and_music_bearing_maps() -> None:
    clean = build_cleanup_plan(
        _semantic_map(),
        run_id="run:clean",
        requested_settings=CleanupSettings(mode="smart"),
    )
    music = build_cleanup_plan(
        _semantic_map(music_probability=0.36),
        run_id="run:music",
        requested_settings=CleanupSettings(mode="smart"),
    )

    assert clean.decision == "no_op"
    assert clean.production_audio_changed is False
    assert not clean.candidate_stages
    assert music.decision == "protect"
    assert music.reason_codes == ("cleanup:protect-music",)


def test_smart_cleanup_protects_any_uncertain_global_region() -> None:
    plan = build_cleanup_plan(
        _semantic_map(protected=True),
        run_id="run:uncertain",
        requested_settings=CleanupSettings(mode="smart"),
    )

    assert plan.decision == "protect"
    assert plan.evidence.protected_region_count == 1
    assert all(decision.disposition == "protected" for decision in plan.stage_decisions)


@pytest.mark.parametrize(
    "expected_stage",
    ("rumble_filter", "hum_reduction", "noise_reduction"),
)
def test_smart_cleanup_records_only_matching_protect_only_candidates(
    expected_stage: str,
) -> None:
    semantic_map = {
        "rumble_filter": lambda: _semantic_map(rumble_probability=0.75),
        "hum_reduction": lambda: _semantic_map(
            hum_probability=0.80,
            observation=_probability_observation(
                ObservationKind.HUM_PROBABILITY,
                0.80,
                attributes={"fundamental_hz": 60},
            ),
        ),
        "noise_reduction": lambda: _semantic_map(
            noise_probability=0.65,
            observation=_probability_observation(
                ObservationKind.NOISE_PROBABILITY,
                0.65,
                attributes={"noise_class": "stationary"},
            ),
        ),
    }[expected_stage]()
    plan = build_cleanup_plan(
        semantic_map,
        run_id=f"run:{expected_stage}",
        requested_settings=CleanupSettings(mode="smart"),
    )

    assert plan.decision == "candidate"
    assert plan.candidate_stages == (expected_stage,)
    assert not plan.applied_stages
    assert plan.production_audio_changed is False
    selected = next(decision for decision in plan.stage_decisions if decision.stage == expected_stage)
    assert selected.disposition == "candidate"
    assert selected.measured_probability == selected.candidate_threshold


def test_generic_noise_and_clipping_do_not_become_smart_candidates() -> None:
    plan = build_cleanup_plan(
        _semantic_map(noise_probability=1.0, clipping_probability=1.0),
        run_id="run:unsupported-defects",
        requested_settings=CleanupSettings(mode="smart"),
    )

    assert plan.decision == "no_op"
    assert not plan.candidate_stages
    declip = next(decision for decision in plan.stage_decisions if decision.stage == "declip")
    denoise = next(decision for decision in plan.stage_decisions if decision.stage == "noise_reduction")
    assert declip.disposition == "protected"
    assert denoise.disposition == "skipped"


def test_manual_cleanup_preserves_exact_requested_settings() -> None:
    requested = CleanupSettings(
        mode="manual",
        noise_reduction="light",
        rumble_filter=True,
        hum_reduction="60hz",
        declip=True,
        noise_gate="light",
        deesser="light",
        voice_enhancement="natural",
        compression="gentle",
    )
    plan = build_cleanup_plan(
        _semantic_map(
            music_probability=None,
            unavailable_adapters=("adapter:music-classifier-unavailable",),
        ),
        run_id="run:manual",
        requested_settings=requested,
    )

    assert plan.decision == "manual"
    assert plan.requested_settings == requested
    assert plan.resolved_settings == requested
    assert plan.requested_settings_sha256 == manifest_sha256(requested)
    assert plan.resolved_settings_sha256 == manifest_sha256(requested)
    assert plan.production_audio_changed is True
    assert plan.applied_stages == (
        "declip",
        "rumble_filter",
        "hum_reduction",
        "noise_reduction",
        "noise_gate",
        "deesser",
        "voice_enhancement",
        "compression",
    )


def test_cleanup_plan_identity_changes_with_policy_or_evidence() -> None:
    semantic_map = _semantic_map()
    requested = CleanupSettings(mode="smart")
    first = build_cleanup_plan(semantic_map, run_id="run:identity", requested_settings=requested)
    repeated = build_cleanup_plan(semantic_map, run_id="run:identity", requested_settings=requested)
    changed_policy = build_cleanup_plan(
        semantic_map,
        run_id="run:identity",
        requested_settings=requested,
        planner_settings=CleanupPlannerSettings(maximum_music_probability=0.34),
    )
    changed_evidence = build_cleanup_plan(
        _semantic_map(music_probability=0.10),
        run_id="run:identity",
        requested_settings=requested,
    )

    assert first == repeated
    assert first.cleanup_plan_id != changed_policy.cleanup_plan_id
    assert first.cleanup_plan_id != changed_evidence.cleanup_plan_id


@pytest.mark.parametrize(
    "field_name",
    ("planner_settings_sha256", "requested_settings_sha256", "resolved_settings_sha256"),
)
def test_cleanup_plan_rejects_mismatched_embedded_hashes(field_name: str) -> None:
    plan = build_cleanup_plan(
        _semantic_map(),
        run_id="run:hash-integrity",
        requested_settings=CleanupSettings(mode="smart"),
    )
    payload = plan.model_dump(mode="json")
    payload[field_name] = "0" * 64

    with pytest.raises(ValueError, match="SHA-256 must match"):
        CleanupPlan.model_validate(payload)


@pytest.mark.parametrize(
    "case",
    ("manual-nonmanual-decision", "smart-manual-decision", "noncandidate-with-candidates"),
)
def test_cleanup_plan_rejects_impossible_mode_decision_pairs(case: str) -> None:
    requested = CleanupSettings(mode="manual" if case == "manual-nonmanual-decision" else "smart")
    plan = build_cleanup_plan(
        _semantic_map(),
        run_id=f"run:{case}",
        requested_settings=requested,
    )
    payload = plan.model_dump(mode="json")
    if case == "manual-nonmanual-decision":
        payload["decision"] = "no_op"
    elif case == "smart-manual-decision":
        payload["decision"] = "manual"
    else:
        payload["candidate_stages"] = ["rumble_filter"]

    with pytest.raises(ValueError):
        CleanupPlan.model_validate(payload)


def test_cleanup_settings_without_mode_remain_manual() -> None:
    legacy = CleanupSettings.model_validate(
        {
            "noise_reduction": "light",
            "rumble_filter": True,
            "hum_reduction": "off",
            "declip": False,
            "noise_gate": "off",
            "deesser": "off",
            "voice_enhancement": "off",
            "compression": "gentle",
        }
    )

    assert legacy.mode == "manual"


def _semantic_map(
    *,
    music_probability: float | None = 0.05,
    noise_probability: float | None = None,
    rumble_probability: float | None = None,
    hum_probability: float | None = None,
    clipping_probability: float | None = None,
    protected: bool = False,
    unavailable_adapters: tuple[str, ...] = (),
    observation: SemanticObservation | None = None,
) -> SemanticMap:
    observations = (observation,) if observation is not None else ()
    provenance = (
        (
            EvidenceProvenance(
                provenance_id="provenance:test-detector",
                provider_id="provider:test-detector",
                provider_version="test:1",
                adapter_id="adapter:test-detector",
                adapter_version="test:1",
                deterministic=True,
            ),
        )
        if observations
        else ()
    )
    region = SemanticRegion(
        region_id="semantic-region:test",
        start_us=0,
        end_us=1_000_000,
        content_label="unknown" if protected else "speech",
        confidence=0.90,
        speech_probability=0.90,
        music_probability=music_probability,
        silence_probability=0.05,
        noise_probability=noise_probability,
        clipping_probability=clipping_probability,
        rumble_probability=rumble_probability,
        hum_probability=hum_probability,
        protected=protected,
        processing_eligibility=ProcessingEligibility.PROTECT if protected else ProcessingEligibility.ELIGIBLE,
        observation_ids=tuple(item.observation_id for item in observations),
        provider_refs=tuple(item.provider_id for item in provenance),
    )
    return SemanticMap(
        semantic_map_id="semantic-map:test",
        source_asset_id="asset:test",
        duration_us=1_000_000,
        analysis_hop_us=1_000_000,
        regions=(region,),
        provenance_sources=provenance,
        observations=observations,
        unavailable_adapters=unavailable_adapters,
    )


def _probability_observation(
    kind: ObservationKind,
    value: float,
    *,
    attributes: dict[str, str | int | float | bool | None],
) -> SemanticObservation:
    return SemanticObservation(
        observation_id=f"observation:{kind.value}",
        kind=kind,
        start_us=0,
        end_us=1_000_000,
        confidence=0.90,
        value=value,
        unit=ObservationUnit.PROBABILITY,
        provenance_ref="provenance:test-detector",
        attributes=attributes,
    )
