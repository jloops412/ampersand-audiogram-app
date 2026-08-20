from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import pairwise
from typing import Literal

from ampersand_contracts import (
    AdaptiveLevelerSettings,
    GainEnvelope,
    GainPoint,
    LevelerStatistics,
    ProcessingEligibility,
    SemanticMap,
    SemanticRegion,
    SignificantGainCorrection,
    SpeakerLevelStatistics,
    manifest_sha256,
)

from .hashing import sha256_text, stable_id

ALGORITHM_VERSION = "0.1.0"
GLOBAL_SPEAKER = "speaker:global"


@dataclass(frozen=True)
class LevelerResult:
    gain_envelope: GainEnvelope
    statistics: LevelerStatistics


@dataclass(frozen=True)
class _RegionEvidence:
    region: SemanticRegion
    loudness_lufs: float
    momentary_lufs: float
    short_term_lufs: float | None
    peak_dbfs: float | None
    speaker_label: str
    weight: float


def default_leveler_settings(
    *,
    activation_mode: Literal["shadow", "active"] = "shadow",
) -> AdaptiveLevelerSettings:
    return AdaptiveLevelerSettings(
        settings_id=f"leveler-settings:spoken-word-v0-{activation_mode}",
        algorithm_version=ALGORITHM_VERSION,
        activation_mode=activation_mode,
    )


def build_adaptive_leveler(
    semantic_map: SemanticMap,
    *,
    run_id: str,
    settings: AdaptiveLevelerSettings | None = None,
) -> LevelerResult:
    """Build Ampersand's deterministic content-aware gain envelope.

    This function plans gain only. The caller decides whether a shadow candidate is
    audited or an approved active envelope is rendered into audio.
    """

    selected_settings = settings or default_leveler_settings()
    if selected_settings.activation_mode == "active" and any(
        "music" in adapter_id for adapter_id in semantic_map.unavailable_adapters
    ):
        raise ValueError("active leveling requires admitted music/protected-content evidence")
    evidence = tuple(
        candidate
        for region in semantic_map.regions
        if (candidate := _eligible_evidence(region, selected_settings)) is not None
    )
    target = _target_speech_level(evidence, selected_settings)
    comfort_half = selected_settings.comfort_band_lu / 2.0
    comfort_low = target - comfort_half if target is not None else None
    comfort_high = target + comfort_half if target is not None else None

    speaker_statistics, speaker_offsets = _speaker_profiles(
        evidence,
        target=target,
        settings=selected_settings,
    )
    raw_gains, peak_limited_mask = _raw_region_gains(
        semantic_map.regions,
        evidence=evidence,
        target=target,
        comfort_low=comfort_low,
        comfort_high=comfort_high,
        speaker_offsets=speaker_offsets,
        settings=selected_settings,
    )
    eligible_mask = tuple(_eligible_evidence(region, selected_settings) is not None for region in semantic_map.regions)
    gains = _smooth_and_limit(
        semantic_map.regions,
        raw_gains=raw_gains,
        eligible_mask=eligible_mask,
        settings=selected_settings,
    )

    semantic_hash = manifest_sha256(semantic_map)
    settings_hash = manifest_sha256(selected_settings)
    envelope_id = stable_id(
        "gain-envelope",
        sha256_text(f"{semantic_hash}|{settings_hash}|{run_id}|{ALGORITHM_VERSION}"),
        length=24,
    )
    envelope = GainEnvelope(
        gain_envelope_id=envelope_id,
        run_id=run_id,
        duration_us=semantic_map.duration_us,
        points=_gain_points(semantic_map.regions, gains, semantic_map.duration_us),
        purpose="adaptive_leveler",
    )
    corrections = _significant_corrections(
        semantic_map.regions,
        gains,
        threshold_db=selected_settings.significant_correction_db,
        identity_seed=envelope_id,
    )
    statistics = _statistics(
        semantic_map=semantic_map,
        run_id=run_id,
        settings=selected_settings,
        target=target,
        comfort_low=comfort_low,
        comfort_high=comfort_high,
        gains=gains,
        eligible_mask=eligible_mask,
        speaker_statistics=speaker_statistics,
        corrections=corrections,
        envelope_id=envelope_id,
        peak_limited_mask=peak_limited_mask,
    )
    return LevelerResult(gain_envelope=envelope, statistics=statistics)


