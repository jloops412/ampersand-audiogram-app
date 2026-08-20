from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from typing import Literal

from ampersand_contracts import (
    EvidenceProvenance,
    ObservationKind,
    ProcessingEligibility,
    SemanticConflict,
    SemanticMap,
    SemanticObservation,
    SemanticRegion,
)

from .hashing import sha256_text, stable_id

_PROBABILITY_KINDS = {
    ObservationKind.SPEECH_PROBABILITY,
    ObservationKind.SILENCE_PROBABILITY,
    ObservationKind.MUSIC_PROBABILITY,
    ObservationKind.AMBIENCE_PROBABILITY,
    ObservationKind.NOISE_PROBABILITY,
    ObservationKind.OVERLAP_PROBABILITY,
    ObservationKind.CLIPPING_PROBABILITY,
    ObservationKind.RUMBLE_PROBABILITY,
    ObservationKind.HUM_PROBABILITY,
    ObservationKind.REVERB_PROBABILITY,
    ObservationKind.BANDWIDTH_LIMIT_PROBABILITY,
}
type ContentLabel = Literal["unknown", "speech", "silence", "music", "ambience", "noise", "mixed"]


def fuse_semantic_map(
    *,
    semantic_map_id: str,
    source_asset_id: str,
    duration_us: int,
    observations: Iterable[SemanticObservation],
    provenance_sources: Sequence[EvidenceProvenance] = (),
    provider_native_artifact_ids: Sequence[str] = (),
    unavailable_adapters: Sequence[str] = (),
    warnings: Sequence[str] = (),
    analysis_hop_us: int = 100_000,
) -> SemanticMap:
    """Fuse provider-normalized evidence without erasing overlap or disagreement."""

    if duration_us <= 0 or analysis_hop_us <= 0:
        raise ValueError("duration_us and analysis_hop_us must be positive")
    ordered = tuple(
        sorted(
            observations,
            key=lambda observation: (
                observation.start_us,
                observation.end_us,
                observation.kind.value,
                observation.observation_id,
            ),
        )
    )
    for observation in ordered:
        if observation.end_us > duration_us:
            raise ValueError(f"observation {observation.observation_id} exceeds the requested duration")
    provenance_by_id = {provenance.provenance_id: provenance for provenance in provenance_sources}

    regions: list[SemanticRegion] = []
    conflicts: list[SemanticConflict] = []
    next_observation = 0
    active: list[SemanticObservation] = []

    for start_us in range(0, duration_us, analysis_hop_us):
        end_us = min(duration_us, start_us + analysis_hop_us)
        active = [observation for observation in active if observation.end_us > start_us]
        while next_observation < len(ordered) and ordered[next_observation].start_us < end_us:
            candidate = ordered[next_observation]
            next_observation += 1
            if candidate.end_us > start_us:
                active.append(candidate)
        overlapping = tuple(
            sorted(
                (observation for observation in active if observation.start_us < end_us),
                key=lambda observation: (observation.kind.value, observation.observation_id),
            )
        )
        region_conflicts = _detect_conflicts(
            start_us=start_us,
            end_us=end_us,
            observations=overlapping,
            id_seed=semantic_map_id,
        )
        conflicts.extend(region_conflicts)
        regions.append(
            _fuse_region(
                semantic_map_id=semantic_map_id,
                start_us=start_us,
                end_us=end_us,
                observations=overlapping,
                conflicts=region_conflicts,
                provenance_by_id=provenance_by_id,
            )
        )

    return SemanticMap(
        semantic_map_id=semantic_map_id,
        source_asset_id=source_asset_id,
        duration_us=duration_us,
        analysis_hop_us=analysis_hop_us,
        regions=tuple(regions),
        provenance_sources=tuple(sorted(provenance_sources, key=lambda provenance: provenance.provenance_id)),
        observations=ordered,
        conflicts=tuple(conflicts),
        provider_native_artifact_ids=tuple(sorted(set(provider_native_artifact_ids))),
        unavailable_adapters=tuple(sorted(set(unavailable_adapters))),
        warnings=tuple(warnings),
    )


