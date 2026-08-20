from __future__ import annotations

import math
import subprocess
from pathlib import Path

import numpy as np
import numpy.typing as npt

from .errors import EngineError
from .ffmpeg import FFmpegTools, decode_float32_command, subprocess_environment
from .semantic_types import JsonValue, VadAnalysisResult, VadFrame

FloatArray = npt.NDArray[np.float32]


def analyze_energy_vad(
    source: Path,
    *,
    duration_us: int,
    tools: FFmpegTools,
    sample_rate_hz: int = 16_000,
    hop_us: int = 100_000,
) -> VadAnalysisResult:
    """Run Ampersand's conservative, first-party energy/spectral VAD baseline.

    The baseline is intentionally confidence-bounded. It supplies useful local speech
    probabilities before a checkpoint-backed VAD is admitted, but it never claims to
    distinguish speech from music reliably enough to make destructive decisions.
    """

    if duration_us <= 0:
        raise ValueError("duration_us must be positive")
    samples_per_frame_numerator = sample_rate_hz * hop_us
    if samples_per_frame_numerator % 1_000_000:
        raise ValueError("sample_rate_hz and hop_us must produce an integer frame size")
    samples_per_frame = samples_per_frame_numerator // 1_000_000
    if samples_per_frame < 256:
        raise ValueError("VAD frames must contain at least 256 samples")

    command = decode_float32_command(source, tools, sample_rate_hz=sample_rate_hz, channels=1)
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=subprocess_environment(),
    )
    if process.stdout is None or process.stderr is None:
        raise EngineError("Could not open the VAD decoder pipes.")

    feature_rows: list[tuple[float, float, float, float, float, float]] = []
    pending = np.empty(0, dtype=np.float32)
    byte_tail = b""
    window = np.hanning(samples_per_frame).astype(np.float64)
    frequencies = np.fft.rfftfreq(samples_per_frame, d=1.0 / sample_rate_hz)

    while chunk := process.stdout.read(4 * 1024 * 1024):
        payload = byte_tail + chunk
        complete_size = len(payload) - (len(payload) % 4)
        complete, byte_tail = payload[:complete_size], payload[complete_size:]
        if not complete:
            continue
        decoded = np.frombuffer(complete, dtype="<f4")
        samples = np.concatenate((pending, decoded)) if pending.size else decoded
        frame_count = samples.size // samples_per_frame
        if frame_count:
            frames = samples[: frame_count * samples_per_frame].reshape((frame_count, samples_per_frame))
            feature_rows.extend(_extract_features(frames, window=window, frequencies=frequencies))
        pending = samples[frame_count * samples_per_frame :].copy()

    stderr = process.stderr.read().decode("utf-8", errors="replace")
    return_code = process.wait()
    if return_code != 0:
        detail = next((line.strip() for line in reversed(stderr.splitlines()) if line.strip()), "")
        raise EngineError(f"ffmpeg failed to decode VAD samples: {detail}".rstrip())
    if byte_tail:
        raise EngineError("Decoded VAD PCM ended with an incomplete float32 sample.")
    if pending.size:
        padded = np.pad(pending, (0, samples_per_frame - pending.size)).reshape((1, samples_per_frame))
        feature_rows.extend(_extract_features(padded, window=window, frequencies=frequencies))

    expected_frames = (duration_us + hop_us - 1) // hop_us
    if len(feature_rows) < expected_frames:
        raise EngineError(
            f"VAD decoder returned {len(feature_rows)} frames; {expected_frames} are required for full coverage."
        )
    feature_rows = feature_rows[:expected_frames]
    if not feature_rows:
        raise EngineError("The source produced no VAD analysis frames.")

    rms_values = np.asarray([row[0] for row in feature_rows], dtype=np.float64)
    estimated_floor = float(np.percentile(rms_values, 20.0))
    noise_floor_dbfs = min(-45.0, max(-90.0, estimated_floor))
    activity_threshold_dbfs = max(-55.0, noise_floor_dbfs + 9.0)

    raw_speech: list[float] = []
    activities: list[float] = []
    for rms_dbfs, _peak_dbfs, band_ratio, rumble_ratio, flatness, zero_crossing_rate in feature_rows:
        activity = _sigmoid((rms_dbfs - activity_threshold_dbfs) / 4.0)
        band_score = _clamp((band_ratio - 0.30) / 0.65)
        tonal_score = _clamp((0.60 - flatness) / 0.58)
        likeness = 0.52 + 0.31 * band_score + 0.17 * tonal_score
        if rumble_ratio > 0.55:
            likeness *= 0.70
        if zero_crossing_rate > 0.36:
            likeness *= 0.78
        raw_speech.append(_clamp(activity * likeness, maximum=0.88))
        activities.append(activity)

    smoothed_speech = _smooth_probabilities(raw_speech)
    vad_frames: list[VadFrame] = []
    raw_frames: list[JsonValue] = []
    active_state = False
    for index, (features, speech_probability, activity) in enumerate(
        zip(feature_rows, smoothed_speech, activities, strict=True)
    ):
        rms_dbfs, sample_peak_dbfs, band_ratio, rumble_ratio, flatness, zero_crossing_rate = features
        if speech_probability >= 0.58:
            active_state = True
        elif speech_probability <= 0.32:
            active_state = False
        silence_probability = _clamp((1.0 - activity) * 0.98)
        confidence = _clamp(0.55 + 0.40 * abs(activity - 0.5) * 2.0, maximum=0.95)
        start_us = index * hop_us
        end_us = min(duration_us, start_us + hop_us)
        attributes: dict[str, str | int | float | bool | None] = {
            "detector_class": "first_party_deterministic_energy_spectral_vad",
            "active_state": active_state,
            "rms_dbfs": round(rms_dbfs, 6),
            "speech_band_ratio": round(band_ratio, 6),
            "rumble_ratio": round(rumble_ratio, 6),
            "spectral_flatness": round(flatness, 6),
            "zero_crossing_rate": round(zero_crossing_rate, 6),
        }
        vad_frames.append(
            VadFrame(
                start_us=start_us,
                end_us=end_us,
                speech_probability=round(speech_probability, 6),
                silence_probability=round(silence_probability, 6),
                confidence=round(confidence, 6),
                sample_peak_dbfs=round(sample_peak_dbfs, 6),
                rms_dbfs=round(rms_dbfs, 6),
                attributes=attributes,
            )
        )
        raw_frames.append(
            {
                "start_us": start_us,
                "end_us": end_us,
                "speech_probability": round(speech_probability, 6),
                "silence_probability": round(silence_probability, 6),
                "confidence": round(confidence, 6),
                "sample_peak_dbfs": round(sample_peak_dbfs, 6),
                **attributes,
            }
        )

    return VadAnalysisResult(
        frames=tuple(vad_frames),
        provider_payload={
            "provider": "ampersand-energy-vad",
            "provider_version": "0.1.0",
            "admission": "builtin_first_party_deterministic",
            "analysis_hop_us": hop_us,
            "analysis_sample_rate_hz": sample_rate_hz,
            "duration_us": duration_us,
            "estimated_noise_floor_dbfs": round(noise_floor_dbfs, 6),
            "activity_threshold_dbfs": round(activity_threshold_dbfs, 6),
            "limitations": (
                "Confidence-bounded bootstrap VAD; music/speech discrimination requires an admitted semantic provider."
            ),
            "frames": raw_frames,
        },
    )


