from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any, cast

from ampersand_contracts import (
    AudiogramSettings,
    CleanupSettings,
    LoudnessMeasurement,
    MasteringSettings,
    MediaProbe,
    OutputMetadataSettings,
)

from .errors import DependencyUnavailable, EngineError, InvalidMedia
from .semantic_types import JsonValue, LoudnessFrame, LoudnessTimelineResult

_EBUR128_FRAME = re.compile(
    r"t:\s*(?P<time>\d+(?:\.\d+)?)\s+.*?M:\s*(?P<momentary>-?inf|nan|-?\d+(?:\.\d+)?)"
    r"\s+S:\s*(?P<short_term>-?inf|nan|-?\d+(?:\.\d+)?)\s+.*?FTPK:\s*(?P<frame_peak>.*?)\s+dBFS"
)


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


def measure_loudness_timeline(
    path: Path,
    *,
    duration_us: int,
    tools: FFmpegTools,
    hop_us: int = 100_000,
) -> LoudnessTimelineResult:
    """Measure deterministic EBU R128 momentary/short-term loudness and frame true peak."""

    if duration_us <= 0 or hop_us <= 0:
        raise ValueError("duration_us and hop_us must be positive")
    if hop_us != 100_000:
        raise ValueError("FFmpeg ebur128 emits a fixed 100 ms analysis hop")
    completed = _run(
        [
            tools.ffmpeg,
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "verbose",
            "-protocol_whitelist",
            "file,pipe",
            "-i",
            str(path),
            "-map",
            "0:a:0",
            "-vn",
            "-af",
            "ebur128=peak=true:framelog=verbose",
            "-f",
            "null",
            "-",
        ],
        failure_message="ffmpeg failed to measure the loudness timeline",
    )

    parsed: list[tuple[float, float, float, float, bool, tuple[float, ...]]] = []
    for line in completed.stderr.splitlines():
        match = _EBUR128_FRAME.search(line)
        if match is None:
            continue
        momentary = _finite_or_floor(match.group("momentary"))
        short_term = _finite_or_floor(match.group("short_term"))
        peaks, below_floor = _frame_true_peaks(match.group("frame_peak"))
        parsed.append(
            (
                float(match.group("time")),
                momentary,
                short_term,
                max(peaks),
                below_floor,
                peaks,
            )
        )

    expected_frames = (duration_us + hop_us - 1) // hop_us
    if len(parsed) < expected_frames:
        raise EngineError(
            f"ffmpeg ebur128 returned {len(parsed)} frames; {expected_frames} are required for full coverage."
        )

    frames: list[LoudnessFrame] = []
    raw_frames: list[JsonValue] = []
    for index, (provider_time, momentary, short_term, true_peak, below_floor, channel_peaks) in enumerate(
        parsed[:expected_frames]
    ):
        start_us = index * hop_us
        end_us = min(duration_us, start_us + hop_us)
        frames.append(
            LoudnessFrame(
                start_us=start_us,
                end_us=end_us,
                momentary_lufs=momentary,
                short_term_lufs=short_term,
                true_peak_dbtp=true_peak,
                below_true_peak_floor=below_floor,
            )
        )
        raw_frames.append(
            {
                "t_seconds": round(provider_time, 7),
                "M": momentary,
                "S": short_term,
                "FTPK": [round(value, 6) for value in channel_peaks],
                "below_true_peak_floor": below_floor,
            }
        )

    return LoudnessTimelineResult(
        frames=tuple(frames),
        provider_payload={
            "provider": "ffmpeg-ebur128",
            "provider_version": tools.ffmpeg_version,
            "analysis_hop_us": hop_us,
            "duration_us": duration_us,
            "privacy_redaction": "Only parsed metric frames are retained; command lines and local paths are excluded.",
            "frames": raw_frames,
        },
    )


def render_cleanup_wav(
    source: Path,
    destination: Path,
    *,
    settings: CleanupSettings,
    tools: FFmpegTools,
) -> None:
    """Apply the admitted global V1 cleanup chain to a new float working file."""

    filters: list[str] = []
    if settings.rumble_filter:
        filters.append("highpass=f=70:poles=2")
    denoise = {
        "light": "afftdn=nr=6:nf=-55:tn=1:gs=4",
        "balanced": "afftdn=nr=10:nf=-50:tn=1:gs=6",
        "strong": "afftdn=nr=15:nf=-45:tn=1:gs=8",
    }.get(settings.noise_reduction)
    if denoise is not None:
        filters.append(denoise)
    compressor = {
        "gentle": "acompressor=threshold=0.18:ratio=2:attack=20:release=250:makeup=1.15:knee=3:detection=rms",
        "balanced": "acompressor=threshold=0.125:ratio=3:attack=12:release=180:makeup=1.30:knee=3:detection=rms",
        "firm": "acompressor=threshold=0.09:ratio=4:attack=8:release=130:makeup=1.45:knee=4:detection=rms",
    }.get(settings.compression)
    if compressor is not None:
        filters.extend((compressor, "alimiter=limit=0.95:attack=5:release=50:level=false"))
    if not filters:
        raise ValueError("cleanup render requires at least one enabled cleanup control")

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
            ",".join(filters),
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
        failure_message="ffmpeg failed to render the admitted cleanup chain",
    )