def _fuse_region(
    *,
    semantic_map_id: str,
    start_us: int,
    end_us: int,
    observations: tuple[SemanticObservation, ...],
    conflicts: tuple[SemanticConflict, ...],
    provenance_by_id: dict[str, EvidenceProvenance],
) -> SemanticRegion:
    grouped: dict[ObservationKind, list[SemanticObservation]] = defaultdict(list)
    for observation in observations:
        grouped[observation.kind].append(observation)

    probabilities = {kind: _weighted_probability(grouped[kind]) for kind in _PROBABILITY_KINDS}
    speech = probabilities[ObservationKind.SPEECH_PROBABILITY]
    silence = probabilities[ObservationKind.SILENCE_PROBABILITY]
    music = probabilities[ObservationKind.MUSIC_PROBABILITY]
    ambience = probabilities[ObservationKind.AMBIENCE_PROBABILITY]
    noise = probabilities[ObservationKind.NOISE_PROBABILITY]
    overlap = probabilities[ObservationKind.OVERLAP_PROBABILITY]

    label, confidence, eligibility = _classify_region(
        speech=speech,
        silence=silence,
        music=music,
        ambience=ambience,
        noise=noise,
        conflicts=conflicts,
    )
    speakers = grouped[ObservationKind.ACTIVE_SPEAKER]
    active_speaker, active_speaker_confidence = _select_speaker(speakers, conflicts)
    summary = _build_summary(grouped)
    identity = f"{semantic_map_id}|{start_us}|{end_us}"
    return SemanticRegion(
        region_id=stable_id("semantic-region", sha256_text(identity), length=24),
        start_us=start_us,
        end_us=end_us,
        content_label=label,
        confidence=round(confidence, 6),
        speech_probability=_rounded(speech),
        silence_probability=_rounded(silence),
        music_probability=_rounded(music),
        ambience_probability=_rounded(ambience),
        noise_probability=_rounded(noise),
        overlap_probability=_rounded(overlap),
        active_speaker=active_speaker,
        active_speaker_confidence=_rounded(active_speaker_confidence),
        protected=eligibility is not ProcessingEligibility.ELIGIBLE,
        processing_eligibility=eligibility,
        observations=summary,
        observation_ids=tuple(observation.observation_id for observation in observations),
        conflict_ids=tuple(conflict.conflict_id for conflict in conflicts),
        provider_refs=tuple(
            sorted(
                {
                    provenance_by_id[observation.provenance_ref].provider_id
                    for observation in observations
                    if observation.provenance_ref in provenance_by_id
                }
            )
        ),
    )


def _classify_region(
    *,
    speech: float | None,
    silence: float | None,
    music: float | None,
    ambience: float | None,
    noise: float | None,
    conflicts: tuple[SemanticConflict, ...],
) -> tuple[ContentLabel, float, ProcessingEligibility]:
    if conflicts:
        return "mixed", max(conflict.severity for conflict in conflicts), ProcessingEligibility.PROTECT
    if music is not None and music >= 0.65:
        return "music", music, ProcessingEligibility.PROTECT
    if speech is not None and speech >= 0.62 and (silence is None or silence < 0.55):
        return "speech", speech, ProcessingEligibility.ELIGIBLE
    if silence is not None and silence >= 0.80 and (speech is None or speech < 0.45):
        return "silence", silence, ProcessingEligibility.NO_OP
    if noise is not None and noise >= 0.70:
        return "noise", noise, ProcessingEligibility.PROTECT
    if ambience is not None and ambience >= 0.70:
        return "ambience", ambience, ProcessingEligibility.PROTECT
    evidence = [value for value in (speech, silence, music, ambience, noise) if value is not None]
    return "unknown", max(evidence, default=0.0), ProcessingEligibility.PROTECT


def _weighted_probability(observations: Sequence[SemanticObservation]) -> float | None:
    if not observations:
        return None
    numerator = 0.0
    denominator = 0.0
    for observation in observations:
        if isinstance(observation.value, bool) or not isinstance(observation.value, (int, float)):
            continue
        weight = max(float(observation.confidence), 1e-9)
        numerator += float(observation.value) * weight
        denominator += weight
    return numerator / denominator if denominator else None


def _select_speaker(
    observations: Sequence[SemanticObservation],
    conflicts: Sequence[SemanticConflict],
) -> tuple[str | None, float | None]:
    if not observations or any(ObservationKind.ACTIVE_SPEAKER in conflict.kinds for conflict in conflicts):
        return None, None
    candidate = max(observations, key=lambda observation: (observation.confidence, observation.observation_id))
    return (str(candidate.value), float(candidate.confidence)) if candidate.value is not None else (None, None)


