from __future__ import annotations

import math
import subprocess
import sys
from array import array
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from ampersand_engine.ffmpeg import FFmpegTools, decode_float32_command, subprocess_environment

from .errors import ListeningLabError


@dataclass(frozen=True)
class PcmDiagnostics:
    sample_peak_dbfs: float
    clipping_sample_count: int


def decode_float32(path: Path, destination: Path, tools: FFmpegTools) -> Path:
    """Decode local audio to deterministic 48 kHz interleaved f32le for bounded streaming metrics."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    command = decode_float32_command(path, tools, sample_rate_hz=48_000)
    command[-1] = str(destination)
    try:
        completed = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=7_200,
            env=subprocess_environment(),
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        destination.unlink(missing_ok=True)
        raise ListeningLabError("FFmpeg could not decode a listening candidate for diagnostics.") from error
    if completed.returncode != 0:
        destination.unlink(missing_ok=True)
        raise ListeningLabError("FFmpeg rejected a listening candidate during diagnostics.")
    return destination


def measure_pcm(path: Path) -> PcmDiagnostics:
    maximum = 0.0
    clipping = 0
    for samples in _float_blocks(path):
        for sample in samples:
            magnitude = abs(sample)
            maximum = max(maximum, magnitude)
            if magnitude >= 0.999969:
                clipping += 1
    peak_dbfs = -200.0 if maximum <= 0.0 else max(-200.0, min(0.0, 20.0 * math.log10(maximum)))
    return PcmDiagnostics(sample_peak_dbfs=round(peak_dbfs, 6), clipping_sample_count=clipping)


def full_reference_metrics(
    reference_path: Path,
    reference_channels: int,
    candidate_path: Path,
    candidate_channels: int,
) -> tuple[float | None, float | None]:
    """Calculate centered SNR and SI-SDR with bounded memory when decoded frame counts align."""

    reference = _mono_blocks(reference_path, reference_channels)
    candidate = _mono_blocks(candidate_path, candidate_channels)
    count = 0
    reference_sum = 0.0
    candidate_sum = 0.0
    reference_square_sum = 0.0
    candidate_square_sum = 0.0
    dot_sum = 0.0
    while True:
        reference_block = next(reference, None)
        candidate_block = next(candidate, None)
        if reference_block is None or candidate_block is None:
            if reference_block is not None or candidate_block is not None:
                return None, None
            break
        if len(reference_block) != len(candidate_block):
            return None, None
        count += len(reference_block)
        reference_sum += sum(reference_block)
        candidate_sum += sum(candidate_block)
        reference_square_sum += sum(value * value for value in reference_block)
        candidate_square_sum += sum(value * value for value in candidate_block)
        dot_sum += sum(left * right for left, right in zip(reference_block, candidate_block, strict=True))
    if count == 0:
        return None, None
    reference_energy = reference_square_sum - reference_sum * reference_sum / count
    candidate_energy = candidate_square_sum - candidate_sum * candidate_sum / count
    dot = dot_sum - reference_sum * candidate_sum / count
    if reference_energy <= 1e-20:
        return None, None
    noise_energy = max(1e-20, reference_energy + candidate_energy - 2.0 * dot)
    target_energy = max(1e-20, dot * dot / reference_energy)
    residual_energy = max(1e-20, candidate_energy - target_energy)
    snr = min(200.0, 10.0 * math.log10(reference_energy / noise_energy))
    si_sdr = min(200.0, 10.0 * math.log10(target_energy / residual_energy))
    return round(snr, 6), round(si_sdr, 6)


def _float_blocks(path: Path, *, block_samples: int = 65_536) -> Iterator[array[float]]:
    with path.open("rb") as source:
        while payload := source.read(block_samples * 4):
            if len(payload) % 4:
                raise ListeningLabError("Decoded diagnostic PCM is truncated.")
            samples = array("f")
            samples.frombytes(payload)
            if sys.byteorder != "little":
                samples.byteswap()
            yield samples


def _mono_blocks(path: Path, channels: int, *, block_frames: int = 16_384) -> Iterator[array[float]]:
    if channels <= 0:
        raise ValueError("channels must be positive")
    block_samples = block_frames * channels
    for samples in _float_blocks(path, block_samples=block_samples):
        if len(samples) % channels:
            raise ListeningLabError("Decoded diagnostic PCM does not contain complete channel frames.")
        mono = array("d")
        for index in range(0, len(samples), channels):
            mono.append(sum(samples[index : index + channels]) / channels)
        yield mono
