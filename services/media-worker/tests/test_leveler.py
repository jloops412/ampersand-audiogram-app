from __future__ import annotations

from ampersand_contracts import (
    AdaptiveLevelerSettings,
    EvidenceProvenance,
    GainPoint,
    ObservationKind,
    ObservationUnit,
    ProcessingEligibility,
    SemanticConflict,
    SemanticMap,
    SemanticObservation,
    SemanticRegion,
    manifest_sha256,
)
from ampersand_engine.leveler import build_adaptive_leveler, default_leveler_settings

SECOND = 1_000_000


def test_leveler_moves_quiet_and_loud_speech_without_chasing_clean_speech() -> None:
    semantic_map = _map(
        _speech(0, -32.0),
        _speech(1, -24.0),
        _speech(2, -16.0),
    )

    result = build_adaptive_leveler(semantic_map, run_id="run:test")
    gains = _region_start_gains(result.gain_envelope.points)

    assert gains[0] > 0.0
    assert abs(gains[SECOND]) < max(abs(gains[0]), abs(gains[2 * SECOND]))
    assert gains[2 * SECOND] < 0.0
    assert result.statistics.target_speech_level_lufs == -24.0
    assert result.statistics.changed_region_count == 2
    assert result.statistics.activation_mode == "shadow"


def test_silence_music_noise_and_unknown_content_remain_unity() -> None:
    semantic_map = _map(
        _speech(0, -31.0),
        _speech(1, -31.0),
        _protected(2, "silence"),
        _protected(3, "music"),
        _protected(4, "noise"),
        _protected(5, "unknown"),
        _speech(6, -17.0),
        _speech(7, -17.0),
    )

    result = build_adaptive_leveler(semantic_map, run_id="run:protected")
    gains = _region_start_gains(result.gain_envelope.points)

    for index in range(2, 6):
        assert gains[index * SECOND] == 0.0
    assert result.statistics.protected_region_count == 4
    assert "Forced silence, noise, music" in result.statistics.reasoning[-1]


def test_explicit_semantic_conflict_remains_unity() -> None:
    provenance = EvidenceProvenance(
        provenance_id="provenance:conflict",
        provider_id="provider:test",
        provider_version="1.0.0",
        adapter_id="adapter:test",
        adapter_version="1.0.0",
        deterministic=True,
    )
    observations = (
        SemanticObservation(
            observation_id="observation:conflict:a",
            kind=ObservationKind.SPEECH_PROBABILITY,
            start_us=0,
            end_us=SECOND,
            confidence=0.9,
            value=0.95,
            unit=ObservationUnit.PROBABILITY,
            provenance_ref=provenance.provenance_id,
        ),
        SemanticObservation(
            observation_id="observation:conflict:b",
            kind=ObservationKind.SPEECH_PROBABILITY,
            start_us=0,
            end_us=SECOND,
            confidence=0.9,
            value=0.05,
            unit=ObservationUnit.PROBABILITY,
            provenance_ref=provenance.provenance_id,
        ),
    )
    conflict = SemanticConflict(
        conflict_id="semantic-conflict:test",
        start_us=0,
        end_us=SECOND,
        kinds=(ObservationKind.SPEECH_PROBABILITY,),
        observation_ids=tuple(observation.observation_id for observation in observations),
        severity=0.9,
        reason="Synthetic providers disagree.",
    )
    region = SemanticRegion(
        region_id="semantic-region:conflict",
        start_us=0,
        end_us=SECOND,
        content_label="mixed",
        confidence=0.9,
        speech_probability=0.5,
        protected=True,
        processing_eligibility=ProcessingEligibility.PROTECT,
        observations={"momentary_lufs": -30.0},
        observation_ids=tuple(observation.observation_id for observation in observations),
        conflict_ids=(conflict.conflict_id,),
    )
    semantic_map = SemanticMap(
        semantic_map_id="semantic-map:conflict-test",
        source_asset_id="asset:source",
        duration_us=SECOND,
        analysis_hop_us=SECOND,
        regions=(region,),
        provenance_sources=(provenance,),
        observations=observations,
        conflicts=(conflict,),
    )

    result = build_adaptive_leveler(semantic_map, run_id="run:conflict")

    assert [point.gain_db for point in result.gain_envelope.points] == [0.0, 0.0]
    assert result.statistics.protected_region_count == 1


