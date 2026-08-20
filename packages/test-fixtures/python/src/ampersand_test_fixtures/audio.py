from __future__ import annotations

import math
import sys
import wave
from array import array
from pathlib import Path


def generate_spoken_word_fixture(path: Path, *, duration_seconds: float = 6.0, sample_rate_hz: int = 48_000) -> Path:
    """Generate deterministic speech-shaped PCM without copied or recorded media."""

    if duration_seconds < 1.0:
        raise ValueError("duration_seconds must be at least one second")
    if sample_rate_hz < 8_000:
        raise ValueError("sample_rate_hz must be at least 8000")
    if path.exists():
        raise FileExistsError(f"refusing to overwrite existing fixture: {path}")

    path.parent.mkdir(parents=True, exist_ok=True)
    frame_count = round(duration_seconds * sample_rate_hz)
    samples = array("h")

    for index in range(frame_count):
        time_seconds = index / sample_rate_hz
        normalized = time_seconds / duration_seconds

        if normalized < 0.05 or normalized >= 0.96:
            amplitude = 0.0
        elif normalized < 0.40:
            amplitude = 0.10
        elif normalized < 0.47:
            amplitude = 0.003
        else:
            amplitude = 0.32

        syllabic = 0.22 + 0.78 * max(0.0, math.sin(2.0 * math.pi * 3.1 * time_seconds)) ** 0.8
        fundamental = 148.0 + 11.0 * math.sin(2.0 * math.pi * 0.43 * time_seconds)
        voice = (
            0.68 * math.sin(2.0 * math.pi * fundamental * time_seconds)
            + 0.22 * math.sin(2.0 * math.pi * fundamental * 2.03 * time_seconds + 0.4)
            + 0.10 * math.sin(2.0 * math.pi * fundamental * 3.97 * time_seconds + 1.1)
        )
        room_tone = 0.4 * math.sin(2.0 * math.pi * 59.7 * time_seconds)
        sample = amplitude * (syllabic * voice + (1.0 - syllabic) * room_tone)
        samples.append(round(max(-1.0, min(1.0, sample)) * 32767.0))

    if sys.byteorder != "little":
        samples.byteswap()
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate_hz)
        output.writeframes(samples.tobytes())
    return path
