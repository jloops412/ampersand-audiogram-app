from __future__ import annotations

from collections.abc import Iterable

from ampersand_contracts import (
    EvidenceProvenance,
    ObservationKind,
    ObservationUnit,
    SemanticObservation,
)

from .hashing import sha256_text, stable_id
from .semantic_types import LoudnessFrame, SpeakerSegment, TranscriptSegment, VadFrame


def normalize_loudness_frames(
    frames: Iterable[LoudnessFrame],
    *,
    provenance: EvidenceProvenance,
    id_seed: str,
) -> tuple[SemanticObservation, ...]:
    observations: list[SemanticObservation] = []
    for frame in frames:
        observations.extend(
            (
                _observation(
                    kind=ObservationKind.MOMENTARY_LOUDNESS,
                    unit=ObservationUnit.LUFS,
                    value=frame.momentary_lufs,
                    confidence=1.0,
                    start_us=frame.start_us,
                    end_us=frame.end_us,
                    provenance=provenance,
                    id_seed=id_seed,
                    attributes={"measurement_window_us": 400_000},
                ),
                _observation(
                    kind=ObservationKind.SHORT_TERM_LOUDNESS,
                    unit=ObservationUnit.LUFS,
                    value=frame.short_term_lufs,
                    confidence=1.0,
                    start_us=frame.start_us,
                    end_us=frame.end_us,
                    provenance=provenance,
                    id_seed=id_seed,
                    attributes={"measurement_window_us": 3_000_000},
                ),
                _observation(
                    kind=ObservationKind.TRUE_PEAK,
                    unit=ObservationUnit.DBTP,
                    value=frame.true_peak_dbtp,
                    confidence=1.0,
                    start_us=frame.start_us,
                    end_us=frame.end_us,
                    provenance=provenance,
                    id_seed=id_seed,
                    attributes={"below_measurement_floor": frame.below_true_peak_floor},
                ),
            )
        )
    return _stable_observation_order(observations)


def normalize_vad_frames(
    frames: Iterable[VadFrame],
    *,
    provenance: EvidenceProvenance,
    id_seed: str,
) -> tuple[SemanticObservation, ...]:
    observations: list[SemanticObservation] = []
    for frame in frames:
        observations.extend(
            (
                _observation(
                    kind=ObservationKind.SPEECH_PROBABILITY,
                    unit=ObservationUnit.PROBABILITY,
                    value=frame.speech_probability,
                    confidence=frame.confidence,
                    start_us=frame.start_us,
                    end_us=frame.end_us,
                    provenance=provenance,
                    id_seed=id_seed,
                    attributes=_vad_summary_attributes(frame),
                ),
                _observation(
                    kind=ObservationKind.SILENCE_PROBABILITY,
                    unit=ObservationUnit.PROBABILITY,
                    value=frame.silence_probability,
                    confidence=frame.confidence,
                    start_us=frame.start_us,
                    end_us=frame.end_us,
                    provenance=provenance,
                    id_seed=id_seed,
                    attributes={"derived_from": "energy_activity_complement"},
                ),
                _observation(
                    kind=ObservationKind.SAMPLE_PEAK,
                    unit=ObservationUnit.DBFS,
                    value=frame.sample_peak_dbfs,
                    confidence=1.0,
                    start_us=frame.start_us,
                    end_us=frame.end_us,
                    provenance=provenance,
                    id_seed=id_seed,
                    attributes={"measurement_window_us": frame.end_us - frame.start_us},
                ),
            )
        )
    return _stable_observation_order(observations)


def normalize_transcript_segments(
    segments: Iterable[TranscriptSegment],
    *,
    provenance: EvidenceProvenance,
    id_seed: str,
) -> tuple[SemanticObservation, ...]:
    return _stable_observation_order(
        _observation(
            kind=ObservationKind.TRANSCRIPT_SEGMENT,
            unit=ObservationUnit.TEXT,
            value=segment.text,
            confidence=segment.confidence,
            start_us=segment.start_us,
            end_us=segment.end_us,
            provenance=provenance,
            id_seed=id_seed,
            attributes={"language": segment.language},
        )
        for segment in segments
    )


def normalize_speaker_segments(
    segments: Iterable[SpeakerSegment],
    *,
    provenance: EvidenceProvenance,
    id_seed: str,
) -> tuple[SemanticObservation, ...]:
    observations: list[SemanticObservation] = []
    for segment in segments:
        observations.append(
            _observation(
                kind=ObservationKind.ACTIVE_SPEAKER,
                unit=ObservationUnit.LABEL,
                value=segment.speaker_label,
                confidence=segment.confidence,
                start_us=segment.start_us,
                end_us=segment.end_us,
                provenance=provenance,
                id_seed=id_seed,
            )
        )
        if segment.overlap_probability is not None:
            observations.append(
                _observation(
                    kind=ObservationKind.OVERLAP_PROBABILITY,
                    unit=ObservationUnit.PROBABILITY,
                    value=segment.overlap_probability,
                    confidence=segment.confidence,
                    start_us=segment.start_us,
                    end_us=segment.end_us,
                    provenance=provenance,
                    id_seed=id_seed,
                )
            )
    return _stable_observation_order(observations)


def _observation(
    *,
    kind: ObservationKind,
    unit: ObservationUnit,
    value: str | int | float | bool | None,
    confidence: float,
    start_us: int,
    end_us: int,
    provenance: EvidenceProvenance,
    id_seed: str,
    attributes: dict[str, str | int | float | bool | None] | None = None,
) -> SemanticObservation:
    identity = "|".join(
        (
            id_seed,
            provenance.provider_id,
            provenance.provider_version,
            kind.value,
            str(start_us),
            str(end_us),
            repr(value),
        )
    )
    return SemanticObservation(
        observation_id=stable_id("observation", sha256_text(identity), length=24),
        kind=kind,
        start_us=start_us,
        end_us=end_us,
        confidence=confidence,
        value=value,
        unit=unit,
        provenance_ref=provenance.provenance_id,
        attributes=attributes or {},
    )


def _stable_observation_order(
    observations: Iterable[SemanticObservation],
) -> tuple[SemanticObservation, ...]:
    return tuple(
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


def _vad_summary_attributes(frame: VadFrame) -> dict[str, str | int | float | bool | None]:
    """Keep only routing-relevant flags; detailed numeric features remain in the native artifact."""

    retained_keys = ("detector_class", "active_state")
    return {key: frame.attributes[key] for key in retained_keys if key in frame.attributes}