def test_clean_in_band_input_is_a_valid_unity_result() -> None:
    result = build_adaptive_leveler(_map(_speech(0, -24.0)), run_id="run:clean")

    assert [point.gain_db for point in result.gain_envelope.points] == [0.0, 0.0]
    assert result.statistics.changed_duration_us == 0
    assert result.statistics.significant_corrections == ()


def test_peak_headroom_prevents_boosting_transient_risk() -> None:
    semantic_map = _map(
        _speech(0, -34.0, sample_peak_dbfs=-2.1, true_peak_dbtp=-2.05),
        _speech(1, -24.0),
        _speech(2, -24.0),
    )

    result = build_adaptive_leveler(semantic_map, run_id="run:peak")

    assert result.statistics.peak_limited_region_count == 1
    assert result.gain_envelope.points[0].gain_db <= 0.051


def test_multi_speaker_profiles_reduce_relative_level_mismatch() -> None:
    semantic_map = _map(
        _speech(0, -20.0, speaker="speaker:a"),
        _speech(1, -20.0, speaker="speaker:a"),
        _speech(2, -28.0, speaker="speaker:b"),
        _speech(3, -28.0, speaker="speaker:b"),
    )

    result = build_adaptive_leveler(semantic_map, run_id="run:speakers")
    profiles = {profile.speaker_label: profile for profile in result.statistics.speaker_statistics}

    assert profiles["speaker:a"].relative_offset_db < 0.0
    assert profiles["speaker:b"].relative_offset_db > 0.0
    assert not profiles["speaker:a"].used_global_fallback
    assert not profiles["speaker:b"].used_global_fallback


def test_short_speaker_evidence_uses_global_fallback() -> None:
    settings = AdaptiveLevelerSettings(
        settings_id="leveler-settings:speaker-fallback",
        algorithm_version="0.1.0",
        minimum_speaker_duration_us=2 * SECOND,
    )
    semantic_map = _map(
        _speech(0, -30.0, speaker="speaker:brief"),
        _speech(1, -22.0, speaker="speaker:established"),
        _speech(2, -22.0, speaker="speaker:established"),
    )

    result = build_adaptive_leveler(semantic_map, run_id="run:speaker-fallback", settings=settings)
    profiles = {profile.speaker_label: profile for profile in result.statistics.speaker_statistics}

    assert profiles["speaker:brief"].used_global_fallback
    assert profiles["speaker:brief"].relative_offset_db == 0.0
    assert not profiles["speaker:established"].used_global_fallback


def test_active_mode_refuses_missing_music_protection_evidence() -> None:
    semantic_map = _map(
        _speech(0, -30.0),
        unavailable_adapters=("adapter:music-classifier-unavailable",),
    )
    settings = default_leveler_settings(activation_mode="active")

    try:
        build_adaptive_leveler(semantic_map, run_id="run:unsafe", settings=settings)
    except ValueError as error:
        assert "music/protected-content" in str(error)
    else:
        raise AssertionError("active mode must fail closed without music/protected-content evidence")


def test_clipping_evidence_is_protected_and_returns_unity() -> None:
    clipped = _speech(0, -30.0).model_copy(
        update={"observations": {"momentary_lufs": -30.0, "clipping_probability_max": 0.9}}
    )
    result = build_adaptive_leveler(_map(clipped), run_id="run:clipped")

    assert [point.gain_db for point in result.gain_envelope.points] == [0.0, 0.0]
    assert result.statistics.eligible_region_count == 0
    assert result.statistics.protected_region_count == 0


def test_leveler_is_deterministic_and_settings_are_hashed() -> None:
    semantic_map = _map(_speech(0, -31.0), _speech(1, -24.0), _speech(2, -17.0))
    settings = AdaptiveLevelerSettings(
        settings_id="leveler-settings:custom",
        algorithm_version="0.1.0",
        comfort_band_lu=3.0,
        max_boost_db=5.0,
    )

    first = build_adaptive_leveler(semantic_map, run_id="run:deterministic", settings=settings)
    second = build_adaptive_leveler(semantic_map, run_id="run:deterministic", settings=settings)

    assert manifest_sha256(first.gain_envelope) == manifest_sha256(second.gain_envelope)
    assert manifest_sha256(first.statistics) == manifest_sha256(second.statistics)
    assert first.statistics.settings_sha256 == manifest_sha256(settings)