def _eligible_evidence(
    region: SemanticRegion,
    settings: AdaptiveLevelerSettings,
) -> _RegionEvidence | None:
    if (
        region.content_label != "speech"
        or region.processing_eligibility is not ProcessingEligibility.ELIGIBLE
        or region.protected
        or region.conflict_ids
        or region.confidence < settings.min_region_confidence
        or region.speech_probability is None
        or region.speech_probability < settings.min_speech_probability
        or (region.silence_probability is not None and region.silence_probability > settings.max_silence_probability)
        or (region.overlap_probability is not None and region.overlap_probability > settings.max_overlap_probability)
        or _clipping_probability(region) > settings.max_clipping_probability
    ):
        return None
    momentary = _valid_loudness(region, "momentary_lufs")
    if momentary is None:
        return None
    short_term = _valid_loudness(region, "short_term_lufs")
    loudness = momentary
    if short_term is not None:
        bounded_short_term = _clamp(short_term, momentary - 8.0, momentary + 8.0)
        weight = settings.short_term_loudness_weight
        loudness = momentary * (1.0 - weight) + bounded_short_term * weight
    peak_values = tuple(
        value
        for key in ("sample_peak_dbfs", "true_peak_dbtp")
        if (value := _summary_float(region, key)) is not None and math.isfinite(value)
    )
    speaker_label = (
        region.active_speaker
        if region.active_speaker is not None
        and region.active_speaker_confidence is not None
        and region.active_speaker_confidence >= settings.min_region_confidence
        else GLOBAL_SPEAKER
    )
    confidence_weight = region.speech_probability * region.confidence
    return _RegionEvidence(
        region=region,
        loudness_lufs=loudness,
        momentary_lufs=momentary,
        short_term_lufs=short_term,
        peak_dbfs=max(peak_values, default=None),
        speaker_label=speaker_label,
        weight=max(1.0, (region.end_us - region.start_us) * confidence_weight),
    )


def _target_speech_level(
    evidence: tuple[_RegionEvidence, ...],
    settings: AdaptiveLevelerSettings,
) -> float | None:
    if not evidence:
        return None
    robust = _weighted_quantile(
        [item.loudness_lufs for item in evidence],
        [item.weight for item in evidence],
        0.5,
    )
    return _clamp(robust, settings.target_speech_min_lufs, settings.target_speech_max_lufs)


def _speaker_profiles(
    evidence: tuple[_RegionEvidence, ...],
    *,
    target: float | None,
    settings: AdaptiveLevelerSettings,
) -> tuple[tuple[SpeakerLevelStatistics, ...], dict[str, float]]:
    if target is None:
        return (), {}
    labels = sorted({item.speaker_label for item in evidence})
    statistics: list[SpeakerLevelStatistics] = []
    offsets: dict[str, float] = {}
    for label in labels:
        items = tuple(item for item in evidence if item.speaker_label == label)
        duration_us = sum(item.region.end_us - item.region.start_us for item in items)
        robust_level = _weighted_quantile(
            [item.loudness_lufs for item in items],
            [item.weight for item in items],
            0.5,
        )
        use_global = label == GLOBAL_SPEAKER or duration_us < settings.minimum_speaker_duration_us
        offset = (
            0.0
            if use_global
            else _clamp(
                target - robust_level,
                -settings.max_speaker_offset_db,
                settings.max_speaker_offset_db,
            )
        )
        offsets[label] = offset
        statistics.append(
            SpeakerLevelStatistics(
                speaker_label=label,
                observation_count=len(items),
                eligible_duration_us=duration_us,
                robust_speech_level_lufs=round(robust_level, 6),
                relative_offset_db=round(offset, 6),
                used_global_fallback=use_global,
            )
        )
    return tuple(statistics), offsets


def _raw_region_gains(
    regions: tuple[SemanticRegion, ...],
    *,
    evidence: tuple[_RegionEvidence, ...],
    target: float | None,
    comfort_low: float | None,
    comfort_high: float | None,
    speaker_offsets: dict[str, float],
    settings: AdaptiveLevelerSettings,
) -> tuple[tuple[float, ...], tuple[bool, ...]]:
    evidence_by_region = {item.region.region_id: item for item in evidence}
    gains: list[float] = []
    peak_limited: list[bool] = []
    for region in regions:
        item = evidence_by_region.get(region.region_id)
        if item is None or target is None or comfort_low is None or comfort_high is None:
            gains.append(0.0)
            peak_limited.append(False)
            continue
        speaker_offset = speaker_offsets.get(item.speaker_label, 0.0)
        adjusted_level = item.loudness_lufs + speaker_offset
        if adjusted_level < comfort_low:
            local_correction = comfort_low - adjusted_level
        elif adjusted_level > comfort_high:
            local_correction = comfort_high - adjusted_level
        else:
            local_correction = 0.0
        requested_gain = _clamp(
            speaker_offset + local_correction,
            -settings.max_cut_db,
            settings.max_boost_db,
        )
        gain = requested_gain
        if gain > 0.0 and item.peak_dbfs is not None:
            headroom = settings.pre_master_peak_ceiling_dbfs - item.peak_dbfs
            gain = min(gain, max(0.0, headroom))
        gains.append(gain)
        peak_limited.append(gain < requested_gain - 1e-9)
    return tuple(gains), tuple(peak_limited)