def _extract_features(
    frames: FloatArray,
    *,
    window: npt.NDArray[np.float64],
    frequencies: npt.NDArray[np.float64],
) -> list[tuple[float, float, float, float, float, float]]:
    working = frames.astype(np.float64, copy=False)
    epsilon = 1e-12
    rms = np.sqrt(np.mean(np.square(working), axis=1) + epsilon)
    peak = np.max(np.abs(working), axis=1)
    rms_dbfs = 20.0 * np.log10(np.maximum(rms, 1e-6))
    peak_dbfs = 20.0 * np.log10(np.maximum(peak, 1e-6))

    spectrum_power = np.square(np.abs(np.fft.rfft(working * window, axis=1))) + epsilon
    total_power = np.sum(spectrum_power, axis=1)
    speech_mask = (frequencies >= 80.0) & (frequencies <= 4_000.0)
    rumble_mask = (frequencies >= 20.0) & (frequencies < 80.0)
    band_ratio = np.sum(spectrum_power[:, speech_mask], axis=1) / total_power
    rumble_ratio = np.sum(spectrum_power[:, rumble_mask], axis=1) / total_power
    non_dc = spectrum_power[:, 1:]
    flatness = np.exp(np.mean(np.log(non_dc), axis=1)) / np.mean(non_dc, axis=1)
    zero_crossing_rate = np.mean(np.signbit(working[:, 1:]) != np.signbit(working[:, :-1]), axis=1)

    stacked = np.stack(
        (rms_dbfs, peak_dbfs, band_ratio, rumble_ratio, flatness, zero_crossing_rate),
        axis=1,
    )
    return [
        (float(row[0]), float(row[1]), float(row[2]), float(row[3]), float(row[4]), float(row[5])) for row in stacked
    ]


def _smooth_probabilities(values: list[float]) -> list[float]:
    array = np.asarray(values, dtype=np.float64)
    if array.size == 1:
        return [float(array[0])]
    padded = np.pad(array, (1, 1), mode="edge")
    smoothed = 0.25 * padded[:-2] + 0.50 * padded[1:-1] + 0.25 * padded[2:]
    return [float(value) for value in smoothed]


def _sigmoid(value: float) -> float:
    if value >= 0:
        return 1.0 / (1.0 + math.exp(-value))
    exponent = math.exp(value)
    return exponent / (1.0 + exponent)


def _clamp(value: float, *, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return min(maximum, max(minimum, value))