def test_transition_velocity_and_acceleration_are_bounded() -> None:
    settings = AdaptiveLevelerSettings(
        settings_id="leveler-settings:dynamics",
        algorithm_version="0.1.0",
        comfort_band_lu=2.0,
        max_gain_slope_db_per_second=2.0,
        max_gain_acceleration_db_per_second2=6.0,
        smoothing_time_ms=100,
        boundary_taper_ms=500,
    )
    semantic_map = _map(
        _protected(0, "silence"),
        _speech(1, -35.0),
        _speech(2, -35.0),
        _speech(3, -15.0),
        _speech(4, -15.0),
        _protected(5, "silence"),
    )

    result = build_adaptive_leveler(semantic_map, run_id="run:dynamics", settings=settings)

    assert result.statistics.maximum_gain_slope_db_per_second <= 2.000001
    assert result.statistics.maximum_gain_acceleration_db_per_second2 <= 6.000001
    assert result.gain_envelope.points[0].gain_db == 0.0
    assert result.gain_envelope.points[-1].gain_db == 0.0


def test_one_hour_timeline_remains_deterministic_and_bounded() -> None:
    regions = tuple(_speech(index, -27.0 if index % 2 else -23.0) for index in range(3_600))
    result = build_adaptive_leveler(_map(*regions), run_id="run:one-hour")

    assert result.gain_envelope.duration_us == 3_600 * SECOND
    assert len(result.gain_envelope.points) <= 3_601
    assert result.statistics.total_duration_us == 3_600 * SECOND
    assert result.statistics.gain_min_db >= -9.0
    assert result.statistics.gain_max_db <= 6.0


def _map(
    *regions: SemanticRegion,
    unavailable_adapters: tuple[str, ...] = (),
) -> SemanticMap:
    return SemanticMap(
        semantic_map_id="semantic-map:leveler-test",
        source_asset_id="asset:source",
        duration_us=regions[-1].end_us,
        analysis_hop_us=SECOND,
        regions=regions,
        unavailable_adapters=unavailable_adapters,
    )


def _speech(
    index: int,
    momentary_lufs: float,
    *,
    short_term_lufs: float | None = None,
    sample_peak_dbfs: float = -12.0,
    true_peak_dbtp: float = -11.5,
    speaker: str | None = None,
) -> SemanticRegion:
    observations: dict[str, float | int] = {
        "momentary_lufs": momentary_lufs,
        "short_term_lufs": short_term_lufs if short_term_lufs is not None else momentary_lufs,
        "sample_peak_dbfs": sample_peak_dbfs,
        "true_peak_dbtp": true_peak_dbtp,
    }
    return SemanticRegion(
        region_id=f"semantic-region:speech:{index}",
        start_us=index * SECOND,
        end_us=(index + 1) * SECOND,
        content_label="speech",
        confidence=0.92,
        speech_probability=0.94,
        silence_probability=0.02,
        active_speaker=speaker,
        active_speaker_confidence=0.9 if speaker is not None else None,
        protected=False,
        processing_eligibility=ProcessingEligibility.ELIGIBLE,
        observations=observations,
    )


def _protected(index: int, label: str) -> SemanticRegion:
    eligibility = ProcessingEligibility.NO_OP if label == "silence" else ProcessingEligibility.PROTECT
    return SemanticRegion(
        region_id=f"semantic-region:{label}:{index}",
        start_us=index * SECOND,
        end_us=(index + 1) * SECOND,
        content_label=label,
        confidence=0.95 if label != "unknown" else 0.0,
        speech_probability=0.01,
        silence_probability=0.98 if label == "silence" else 0.01,
        music_probability=0.95 if label == "music" else None,
        noise_probability=0.95 if label == "noise" else None,
        protected=True,
        processing_eligibility=eligibility,
        observations={"momentary_lufs": -40.0, "sample_peak_dbfs": -20.0},
    )


def _region_start_gains(points: tuple[GainPoint, ...]) -> dict[int, float]:
    return {point.at_us: point.gain_db for point in points}