def _smooth_and_limit(
    regions: tuple[SemanticRegion, ...],
    *,
    raw_gains: tuple[float, ...],
    eligible_mask: tuple[bool, ...],
    settings: AdaptiveLevelerSettings,
) -> tuple[float, ...]:
    if len(regions) != len(raw_gains) or len(regions) != len(eligible_mask):
        raise ValueError("regions, raw gains, and eligibility mask must have equal length")
    result = [0.0] * len(regions)
    for start, end in _true_runs(eligible_mask):
        run_values = list(raw_gains[start:end])
        durations = [(regions[index].end_us - regions[index].start_us) / 1_000_000 for index in range(start, end)]
        smoothed = _bidirectional_smooth(
            run_values,
            durations,
            smoothing_seconds=settings.smoothing_time_ms / 1_000,
        )
        if start > 0 and settings.boundary_taper_ms:
            _taper_start(smoothed, durations, settings.boundary_taper_ms / 1_000)
        if end < len(regions) and settings.boundary_taper_ms:
            _taper_end(smoothed, durations, settings.boundary_taper_ms / 1_000)
        smoothed = _limit_dynamics_bidirectional(
            smoothed,
            durations,
            max_slope=settings.max_gain_slope_db_per_second,
            max_acceleration=settings.max_gain_acceleration_db_per_second2,
            constrain_start=start > 0,
            constrain_end=end < len(regions),
        )
        for offset, value in enumerate(smoothed):
            result[start + offset] = _clamp(value, -settings.max_cut_db, settings.max_boost_db)
    projected = _project_global_dynamics(
        result,
        regions=regions,
        eligible_mask=eligible_mask,
        max_slope=settings.max_gain_slope_db_per_second,
        max_acceleration=settings.max_gain_acceleration_db_per_second2,
    )
    return tuple(round(value, 6) for value in projected)


def _bidirectional_smooth(
    values: list[float],
    durations: list[float],
    *,
    smoothing_seconds: float,
) -> list[float]:
    if len(values) <= 1:
        return values.copy()
    forward: list[float] = []
    state = values[0]
    for value, duration in zip(values, durations, strict=True):
        alpha = 1.0 - math.exp(-duration / smoothing_seconds)
        state += alpha * (value - state)
        forward.append(state)
    backward_reversed: list[float] = []
    state = values[-1]
    for value, duration in zip(reversed(values), reversed(durations), strict=True):
        alpha = 1.0 - math.exp(-duration / smoothing_seconds)
        state += alpha * (value - state)
        backward_reversed.append(state)
    backward = list(reversed(backward_reversed))
    return [(left + right) / 2.0 for left, right in zip(forward, backward, strict=True)]


def _limit_dynamics_bidirectional(
    values: list[float],
    durations: list[float],
    *,
    max_slope: float,
    max_acceleration: float,
    constrain_start: bool,
    constrain_end: bool,
) -> list[float]:
    if not values:
        return []
    limited = values.copy()
    for _ in range(6):
        forward = _limit_dynamics_direction(
            limited,
            durations,
            max_slope=max_slope,
            max_acceleration=max_acceleration,
            constrain_boundary=constrain_start,
        )
        backward = list(
            reversed(
                _limit_dynamics_direction(
                    list(reversed(limited)),
                    list(reversed(durations)),
                    max_slope=max_slope,
                    max_acceleration=max_acceleration,
                    constrain_boundary=constrain_end,
                )
            )
        )
        limited = [
            _closest_to_zero(value, forward_value, backward_value)
            for value, forward_value, backward_value in zip(limited, forward, backward, strict=True)
        ]
        if constrain_start:
            limited[0] = 0.0
    return limited


