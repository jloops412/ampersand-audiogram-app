from __future__ import annotations

from dataclasses import dataclass

type JsonValue = str | int | float | bool | list[JsonValue] | dict[str, JsonValue] | None


@dataclass(frozen=True)
class LoudnessFrame:
    start_us: int
    end_us: int
    momentary_lufs: float
    short_term_lufs: float
    true_peak_dbtp: float
    below_true_peak_floor: bool = False


@dataclass(frozen=True)
class VadFrame:
    start_us: int
    end_us: int
    speech_probability: float
    silence_probability: float
    confidence: float
    sample_peak_dbfs: float
    rms_dbfs: float
    attributes: dict[str, str | int | float | bool | None]


@dataclass(frozen=True)
class TranscriptSegment:
    start_us: int
    end_us: int
    text: str
    confidence: float
    language: str | None = None


@dataclass(frozen=True)
class SpeakerSegment:
    start_us: int
    end_us: int
    speaker_label: str
    confidence: float
    overlap_probability: float | None = None


@dataclass(frozen=True)
class LoudnessTimelineResult:
    frames: tuple[LoudnessFrame, ...]
    provider_payload: dict[str, JsonValue]


@dataclass(frozen=True)
class VadAnalysisResult:
    frames: tuple[VadFrame, ...]
    provider_payload: dict[str, JsonValue]
