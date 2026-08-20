from __future__ import annotations

import math
import os
import platform
import shutil
import subprocess
import tempfile
import time
import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import numpy.typing as npt
from ampersand_contracts import (
    GainEnvelope,
    GainRenderManifest,
    GainRenderRuntimeReport,
    manifest_sha256,
    write_manifest,
)

from . import __version__
from .errors import EngineError, OutputValidationError
from .ffmpeg import FFmpegTools, decode_float32_command, probe_media, subprocess_environment
from .hashing import sha256_file, sha256_text, stable_id

RENDERER_ALGORITHM_VERSION = "0.1.0"
SAMPLE_RATE_HZ = 48_000
DEFAULT_BLOCK_FRAMES = 65_536
MAX_FRAME_DELTA = 2
MAX_ADJACENT_GAIN_DELTA_DB = 0.001

FloatArray = npt.NDArray[np.float64]


@dataclass(frozen=True)
class GainRenderResult:
    output_directory: Path
    candidate_path: Path
    manifest: GainRenderManifest
    runtime: GainRenderRuntimeReport


@dataclass(frozen=True)
class _PcmRenderStatistics:
    rendered_frame_count: int
    input_sample_peak: float
    output_sample_peak: float
    clipping_sample_count: int
    maximum_adjacent_gain_delta_db: float
    peak_working_buffer_bytes: int