def _limit_dynamics_direction(
    values: list[float],
    durations: list[float],
    *,
    max_slope: float,
    max_acceleration: float,
    constrain_boundary: bool,
) -> list[float]:
    result: list[float] = []
    previous_gain = 0.0 if constrain_boundary else values[0]
    previous_slope = 0.0
    for index, (value, duration) in enumerate(zip(values, durations, strict=True)):
        if index == 0 and not constrain_boundary:
            result.append(value)
            continue
        safe_duration = max(duration, 1e-9)
        desired_slope = (value - previous_gain) / safe_duration
        slope = _clamp(
            desired_slope,
            previous_slope - max_acceleration * safe_duration,
            previous_slope + max_acceleration * safe_duration,
        )
        slope = _clamp(slope, -max_slope, max_slope)
        current = previous_gain + slope * safe_duration
        result.append(current)
        previous_gain = current
        previous_slope = slope
    return result


def _taper_start(values: list[float], durations: list[float], taper_seconds: float) -> None:
    elapsed = 0.0
    for index, duration in enumerate(durations):
        values[index] *= min(1.0, elapsed / taper_seconds)
        elapsed += duration
        if elapsed >= taper_seconds:
            break


def _taper_end(values: list[float], durations: list[float], taper_seconds: float) -> None:
    elapsed = 0.0
    for index in range(len(values) - 1, -1, -1):
        elapsed += durations[index]
        values[index] *= min(1.0, elapsed / taper_seconds)
        if elapsed >= taper_seconds:
            break


def _gain_points(
    regions: tuple[SemanticRegion, ...],
    gains: tuple[float, ...],
    duration_us: int,
) -> tuple[GainPoint, ...]:
    if not gains or all(abs(value) < 1e-9 for value in gains):
        return (GainPoint(at_us=0, gain_db=0.0), GainPoint(at_us=duration_us, gain_db=0.0))
    points = [GainPoint(at_us=region.start_us, gain_db=gain) for region, gain in zip(regions, gains, strict=True)]
    points.append(GainPoint(at_us=duration_us, gain_db=gains[-1]))
    return tuple(points)


def _significant_corrections(
    regions: tuple[SemanticRegion, ...],
    gains: tuple[float, ...],
    *,
    threshold_db: float,
    identity_seed: str,
) -> tuple[SignificantGainCorrection, ...]:
    significant = tuple(abs(gain) >= threshold_db for gain in gains)
    corrections: list[SignificantGainCorrection] = []
    for start, end in _true_runs(significant):
        run_gains = gains[start:end]
        peak = max(run_gains, key=abs)
        start_us = regions[start].start_us
        end_us = regions[end - 1].end_us
        identity = sha256_text(f"{identity_seed}|{start_us}|{end_us}|{peak:.6f}")
        corrections.append(
            SignificantGainCorrection(
                correction_id=stable_id("gain-correction", identity, length=24),
                start_us=start_us,
                end_us=end_us,
                peak_gain_db=round(peak, 6),
                reason=(
                    "Raised reliable speech that remained below the comfort band."
                    if peak > 0
                    else "Reduced reliable speech that remained above the comfort band."
                ),
            )
        )
    return tuple(corrections)