def render_master_wav(
    source: Path,
    destination: Path,
    *,
    measurement: LoudnessMeasurement,
    settings: MasteringSettings,
    title: str,
    metadata: OutputMetadataSettings,
    tools: FFmpegTools,
) -> None:
    first_pass = _measure_loudnorm_pass(source, settings=settings, tools=tools)
    loudnorm = ":".join(
        (
            f"loudnorm=I={settings.target_integrated_lufs:.3f}",
            f"TP={settings.max_true_peak_dbtp:.3f}",
            f"LRA={settings.target_loudness_range_lu:.3f}",
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
            *_metadata_arguments(title, metadata),
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


def encode_master_mp3(
    source_wav: Path,
    destination: Path,
    tools: FFmpegTools,
    *,
    bitrate_kbps: int = 192,
    title: str,
    metadata: OutputMetadataSettings,
) -> None:
    if bitrate_kbps not in {128, 160, 192, 256, 320}:
        raise ValueError("unsupported MP3 bitrate")
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
            *_metadata_arguments(title, metadata),
            "-fflags",
            "+bitexact",
            "-flags:a",
            "+bitexact",
            "-c:a",
            "libmp3lame",
            "-b:a",
            f"{bitrate_kbps}k",
            "-id3v2_version",
            "3",
            "-write_id3v1",
            "0",
            "-write_xing",
            "0",
            "-y",
            str(destination),
        ],
        failure_message="ffmpeg failed to encode the MP3 master",
    )


def render_audiogram_mp4(
    source_wav: Path,
    destination: Path,
    *,
    title: str,
    metadata: OutputMetadataSettings,
    settings: AudiogramSettings,
    artwork: Path | None,
    tools: FFmpegTools,
) -> None:
    """Render a deterministic full-duration H.264 audiogram from the mastered WAV."""

    if not settings.enabled:
        raise ValueError("audiogram render requires audiogram.enabled")
    if settings.background_mode == "artwork" and artwork is None:
        raise ValueError("an uploaded background artwork is required for artwork mode")
    if artwork is not None and not artwork.is_file():
        raise InvalidMedia("The audiogram background artwork is unavailable.")

    width, height = {
        "square": (1080, 1080),
        "portrait": (1080, 1920),
        "landscape": (1920, 1080),
    }[settings.aspect_ratio]
    wave_width = int(width * 0.82)
    wave_height = max(220, int(height * 0.30))
    wave_mode = {"line": "line", "mirrored": "cline", "bars": "p2p"}[settings.waveform_style]
    background = settings.background_color.removeprefix("#")
    waveform = settings.waveform_color.removeprefix("#")
    text_color = settings.text_color.removeprefix("#")
    headline = settings.headline.strip() or title
    subtitle = settings.subtitle.strip()
    destination.parent.mkdir(parents=True, exist_ok=True)

    temporary_files: list[Path] = []
    try:
        headline_file = _write_drawtext_file(destination.parent, headline)
        temporary_files.append(headline_file)
        subtitle_file = _write_drawtext_file(destination.parent, subtitle) if subtitle else None
        if subtitle_file is not None:
            temporary_files.append(subtitle_file)

        input_arguments = (
            ["-loop", "1", "-framerate", "30", "-i", str(artwork)]
            if settings.background_mode == "artwork" and artwork is not None
            else ["-f", "lavfi", "-i", f"color=c=0x{background}:s={width}x{height}:r=30"]
        )
        base_filter = (
            f"[0:v]scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height},setsar=1,format=rgba,"
            "drawbox=x=0:y=0:w=iw:h=ih:color=black@0.34:t=fill[background]"
        )
        wave_filter = (
            f"[1:a]showwaves=s={wave_width}x{wave_height}:mode={wave_mode}:"
            f"colors=0x{waveform}:rate=30:scale=sqrt,format=rgba,"
            "colorkey=black:0.02:0.10[waveform]"
        )
        overlay_filter = "[background][waveform]overlay=(W-w)/2:(H-h)/2:shortest=1[composite]"
        headline_size = max(34, int(width * 0.048))
        title_filter = (
            f"[composite]drawtext=fontfile={_filter_path(_font_path())}:"
            f"textfile={_filter_path(headline_file)}:fontcolor=0x{text_color}:fontsize={headline_size}:"
            "x=(w-text_w)/2:y=h*0.14:box=1:boxcolor=black@0.28:boxborderw=18"
        )
        if subtitle_file is not None:
            subtitle_size = max(24, int(width * 0.027))
            title_filter += (
                f"[titled];[titled]drawtext=fontfile={_filter_path(_font_path())}:"
                f"textfile={_filter_path(subtitle_file)}:fontcolor=0x{text_color}@0.86:"
                f"fontsize={subtitle_size}:x=(w-text_w)/2:y=h*0.14+{headline_size + 54}[video]"
            )
        else:
            title_filter += "[video]"
        filter_complex = ";".join((base_filter, wave_filter, overlay_filter, title_filter))

        _run(
            [
                tools.ffmpeg,
                "-nostdin",
                "-hide_banner",
                "-loglevel",
                "error",
                "-protocol_whitelist",
                "file,pipe",
                *input_arguments,
                "-i",
                str(source_wav),
                "-filter_complex",
                filter_complex,
                "-map",
                "[video]",
                "-map",
                "1:a:0",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "22",
                "-pix_fmt",
                "yuv420p",
                "-r",
                "30",
                "-threads",
                "1",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-map_metadata",
                "-1",
                *_metadata_arguments(title, metadata),
                "-movflags",
                "+faststart",
                "-shortest",
                "-y",
                str(destination),
            ],
            failure_message="ffmpeg failed to render the audiogram",
        )
    finally:
        for temporary_file in temporary_files:
            temporary_file.unlink(missing_ok=True)


