from __future__ import annotations

import math
import sys
import wave
from array import array
from collections.abc import Callable
from pathlib import Path

SampleFunction = Callable[[int, int], float]


def generate_spoken_word_fixture(
    path: Path,
    *,
    duration_seconds: float = 6.0,
    sample_rate_hz: int = 48_000,
) -> Path:
    """Generate deterministic voice-shaped PCM without recorded or copied media."""

    if duration_seconds < 1.0:
        raise ValueError("duration_seconds must be at least one second")

    def sample_at(frame_index: int, _channel: int) -> float:
        normalized = frame_index / round(duration_seconds * sample_rate_hz)
        if normalized < 0.05 or normalized >= 0.96:
            return 0.0
        if normalized < 0.40:
            amplitude = 0.10
        elif normalized < 0.47:
            amplitude = 0.003
        else:
            amplitude = 0.32
        return amplitude * synthetic_voice_sample(frame_index, sample_rate_hz, speaker_index=0)

    return write_pcm16_fixture(
        path,
        duration_seconds=duration_seconds,
        sample_rate_hz=sample_rate_hz,
        channels=1,
        sample_at=sample_at,
    )


def write_pcm16_fixture(
    path: Path,
    *,
    duration_seconds: float,
    sample_rate_hz: int,
    channels: int,
    sample_at: SampleFunction,
    chunk_frames: int = 4_096,
) -> Path:
    """Stream deterministic PCM16 WAV frames to a new file."""

    _validate_output(path, duration_seconds, sample_rate_hz, channels)
    if chunk_frames <= 0:
        raise ValueError("chunk_frames must be positive")
    frame_count = round(duration_seconds * sample_rate_hz)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with wave.open(str(path), "wb") as output:
            output.setnchannels(channels)
            output.setsampwidth(2)
            output.setframerate(sample_rate_hz)
            for chunk_start in range(0, frame_count, chunk_frames):
                chunk_end = min(frame_count, chunk_start + chunk_frames)
                samples = array("h")
                for frame_index in range(chunk_start, chunk_end):
                    for channel in range(channels):
                        samples.append(_pcm16(sample_at(frame_index, channel)))
                if sys.byteorder != "little":
                    samples.byteswap()
                output.writeframesraw(samples.tobytes())
            output.writeframes(b"")
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return path


def write_repeating_pcm16_fixture(
    path: Path,
    *,
    duration_seconds: float,
    sample_rate_hz: int,
    channels: int,
    block_duration_seconds: float,
    sample_at: SampleFunction,
) -> Path:
    """Write a bounded-memory long-form fixture by repeating a deterministic block."""

    _validate_output(path, duration_seconds, sample_rate_hz, channels)
    if block_duration_seconds <= 0 or block_duration_seconds > duration_seconds:
        raise ValueError("block_duration_seconds must be positive and no longer than the fixture")
    total_frames = round(duration_seconds * sample_rate_hz)
    block_frames = round(block_duration_seconds * sample_rate_hz)
    block = _pcm16_bytes(block_frames, channels, sample_at)
    full_blocks, remaining_frames = divmod(total_frames, block_frames)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with wave.open(str(path), "wb") as output:
            output.setnchannels(channels)
            output.setsampwidth(2)
            output.setframerate(sample_rate_hz)
            for _ in range(full_blocks):
                output.writeframesraw(block)
            if remaining_frames:
                frame_bytes = channels * 2
                output.writeframesraw(block[: remaining_frames * frame_bytes])
            output.writeframes(b"")
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return path


def synthetic_voice_sample(
    frame_index: int,
    sample_rate_hz: int,
    *,
    speaker_index: int,
    syllable_hz: float = 3.1,
) -> float:
    """Return a voice-shaped mathematical control signal with no linguistic content."""

    time_seconds = frame_index / sample_rate_hz
    base_frequency = 122.0 + speaker_index * 71.0
    fundamental = base_frequency + 9.0 * math.sin(2.0 * math.pi * 0.41 * time_seconds + speaker_index)
    syllabic = 0.18 + 0.82 * max(0.0, math.sin(2.0 * math.pi * syllable_hz * time_seconds)) ** 0.8
    voice = (
        0.62 * math.sin(2.0 * math.pi * fundamental * time_seconds)
        + 0.24 * math.sin(2.0 * math.pi * fundamental * 2.01 * time_seconds + 0.37)
        + 0.10 * math.sin(2.0 * math.pi * fundamental * 3.91 * time_seconds + 1.13)
        + 0.04 * math.sin(2.0 * math.pi * fundamental * 6.17 * time_seconds + 0.73)
    )
    breath = deterministic_noise_sample(frame_index, seed=11_003 + speaker_index * 977) * 0.08
    return _clamp(syllabic * voice + (1.0 - syllabic) * breath)


def deterministic_noise_sample(frame_index: int, *, seed: int) -> float:
    """Return stable pseudo-noise derived only from integer arithmetic."""

    value = (frame_index + seed * 0x9E3779B1) & 0xFFFFFFFF
    value ^= value >> 16
    value = (value * 0x7FEB352D) & 0xFFFFFFFF
    value ^= value >> 15
    value = (value * 0x846CA68B) & 0xFFFFFFFF
    value ^= value >> 16
    return ((value & 0xFFFF) / 32_767.5) - 1.0


def harmonic_music_control(frame_index: int, sample_rate_hz: int) -> float:
    """Return an original chord-like control signal, not a copied composition."""

    time_seconds = frame_index / sample_rate_hz
    pulse = 0.55 + 0.45 * math.sin(2.0 * math.pi * 0.5 * time_seconds) ** 2
    chord = (
        0.50 * math.sin(2.0 * math.pi * 196.0 * time_seconds)
        + 0.30 * math.sin(2.0 * math.pi * 246.94 * time_seconds + 0.2)
        + 0.20 * math.sin(2.0 * math.pi * 293.66 * time_seconds + 0.6)
    )
    return _clamp(pulse * chord)


def _pcm16_bytes(frame_count: int, channels: int, sample_at: SampleFunction) -> bytes:
    samples = array("h")
    for frame_index in range(frame_count):
        for channel in range(channels):
            samples.append(_pcm16(sample_at(frame_index, channel)))
    if sys.byteorder != "little":
        samples.byteswap()
    return samples.tobytes()


def _validate_output(path: Path, duration_seconds: float, sample_rate_hz: int, channels: int) -> None:
    if duration_seconds <= 0:
        raise ValueError("duration_seconds must be positive")
    if sample_rate_hz < 8_000 or sample_rate_hz > 192_000:
        raise ValueError("sample_rate_hz must be within [8000, 192000]")
    if channels < 1 or channels > 8:
        raise ValueError("channels must be within [1, 8]")
    if path.exists():
        raise FileExistsError(f"refusing to overwrite existing fixture: {path}")


def _pcm16(value: float) -> int:
    return round(_clamp(value) * 32_767.0)


def _clamp(value: float) -> float:
    return max(-1.0, min(1.0, value))
