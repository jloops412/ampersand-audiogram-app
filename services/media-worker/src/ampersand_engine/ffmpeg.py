from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any, cast

from ampersand_contracts import LoudnessMeasurement, MediaProbe, RecipeVersion

from .errors import DependencyUnavailable, EngineError, InvalidMedia


@dataclass(frozen=True)
class FFmpegTools:
    ffmpeg: str
    ffprobe: str
    ffmpeg_version: str
    ffprobe_version: str

    @classmethod
    def discover(cls) -> FFmpegTools:
        ffmpeg = shutil.which("ffmpeg")
        ffprobe = shutil.which("ffprobe")
        if not ffmpeg or not ffprobe:
            raise DependencyUnavailable("Ampersand requires ffmpeg and ffprobe on PATH.")
        return cls(
            ffmpeg=ffmpeg,
            ffprobe=ffprobe,
            ffmpeg_version=_tool_version(ffmpeg),
            ffprobe_version=_tool_version(ffprobe),
        )


def probe_media(path: Path, *, source_asset_id: str, probe_id: str, tools: FFmpegTools) -> MediaProbe:
    completed = _run(
        [
            tools.ffprobe,
            "-v",
            "error",
            "-protocol_whitelist",
            "file,pipe",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ],
        failure_message="ffprobe could not read the source",
        invalid_media=True,
    )
    try:
        payload: dict[str, Any] = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise InvalidMedia("ffprobe returned malformed media metadata.") from error

    streams = payload.get("streams")
    if not isinstance(streams, list):
        raise InvalidMedia("The source contains no readable streams.")
    audio = next(
        (stream for stream in streams if isinstance(stream, dict) and stream.get("codec_type") == "audio"),
        None,
    )
    if not isinstance(audio, dict):
        raise InvalidMedia("The source does not contain an audio stream.")

    raw_format = payload.get("format")
    format_payload = cast(dict[str, Any], raw_format) if isinstance(raw_format, dict) else {}
    duration_us = _duration_us(audio, format_payload)
    sample_rate = _positive_int(audio.get("sample_rate"), "sample rate")
    channels = _positive_int(audio.get("channels"), "channel count")
    format_name = str(format_payload.get("format_name") or audio.get("codec_name") or "unknown")
    codec_name = str(audio.get("codec_name") or "unknown")
    bit_rate = _optional_nonnegative_int(audio.get("bit_rate") or format_payload.get("bit_rate"))

    return MediaProbe(
        probe_id=probe_id,
        source_asset_id=source_asset_id,
        format_name=format_name,
        codec_name=codec_name,
        sample_format=str(audio["sample_fmt"]) if audio.get("sample_fmt") else None,
        duration_us=duration_us,
        sample_rate_hz=sample_rate,
        channels=channels,
        channel_layout=str(audio["channel_layout"]) if audio.get("channel_layout") else None,
        bit_rate_bps=bit_rate,
        ffprobe_version=tools.ffprobe_version,
    )


def requires_canonical_audio(probe: MediaProbe) -> bool:
    return not (
        probe.codec_name == "pcm_f32le" and probe.sample_rate_hz == 48_000 and "wav" in probe.format_name.split(",")
    )


def canonicalize_audio(source: Path, destination: Path, tools: FFmpegTools) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    _run(
        [
            tools.ffmpeg,
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-protocol_whitelist",
            "file,pipe",
            "-i",
            str(source),
            "-map",
            "0:a:0",
            "-vn",
            "-map_metadata",
            "-1",
            "-fflags",
            "+bitexact",
            "-flags:a",
            "+bitexact",
            "-ar",
            "48000",
            "-c:a",
            "pcm_f32le",
            "-y",
            str(destination),
        ],
        failure_message="ffmpeg failed to create canonical working audio",
    )


def measure_loudness(path: Path, tools: FFmpegTools) -> LoudnessMeasurement:
    completed = _run(
        [
            tools.ffmpeg,
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "info",
            "-protocol_whitelist",
            "file,pipe",
            "-i",
            str(path),
            "-map",
            "0:a:0",
            "-vn",
            "-af",
            "loudnorm=I=-16:TP=-1:LRA=11:print_format=json",
            "-f",
            "null",
            "-",
        ],
        failure_message="ffmpeg failed to measure loudness",
    )
    payload = _extract_loudnorm_json(completed.stderr)
    return LoudnessMeasurement(
        integrated_lufs=_finite_float(payload, "input_i"),
        true_peak_dbtp=_finite_float(payload, "input_tp"),
        loudness_range_lu=max(0.0, _finite_float(payload, "input_lra")),
        threshold_lufs=_finite_float(payload, "input_thresh"),
        measurement_backend="ffmpeg-loudnorm-bs1770",
        backend_version=tools.ffmpeg_version,
    )