def _statistics(
    *,
    semantic_map: SemanticMap,
    run_id: str,
    settings: AdaptiveLevelerSettings,
    target: float | None,
    comfort_low: float | None,
    comfort_high: float | None,
    gains: tuple[float, ...],
    eligible_mask: tuple[bool, ...],
    speaker_statistics: tuple[SpeakerLevelStatistics, ...],
    corrections: tuple[SignificantGainCorrection, ...],
    envelope_id: str,
    peak_limited_mask: tuple[bool, ...],
) -> LevelerStatistics:
    durations = tuple(region.end_us - region.start_us for region in semantic_map.regions)
    eligible_duration = sum(duration for duration, eligible in zip(durations, eligible_mask, strict=True) if eligible)
    changed_mask = tuple(eligible and abs(gain) >= 1e-6 for gain, eligible in zip(gains, eligible_mask, strict=True))
    changed_duration = sum(duration for duration, changed in zip(durations, changed_mask, strict=True) if changed)
    total_weight = sum(durations)
    gain_mean = sum(gain * duration for gain, duration in zip(gains, durations, strict=True)) / total_weight
    maximum_slope, maximum_acceleration = _maximum_dynamics(gains, durations)
    settings_hash = manifest_sha256(settings)
    warnings: list[str] = []
    if settings.activation_mode == "shadow":
        warnings.append("Shadow candidate only; this envelope was not authorized for audio rendering.")
    if target is None:
        warnings.append("No reliable eligible speech observations were available; emitted a unity envelope.")
    if any(statistic.used_global_fallback for statistic in speaker_statistics):
        warnings.append("Missing or short speaker evidence used the conservative global speech profile.")
    if any("music" in adapter_id for adapter_id in semantic_map.unavailable_adapters):
        warnings.append("Music classification is unavailable; the candidate remains shadow-only.")
    reasoning = (
        "Used only unprotected, conflict-free speech regions above configured confidence thresholds.",
        "Blended bounded momentary and short-term loudness, then estimated robust "
        "duration/confidence-weighted speech levels and a comfort band.",
        "Clamped boost, cut, speaker offsets, peak headroom, transition slope/acceleration, and boundary taper.",
        "Forced silence, noise, music, overlap, uncertain, and unsupported regions to unity.",
    )
    stats_hash = sha256_text(f"{envelope_id}|statistics|{settings_hash}")
    return LevelerStatistics(
        leveler_statistics_id=stable_id("leveler-statistics", stats_hash, length=24),
        run_id=run_id,
        semantic_map_id=semantic_map.semantic_map_id,
        settings_id=settings.settings_id,
        settings_sha256=settings_hash,
        algorithm_version=settings.algorithm_version,
        activation_mode=settings.activation_mode,
        target_speech_level_lufs=round(target, 6) if target is not None else None,
        comfort_band_low_lufs=round(comfort_low, 6) if comfort_low is not None else None,
        comfort_band_high_lufs=round(comfort_high, 6) if comfort_high is not None else None,
        total_duration_us=semantic_map.duration_us,
        eligible_duration_us=eligible_duration,
        changed_duration_us=changed_duration,
        eligible_region_count=sum(eligible_mask),
        protected_region_count=sum(region.protected for region in semantic_map.regions),
        changed_region_count=sum(changed_mask),
        gain_min_db=round(min(gains, default=0.0), 6),
        gain_mean_db=round(gain_mean, 6),
        gain_max_db=round(max(gains, default=0.0), 6),
        maximum_gain_slope_db_per_second=round(maximum_slope, 6),
        maximum_gain_acceleration_db_per_second2=round(maximum_acceleration, 6),
        peak_limited_region_count=sum(peak_limited_mask),
        speaker_statistics=speaker_statistics,
        significant_corrections=corrections,
        reasoning=reasoning,
        warnings=tuple(warnings),
    )


def _summary_float(region: SemanticRegion, key: str) -> float | None:
    value = region.observations.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _valid_loudness(region: SemanticRegion, key: str) -> float | None:
    value = _summary_float(region, key)
    if value is None or not math.isfinite(value) or value <= -70.0 or value > 0.0:
        return None
    return value


def _clipping_probability(region: SemanticRegion) -> float:
    values = tuple(
        value
        for key in ("clipping_probability", "clipping_probability_max")
        if (value := _summary_float(region, key)) is not None and math.isfinite(value)
    )
    return max(values, default=0.0)


def _maximum_dynamics(
    gains: tuple[float, ...],
    durations_us: tuple[int, ...],
) -> tuple[float, float]:
    if len(gains) <= 1:
        return 0.0, 0.0
    slopes: list[float] = []
    for previous, current, duration_us in zip(gains, gains[1:], durations_us, strict=False):
        duration_seconds = max(duration_us / 1_000_000, 1e-9)
        slopes.append((current - previous) / duration_seconds)
    accelerations: list[float] = []
    for index, (previous, current) in enumerate(pairwise(slopes)):
        previous_seconds = max(durations_us[index] / 1_000_000, 1e-9)
        current_seconds = max(durations_us[index + 1] / 1_000_000, 1e-9)
        accelerations.append((current - previous) / ((previous_seconds + current_seconds) / 2.0))
    return (
        max((abs(value) for value in slopes), default=0.0),
        max((abs(value) for value in accelerations), default=0.0),
    )