def _build_summary(
    grouped: dict[ObservationKind, list[SemanticObservation]],
) -> dict[str, str | int | float | bool | None]:
    summary: dict[str, str | int | float | bool | None] = {
        "evidence_count": sum(len(values) for values in grouped.values()),
    }
    measurement_rules = {
        ObservationKind.MOMENTARY_LOUDNESS: ("momentary_lufs", "mean"),
        ObservationKind.SHORT_TERM_LOUDNESS: ("short_term_lufs", "mean"),
        ObservationKind.SAMPLE_PEAK: ("sample_peak_dbfs", "max"),
        ObservationKind.TRUE_PEAK: ("true_peak_dbtp", "max"),
    }
    for kind, (key, rule) in measurement_rules.items():
        values = [
            float(observation.value)
            for observation in grouped[kind]
            if isinstance(observation.value, (int, float)) and not isinstance(observation.value, bool)
        ]
        if values:
            summary[key] = round(max(values) if rule == "max" else sum(values) / len(values), 6)
    for kind in _PROBABILITY_KINDS:
        values = [
            float(observation.value)
            for observation in grouped[kind]
            if isinstance(observation.value, (int, float)) and not isinstance(observation.value, bool)
        ]
        if len(values) > 1:
            summary[f"{kind.value}_min"] = round(min(values), 6)
            summary[f"{kind.value}_max"] = round(max(values), 6)
    return summary


def _detect_conflicts(
    *,
    start_us: int,
    end_us: int,
    observations: tuple[SemanticObservation, ...],
    id_seed: str,
) -> tuple[SemanticConflict, ...]:
    grouped: dict[ObservationKind, list[SemanticObservation]] = defaultdict(list)
    for observation in observations:
        grouped[observation.kind].append(observation)
    conflicts: list[SemanticConflict] = []

    for kind in sorted(_PROBABILITY_KINDS, key=lambda value: value.value):
        reliable = [
            observation
            for observation in grouped[kind]
            if observation.confidence >= 0.5
            and isinstance(observation.value, (int, float))
            and not isinstance(observation.value, bool)
        ]
        if len(reliable) < 2:
            continue
        values = [_numeric_value(observation) for observation in reliable]
        spread = max(values) - min(values)
        if spread >= 0.55:
            conflicts.append(
                _conflict(
                    start_us=start_us,
                    end_us=end_us,
                    observations=reliable,
                    severity=min(1.0, spread),
                    reason=f"Reliable {kind.value} providers disagree by {spread:.2f}.",
                    id_seed=id_seed,
                )
            )

    mutually_exclusive = (
        (ObservationKind.SPEECH_PROBABILITY, ObservationKind.SILENCE_PROBABILITY, 0.65),
        (ObservationKind.SPEECH_PROBABILITY, ObservationKind.MUSIC_PROBABILITY, 0.60),
    )
    for first_kind, second_kind, threshold in mutually_exclusive:
        first = _high_probability_evidence(grouped[first_kind], threshold)
        second = _high_probability_evidence(grouped[second_kind], threshold)
        if first and second:
            values = [_numeric_value(observation) for observation in (*first, *second)]
            conflicts.append(
                _conflict(
                    start_us=start_us,
                    end_us=end_us,
                    observations=(*first, *second),
                    severity=min(values),
                    reason=f"High-confidence {first_kind.value} and {second_kind.value} evidence overlap.",
                    id_seed=id_seed,
                )
            )

    speakers = [
        observation
        for observation in grouped[ObservationKind.ACTIVE_SPEAKER]
        if observation.confidence >= 0.65 and isinstance(observation.value, str)
    ]
    if len({str(observation.value) for observation in speakers}) > 1:
        conflicts.append(
            _conflict(
                start_us=start_us,
                end_us=end_us,
                observations=speakers,
                severity=min(float(observation.confidence) for observation in speakers),
                reason="Multiple reliable active-speaker labels overlap.",
                id_seed=id_seed,
            )
        )
    return tuple(sorted(conflicts, key=lambda conflict: conflict.conflict_id))


def _high_probability_evidence(
    observations: Sequence[SemanticObservation], threshold: float
) -> tuple[SemanticObservation, ...]:
    return tuple(
        observation
        for observation in observations
        if observation.confidence >= 0.5
        and isinstance(observation.value, (int, float))
        and not isinstance(observation.value, bool)
        and float(observation.value) >= threshold
    )


def _conflict(
    *,
    start_us: int,
    end_us: int,
    observations: Sequence[SemanticObservation],
    severity: float,
    reason: str,
    id_seed: str,
) -> SemanticConflict:
    observation_ids = tuple(sorted({observation.observation_id for observation in observations}))
    kinds = tuple(sorted({observation.kind for observation in observations}, key=lambda kind: kind.value))
    identity = f"{id_seed}|{start_us}|{end_us}|{'|'.join(observation_ids)}"
    return SemanticConflict(
        conflict_id=stable_id("semantic-conflict", sha256_text(identity), length=24),
        start_us=start_us,
        end_us=end_us,
        kinds=kinds,
        observation_ids=observation_ids,
        severity=round(severity, 6),
        reason=reason,
    )


def _rounded(value: float | None) -> float | None:
    return round(value, 6) if value is not None else None


def _numeric_value(observation: SemanticObservation) -> float:
    value = observation.value
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"observation {observation.observation_id} does not contain a numeric value")
    return float(value)