def render_master_wav(
    source: Path,
    destination: Path,
    *,
    measurement: LoudnessMeasurement,
    recipe: RecipeVersion,
    tools: FFmpegTools,
) -> None:
    first_pass = _measure_loudnorm_pass(source, recipe=recipe, tools=tools)
    loudnorm = ":".join(
        (
            f"loudnorm=I={recipe.target_integrated_lufs:.3f}",
            f"TP={recipe.max_true_peak_dbtp:.3f}",
            f"LRA={recipe.target_loudness_range_lu:.3f}",
            f"measured_I={measurement.integrated_lufs:.6f}",
            f"measured_TP={measurement.true_peak_dbtp:.6f}",
            f"measured_LRA={measurement.loudness_range_lu:.6f}",
            f"measured_thresh={measurement.threshold_lufs:.6f}",
            f"offset={_finite_float(first_pass, 'target_offset'):.6f}",
            "linear=true",
            "print_format=summary",
        )
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    _run(
        [
            tools.ffmpeg,
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-protocol_whitelist",
            "file,pipe",
            "-i",
            str(source),
            "-map",
            "0:a:0",
            "-vn",
            "-af",
            loudnorm,
            "-map_metadata",
            "-1",
            "-fflags",
            "+bitexact",
            "-flags:a",
            "+bitexact",
            "-ar",
            "48000",
            "-c:a",
            "pcm_s24le",
            "-y",
            str(destination),
        ],
        failure_message="ffmpeg failed to render the WAV master",
    )


def encode_master_mp3(source_wav: Path, destination: Path, tools: FFmpegTools) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    _run(
        [
            tools.ffmpeg,
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-protocol_whitelist",
            "file,pipe",
            "-i",
            str(source_wav),
            "-map",
            "0:a:0",
            "-vn",
            "-map_metadata",
            "-1",
            "-fflags",
            "+bitexact",
            "-flags:a",
            "+bitexact",
            "-c:a",
            "libmp3lame",
            "-b:a",
            "192k",
            "-id3v2_version",
            "0",
            "-write_xing",
            "0",
            "-y",
            str(destination),
        ],
        failure_message="ffmpeg failed to encode the MP3 master",
    )


def decode_float32_command(path: Path, tools: FFmpegTools, *, sample_rate_hz: int = 48_000) -> list[str]:
    return [
        tools.ffmpeg,
        "-nostdin",
        "-hide_banner",
        "-loglevel",
        "error",
        "-protocol_whitelist",
        "file,pipe",
        "-i",
        str(path),
        "-map",
        "0:a:0",
        "-vn",
        "-ar",
        str(sample_rate_hz),
        "-c:a",
        "pcm_f32le",
        "-f",
        "f32le",
        "-",
    ]


def subprocess_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.update({"LC_ALL": "C", "LANG": "C", "TZ": "UTC"})
    return environment


def _measure_loudnorm_pass(path: Path, *, recipe: RecipeVersion, tools: FFmpegTools) -> dict[str, Any]:
    filter_value = (
        f"loudnorm=I={recipe.target_integrated_lufs:.3f}:TP={recipe.max_true_peak_dbtp:.3f}:"
        f"LRA={recipe.target_loudness_range_lu:.3f}:print_format=json"
    )
    completed = _run(
        [
            tools.ffmpeg,
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "info",
            "-protocol_whitelist",
            "file,pipe",
            "-i",
            str(path),
            "-map",
            "0:a:0",
            "-vn",
            "-af",
            filter_value,
            "-f",
            "null",
            "-",
        ],
        failure_message="ffmpeg failed during the first loudness-normalization pass",
    )
    return _extract_loudnorm_json(completed.stderr)


def _run(
    command: list[str],
    *,
    failure_message: str,
    invalid_media: bool = False,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        env=subprocess_environment(),
        text=True,
    )
    if completed.returncode != 0:
        detail = _last_nonempty_line(completed.stderr) or _last_nonempty_line(completed.stdout)
        message = f"{failure_message}: {detail}" if detail else failure_message
        if invalid_media:
            raise InvalidMedia(message)
        raise EngineError(message)
    return completed


def _tool_version(executable: str) -> str:
    completed = subprocess.run(
        [executable, "-version"],
        check=False,
        capture_output=True,
        env=subprocess_environment(),
        text=True,
    )
    if completed.returncode != 0:
        raise DependencyUnavailable(f"Could not execute required tool: {executable}")
    first_line = completed.stdout.splitlines()[0].strip() if completed.stdout.splitlines() else "unknown"
    return first_line[:256]


def _duration_us(audio: dict[str, Any], format_payload: dict[str, Any]) -> int:
    raw_duration = audio.get("duration") or format_payload.get("duration")
    if raw_duration not in (None, "N/A"):
        duration = Decimal(str(raw_duration))
    elif audio.get("duration_ts") not in (None, "N/A") and audio.get("time_base"):
        numerator, denominator = str(audio["time_base"]).split("/", maxsplit=1)
        duration = Decimal(str(audio["duration_ts"])) * Decimal(numerator) / Decimal(denominator)
    else:
        raise InvalidMedia("The source has no usable duration metadata.")
    microseconds = int((duration * Decimal(1_000_000)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    if microseconds <= 0:
        raise InvalidMedia("The source duration must be positive.")
    return microseconds


def _positive_int(value: Any, label: str) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError) as error:
        raise InvalidMedia(f"The source has no usable {label}.") from error
    if result <= 0:
        raise InvalidMedia(f"The source has an invalid {label}.")
    return result


def _optional_nonnegative_int(value: Any) -> int | None:
    if value in (None, "N/A"):
        return None
    try:
        result = int(value)
    except (TypeError, ValueError):
        return None
    return result if result >= 0 else None


def _extract_loudnorm_json(stderr: str) -> dict[str, Any]:
    start = stderr.rfind("{")
    end = stderr.find("}", start)
    if start < 0 or end < 0:
        raise EngineError("ffmpeg loudness analysis did not return a JSON measurement.")
    try:
        payload: dict[str, Any] = json.loads(stderr[start : end + 1])
    except json.JSONDecodeError as error:
        raise EngineError("ffmpeg loudness analysis returned malformed JSON.") from error
    return payload


def _finite_float(payload: dict[str, Any], key: str) -> float:
    try:
        value = float(payload[key])
    except (KeyError, TypeError, ValueError) as error:
        raise EngineError(f"ffmpeg loudness result is missing {key}.") from error
    if not math.isfinite(value):
        raise InvalidMedia(f"Audio is too short or silent for a finite {key} measurement.")
    return value


def _last_nonempty_line(value: str) -> str:
    return next((line.strip() for line in reversed(value.splitlines()) if line.strip()), "")