def _weighted_quantile(values: list[float], weights: list[float], quantile: float) -> float:
    if not values or len(values) != len(weights):
        raise ValueError("weighted quantile requires equally sized non-empty values and weights")
    if not 0.0 <= quantile <= 1.0 or any(weight <= 0 for weight in weights):
        raise ValueError("weighted quantile requires positive weights and quantile within [0, 1]")
    ordered = sorted(zip(values, weights, strict=True), key=lambda item: item[0])
    total = sum(weight for _, weight in ordered)
    positions: list[float] = []
    cumulative = 0.0
    for _, weight in ordered:
        positions.append((cumulative + weight / 2.0) / total)
        cumulative += weight
    if quantile <= positions[0]:
        return ordered[0][0]
    if quantile >= positions[-1]:
        return ordered[-1][0]
    for index in range(1, len(ordered)):
        if quantile <= positions[index]:
            lower_position = positions[index - 1]
            upper_position = positions[index]
            fraction = (quantile - lower_position) / (upper_position - lower_position)
            return ordered[index - 1][0] + fraction * (ordered[index][0] - ordered[index - 1][0])
    return ordered[-1][0]


def _true_runs(mask: tuple[bool, ...]) -> tuple[tuple[int, int], ...]:
    runs: list[tuple[int, int]] = []
    start: int | None = None
    for index, value in enumerate((*mask, False)):
        if value and start is None:
            start = index
        elif not value and start is not None:
            runs.append((start, index))
            start = None
    return tuple(runs)


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return min(maximum, max(minimum, value))


def _closest_to_zero(target: float, first: float, second: float) -> float:
    if target > 0.0:
        return max(0.0, min(target, first, second))
    if target < 0.0:
        return min(0.0, max(target, first, second))
    return 0.0


def _project_global_dynamics(
    values: list[float],
    *,
    regions: tuple[SemanticRegion, ...],
    eligible_mask: tuple[bool, ...],
    max_slope: float,
    max_acceleration: float,
) -> list[float]:
    if len(values) <= 1:
        return values.copy()
    projected = values.copy()
    targets = values.copy()
    modifiable = [
        eligible and not (index > 0 and not eligible_mask[index - 1]) for index, eligible in enumerate(eligible_mask)
    ]
    for index, can_change in enumerate(modifiable):
        if not can_change:
            projected[index] = 0.0
    durations = [max((region.end_us - region.start_us) / 1_000_000, 1e-9) for region in regions]

    for _ in range(48):
        for pair_index in (*range(len(projected) - 1), *range(len(projected) - 2, -1, -1)):
            _project_constraint(
                projected,
                coefficients=(-1.0, 1.0),
                indices=(pair_index, pair_index + 1),
                modifiable=modifiable,
                limit=max_slope * durations[pair_index],
            )
        for center in (*range(1, len(projected) - 1), *range(len(projected) - 2, 0, -1)):
            before_duration = durations[center - 1]
            after_duration = durations[center]
            acceleration_window = (before_duration + after_duration) / 2.0
            _project_constraint(
                projected,
                coefficients=(
                    1.0 / before_duration,
                    -(1.0 / before_duration + 1.0 / after_duration),
                    1.0 / after_duration,
                ),
                indices=(center - 1, center, center + 1),
                modifiable=modifiable,
                limit=max_acceleration * acceleration_window,
            )
        for index, target in enumerate(targets):
            projected[index] = _clamp(projected[index], min(0.0, target), max(0.0, target))
            if not modifiable[index]:
                projected[index] = 0.0
        observed_slope, observed_acceleration = _maximum_dynamics(
            tuple(projected),
            tuple(region.end_us - region.start_us for region in regions),
        )
        if observed_slope <= max_slope + 1e-9 and observed_acceleration <= max_acceleration + 1e-9:
            break

    observed_slope, observed_acceleration = _maximum_dynamics(
        tuple(projected),
        tuple(region.end_us - region.start_us for region in regions),
    )
    scale = min(
        1.0,
        max_slope / observed_slope if observed_slope > 0.0 else 1.0,
        max_acceleration / observed_acceleration if observed_acceleration > 0.0 else 1.0,
    )
    if scale < 1.0:
        projected = [
            value * scale if can_change else 0.0 for value, can_change in zip(projected, modifiable, strict=True)
        ]
    return projected


def _project_constraint(
    values: list[float],
    *,
    coefficients: tuple[float, ...],
    indices: tuple[int, ...],
    modifiable: list[bool],
    limit: float,
) -> None:
    measurement = sum(coefficient * values[index] for coefficient, index in zip(coefficients, indices, strict=True))
    if abs(measurement) <= limit:
        return
    movable = tuple(
        (coefficient, index) for coefficient, index in zip(coefficients, indices, strict=True) if modifiable[index]
    )
    denominator = sum(coefficient * coefficient for coefficient, _ in movable)
    if denominator <= 0.0:
        return
    excess = measurement - math.copysign(limit, measurement)
    for coefficient, index in movable:
        values[index] -= excess * coefficient / denominator