def render_leveler_candidate(
    source: Path,
    gain_envelope: GainEnvelope,
    destination: Path,
    *,
    tools: FFmpegTools | None = None,
    block_frames: int = DEFAULT_BLOCK_FRAMES,
) -> GainRenderResult:
    """Render one evaluation-only, channel-linked, sample-accurate Leveler candidate.

    The candidate deliberately skips final loudness normalization. The blinded listening
    harness creates validated loudness-matched copies, while the production master remains
    on the separately approved final-master path.
    """

    if gain_envelope.purpose != "adaptive_leveler":
        raise ValueError("the evaluation renderer requires an adaptive_leveler envelope")
    if block_frames <= 0:
        raise ValueError("block_frames must be positive")
    source_path = source.expanduser().resolve(strict=True)
    if not source_path.is_file() or source_path.stat().st_size <= 0:
        raise EngineError("The Leveler evaluation source must be a non-empty local file.")
    output_directory = destination.expanduser().resolve(strict=False)
    if output_directory.exists():
        raise FileExistsError(f"refusing to overwrite existing Leveler evaluation output: {output_directory}")

    output_directory.parent.mkdir(parents=True, exist_ok=True)
    selected_tools = tools or FFmpegTools.discover()
    source_sha = sha256_file(source_path)
    source_asset_id = stable_id("asset", source_sha)
    source_probe = probe_media(
        source_path,
        source_asset_id=source_asset_id,
        probe_id=stable_id("probe", source_sha),
        tools=selected_tools,
    )
    if abs(source_probe.duration_us - gain_envelope.duration_us) > 10_000:
        raise OutputValidationError("The gain envelope duration does not match the evaluation source.")
    if source_probe.channels > 8:
        raise OutputValidationError("The Leveler evaluation renderer supports no more than eight channels.")

    started = time.perf_counter()
    temporary = Path(tempfile.mkdtemp(prefix=f".{output_directory.name}-", dir=output_directory.parent))
    try:
        raw_path = temporary / "decoded.f32le"
        candidate_path = temporary / "candidate.wav"
        _decode_source(source_path, raw_path, tools=selected_tools, channels=source_probe.channels)
        pcm = _render_pcm24(
            raw_path,
            candidate_path,
            gain_envelope=gain_envelope,
            channels=source_probe.channels,
            block_frames=block_frames,
        )
        raw_path.unlink()
        expected_frames = _frames_for_duration(gain_envelope.duration_us)
        frame_delta = pcm.rendered_frame_count - expected_frames
        if abs(frame_delta) > MAX_FRAME_DELTA:
            raise OutputValidationError("Decoded frame count does not match the gain-envelope duration.")
        if pcm.clipping_sample_count:
            raise OutputValidationError("The proposed gain envelope would clip the evaluation candidate.")
        if pcm.maximum_adjacent_gain_delta_db > MAX_ADJACENT_GAIN_DELTA_DB + 1e-12:
            raise OutputValidationError("The proposed gain envelope changes too quickly for evaluation rendering.")

        candidate_sha = sha256_file(candidate_path)
        candidate_probe = probe_media(
            candidate_path,
            source_asset_id=stable_id("asset", candidate_sha),
            probe_id=stable_id("probe", candidate_sha),
            tools=selected_tools,
        )
        if candidate_probe.sample_rate_hz != SAMPLE_RATE_HZ or candidate_probe.channels != source_probe.channels:
            raise OutputValidationError("The Leveler evaluation candidate changed sample rate or channel count.")
        envelope_sha = manifest_sha256(gain_envelope)
        renderer_build_id = f"ampersand-media-worker:{__version__}"
        manifest_identity = sha256_text(
            "|".join(
                (
                    source_sha,
                    envelope_sha,
                    candidate_sha,
                    renderer_build_id,
                    RENDERER_ALGORITHM_VERSION,
                    selected_tools.ffmpeg_version,
                )
            )
        )
        gains = tuple(point.gain_db for point in gain_envelope.points)
        manifest = GainRenderManifest(
            gain_render_manifest_id=stable_id("gain-render", manifest_identity),
            run_id=gain_envelope.run_id,
            source_sha256=source_sha,
            gain_envelope_id=gain_envelope.gain_envelope_id,
            gain_envelope_sha256=envelope_sha,
            renderer_build_id=renderer_build_id,
            renderer_algorithm_version=RENDERER_ALGORITHM_VERSION,
            ffmpeg_version=selected_tools.ffmpeg_version,
            candidate_relative_path="candidate.wav",
            candidate_sha256=candidate_sha,
            candidate_size_bytes=candidate_path.stat().st_size,
            channels=candidate_probe.channels,
            source_duration_us=gain_envelope.duration_us,
            candidate_duration_us=candidate_probe.duration_us,
            expected_frame_count=expected_frames,
            rendered_frame_count=pcm.rendered_frame_count,
            frame_count_delta=frame_delta,
            input_sample_peak_dbfs=_dbfs(pcm.input_sample_peak),
            output_sample_peak_dbfs=_dbfs(pcm.output_sample_peak),
            gain_min_db=round(min(gains), 9),
            gain_max_db=round(max(gains), 9),
            maximum_adjacent_gain_delta_db=round(pcm.maximum_adjacent_gain_delta_db, 12),
        )
        elapsed = max(time.perf_counter() - started, 1e-9)
        audio_seconds = pcm.rendered_frame_count / SAMPLE_RATE_HZ
        runtime = GainRenderRuntimeReport(
            gain_render_runtime_report_id=stable_id(
                "gain-render-runtime",
                sha256_text(f"{manifest.gain_render_manifest_id}|{elapsed:.9f}|{pcm.peak_working_buffer_bytes}"),
            ),
            gain_render_manifest_id=manifest.gain_render_manifest_id,
            wall_seconds=round(elapsed, 9),
            audio_seconds=round(audio_seconds, 9),
            real_time_factor=round(elapsed / audio_seconds, 9),
            working_block_frames=block_frames,
            peak_working_buffer_mb=round(pcm.peak_working_buffer_bytes / (1024 * 1024), 6),
            device_summary=_device_summary(),
        )
        write_manifest(temporary / "gain-render-manifest.json", manifest)
        write_manifest(temporary / "gain-render-runtime.json", runtime)
        if sha256_file(source_path) != source_sha:
            raise OutputValidationError("The archived evaluation source changed during rendering.")
        if output_directory.exists():
            raise FileExistsError(f"refusing to overwrite Leveler evaluation output: {output_directory}")
        os.replace(temporary, output_directory)
        return GainRenderResult(
            output_directory=output_directory,
            candidate_path=output_directory / manifest.candidate_relative_path,
            manifest=manifest,
            runtime=runtime,
        )
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def _decode_source(source: Path, destination: Path, *, tools: FFmpegTools, channels: int) -> None:
    command = decode_float32_command(
        source,
        tools,
        sample_rate_hz=SAMPLE_RATE_HZ,
        channels=channels,
    )
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
        raise EngineError("FFmpeg could not decode the Leveler evaluation source.") from error
    if completed.returncode != 0:
        destination.unlink(missing_ok=True)
        raise EngineError("FFmpeg rejected the Leveler evaluation source.")


