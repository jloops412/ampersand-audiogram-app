from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np
import numpy.typing as npt
from ampersand_contracts import WaveformLevel, WaveformPeaks

from .errors import EngineError
from .ffmpeg import FFmpegTools, decode_float32_command, subprocess_environment

FloatArray = npt.NDArray[np.float32]
STUDIO_MAX_WAVEFORM_SAMPLES_PER_CHANNEL = 240_000


def generate_waveform_peaks(
    source: Path,
    *,
    waveform_id: str,
    source_asset_id: str,
    channels: int,
    duration_us: int,
    tools: FFmpegTools,
    sample_rate_hz: int = 48_000,
    base_window_samples: int = 960,
) -> WaveformPeaks:
    if channels <= 0:
        raise ValueError("channels must be positive")
    command = decode_float32_command(source, tools, sample_rate_hz=sample_rate_hz)
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=subprocess_environment(),
    )
    if process.stdout is None or process.stderr is None:
        raise EngineError("Could not open the waveform decoder pipes.")

    frames_pending = np.empty((0, channels), dtype=np.float32)
    byte_tail = b""
    level_zero_chunks: list[FloatArray] = []
    bytes_per_frame = channels * 4

    while chunk := process.stdout.read(4 * 1024 * 1024):
        payload = byte_tail + chunk
        complete_size = len(payload) - (len(payload) % bytes_per_frame)
        complete, byte_tail = payload[:complete_size], payload[complete_size:]
        if not complete:
            continue
        decoded = np.frombuffer(complete, dtype="<f4").reshape((-1, channels))
        frames = np.concatenate((frames_pending, decoded), axis=0) if frames_pending.size else decoded
        window_count = frames.shape[0] // base_window_samples
        if window_count:
            bounded = frames[: window_count * base_window_samples].reshape(
                (window_count, base_window_samples, channels)
            )
            minimums = bounded.min(axis=1)
            maximums = bounded.max(axis=1)
            level_zero_chunks.append(np.stack((minimums, maximums), axis=-1))
        frames_pending = frames[window_count * base_window_samples :].copy()

    stderr = process.stderr.read().decode("utf-8", errors="replace")
    return_code = process.wait()
    if return_code != 0:
        detail = next((line.strip() for line in reversed(stderr.splitlines()) if line.strip()), "")
        raise EngineError(f"ffmpeg failed to decode waveform samples: {detail}".rstrip())
    if byte_tail:
        raise EngineError("Decoded PCM ended with an incomplete audio frame.")
    if frames_pending.size:
        level_zero_chunks.append(
            np.stack((frames_pending.min(axis=0), frames_pending.max(axis=0)), axis=-1)[np.newaxis, ...]
        )
    if not level_zero_chunks:
        raise EngineError("The source produced no waveform samples.")

    current = np.concatenate(level_zero_chunks, axis=0).astype(np.float32, copy=False)
    levels: list[WaveformLevel] = []
    samples_per_window = base_window_samples
    while True:
        levels.append(
            WaveformLevel(
                samples_per_window=samples_per_window,
                windows=_contract_windows(current),
            )
        )
        if current.shape[0] <= 1:
            break
        current = _combine_adjacent(current)
        samples_per_window *= 2

    return WaveformPeaks(
        waveform_id=waveform_id,
        source_asset_id=source_asset_id,
        sample_rate_hz=sample_rate_hz,
        channels=channels,
        duration_us=duration_us,
        levels=tuple(levels),
    )


def select_studio_waveform_peaks(
    waveform: WaveformPeaks,
    *,
    max_samples_per_channel: int = STUDIO_MAX_WAVEFORM_SAMPLES_PER_CHANNEL,
) -> WaveformPeaks:
    """Return a deterministic one-level browser view while preserving canonical waveform identity."""
    if max_samples_per_channel < 2:
        raise ValueError("max_samples_per_channel must be at least two")
    populated = [level for level in waveform.levels if level.windows]
    if not populated:
        raise ValueError("waveform must contain a populated level")
    ordered = sorted(populated, key=lambda level: level.samples_per_window)
    selected = next(
        (level for level in ordered if len(level.windows) * 2 <= max_samples_per_channel),
        ordered[-1],
    )
    return waveform.model_copy(update={"levels": (selected,)})


def _combine_adjacent(level: FloatArray) -> FloatArray:
    pair_count = level.shape[0] // 2
    combined: list[FloatArray] = []
    if pair_count:
        paired = level[: pair_count * 2].reshape((pair_count, 2, level.shape[1], 2))
        minimums = paired[:, :, :, 0].min(axis=1)
        maximums = paired[:, :, :, 1].max(axis=1)
        combined.append(np.stack((minimums, maximums), axis=-1))
    if level.shape[0] % 2:
        combined.append(level[-1:, :, :])
    return np.concatenate(combined, axis=0).astype(np.float32, copy=False)


def _contract_windows(level: FloatArray) -> tuple[tuple[tuple[float, float], ...], ...]:
    rounded = np.round(level.astype(np.float64), decimals=7).tolist()
    return tuple(tuple((float(channel[0]), float(channel[1])) for channel in window) for window in rounded)