def decode_float32_command(
    path: Path,
    tools: FFmpegTools,
    *,
    sample_rate_hz: int = 48_000,
    channels: int | None = None,
) -> list[str]:
    command = [
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
    ]
    if channels is not None:
        if channels <= 0:
            raise ValueError("channels must be positive")
        command.extend(("-ac", str(channels)))
    command.extend(
        [
            "-ar",
            str(sample_rate_hz),
            "-c:a",
            "pcm_f32le",
            "-f",
            "f32le",
            "-",
        ]
    )
    return command


def _metadata_arguments(title: str, metadata: OutputMetadataSettings) -> list[str]:
    values = {
        "title": title,
        "artist": metadata.artist,
        "album": metadata.album,
        "genre": metadata.genre,
        "date": metadata.date,
        "comment": metadata.comment,
        "copyright": metadata.copyright,
        "track": metadata.track_number,
    }
    arguments: list[str] = []
    for key, value in values.items():
        normalized = " ".join(value.replace("\x00", " ").split()).strip()
        if normalized:
            arguments.extend(("-metadata", f"{key}={normalized}"))
    return arguments


def _write_drawtext_file(directory: Path, value: str) -> Path:
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        prefix=".audiogram-text-",
        suffix=".txt",
        dir=directory,
        delete=False,
    ) as handle:
        handle.write(" ".join(value.replace("\x00", " ").split())[:160])
        return Path(handle.name)


def _filter_path(path: Path) -> str:
    value = str(path)
    return "'" + value.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'") + "'"


def _font_path() -> Path:
    candidates = (
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
    )
    font = next((candidate for candidate in candidates if candidate.is_file()), None)
    if font is None:
        raise DependencyUnavailable("Ampersand requires an installed TrueType font for audiogram titles.")
    return font


def subprocess_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.update({"LC_ALL": "C", "LANG": "C", "TZ": "UTC"})
    return environment


def _measure_loudnorm_pass(
    path: Path,
    *,
    settings: MasteringSettings,
    tools: FFmpegTools,
) -> dict[str, Any]:
    filter_value = (
        f"loudnorm=I={settings.target_integrated_lufs:.3f}:TP={settings.max_true_peak_dbtp:.3f}:"
        f"LRA={settings.target_loudness_range_lu:.3f}:print_format=json"
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


def _finite_or_floor(raw: str, *, floor: float = -120.0) -> float:
    try:
        value = float(raw)
    except ValueError:
        return floor
    return value if math.isfinite(value) else floor


def _frame_true_peaks(raw: str) -> tuple[tuple[float, ...], bool]:
    values = tuple(_finite_or_floor(token) for token in raw.split())
    if not values:
        raise EngineError("ffmpeg ebur128 frame omitted its true-peak measurement")
    below_floor = all(not math.isfinite(float(token)) for token in raw.split())
    return values, below_floor


def _last_nonempty_line(value: str) -> str:
    return next((line.strip() for line in reversed(value.splitlines()) if line.strip()), "")