def _render_pcm24(
    raw_path: Path,
    candidate_path: Path,
    *,
    gain_envelope: GainEnvelope,
    channels: int,
    block_frames: int,
) -> _PcmRenderStatistics:
    point_frames = np.asarray(
        [point.at_us * SAMPLE_RATE_HZ / 1_000_000 for point in gain_envelope.points],
        dtype=np.float64,
    )
    point_gains = np.asarray([point.gain_db for point in gain_envelope.points], dtype=np.float64)
    rendered_frames = 0
    input_peak = 0.0
    output_peak = 0.0
    clipping_samples = 0
    maximum_gain_delta = 0.0
    previous_gain_db: float | None = None
    peak_buffer_bytes = 0
    bytes_per_block = block_frames * channels * 4

    with raw_path.open("rb") as source, wave.open(str(candidate_path), "wb") as output:
        output.setnchannels(channels)
        output.setsampwidth(3)
        output.setframerate(SAMPLE_RATE_HZ)
        while payload := source.read(bytes_per_block):
            if len(payload) % (channels * 4):
                raise EngineError("Decoded Leveler PCM ended with an incomplete channel frame.")
            decoded = np.frombuffer(payload, dtype="<f4").reshape((-1, channels))
            if not np.isfinite(decoded).all():
                raise OutputValidationError("Decoded Leveler PCM contains a non-finite sample.")
            frame_count = decoded.shape[0]
            frame_indices = np.arange(rendered_frames, rendered_frames + frame_count, dtype=np.float64)
            gain_db: FloatArray = np.interp(frame_indices, point_frames, point_gains)
            gain_linear: FloatArray = np.power(10.0, gain_db / 20.0)
            adjusted: FloatArray = decoded.astype(np.float64) * gain_linear[:, np.newaxis]
            magnitude = np.abs(adjusted)
            clipping_samples += int(np.count_nonzero(magnitude > 1.0))
            input_peak = max(input_peak, float(np.max(np.abs(decoded), initial=0.0)))
            output_peak = max(output_peak, float(np.max(magnitude, initial=0.0)))
            if gain_db.size:
                if previous_gain_db is not None:
                    maximum_gain_delta = max(maximum_gain_delta, abs(float(gain_db[0]) - previous_gain_db))
                if gain_db.size > 1:
                    maximum_gain_delta = max(maximum_gain_delta, float(np.max(np.abs(np.diff(gain_db)))))
                previous_gain_db = float(gain_db[-1])
            bounded = np.clip(adjusted, -1.0, 1.0)
            quantized = np.rint(bounded * 8_388_607.0).astype("<i4")
            packed = quantized.reshape(-1).view(np.uint8).reshape((-1, 4))[:, :3].tobytes()
            output.writeframesraw(packed)
            peak_buffer_bytes = max(
                peak_buffer_bytes,
                len(payload)
                + frame_indices.nbytes
                + gain_db.nbytes
                + gain_linear.nbytes
                + adjusted.nbytes
                + magnitude.nbytes
                + bounded.nbytes
                + quantized.nbytes
                + len(packed),
            )
            rendered_frames += frame_count
        output.writeframes(b"")
    if rendered_frames == 0:
        raise OutputValidationError("The Leveler evaluation source decoded to zero frames.")
    return _PcmRenderStatistics(
        rendered_frame_count=rendered_frames,
        input_sample_peak=input_peak,
        output_sample_peak=output_peak,
        clipping_sample_count=clipping_samples,
        maximum_adjacent_gain_delta_db=maximum_gain_delta,
        peak_working_buffer_bytes=peak_buffer_bytes,
    )


def _frames_for_duration(duration_us: int) -> int:
    return (duration_us * SAMPLE_RATE_HZ + 500_000) // 1_000_000


def _dbfs(magnitude: float) -> float:
    if magnitude <= 0.0:
        return -200.0
    return round(max(-200.0, min(0.0, 20.0 * math.log10(magnitude))), 9)


def _device_summary() -> str:
    return (
        f"{platform.system().lower()}-{platform.machine().lower()} python-{platform.python_implementation().lower()}"
    )[:256]
