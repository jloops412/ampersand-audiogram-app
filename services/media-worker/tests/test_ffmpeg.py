from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from ampersand_engine import ffmpeg as ffmpeg_module
from ampersand_engine.errors import EngineError
from ampersand_engine.ffmpeg import FFmpegTools, measure_loudness_timeline, probe_media
from ampersand_test_fixtures import generate_spoken_word_fixture
from ampersand_test_fixtures.audio import write_pcm16_fixture


def test_loudness_timeline_measures_and_normalizes_a_partial_tail(tmp_path: Path) -> None:
    sample_rate_hz = 48_000
    tail_impulse_start = round(1.02 * sample_rate_hz)
    source = write_pcm16_fixture(
        tmp_path / "partial-tail.wav",
        duration_seconds=1.05,
        sample_rate_hz=sample_rate_hz,
        channels=1,
        sample_at=lambda frame_index, _channel: (
            0.8 if tail_impulse_start <= frame_index < tail_impulse_start + 48 else 0.0
        ),
    )
    tools = FFmpegTools.discover()
    probe = probe_media(source, source_asset_id="asset:test", probe_id="probe:test", tools=tools)

    result = measure_loudness_timeline(source, duration_us=probe.duration_us, tools=tools)

    assert len(result.frames) == 11
    assert result.frames[0].start_us == 0
    assert result.frames[-1].start_us == 1_000_000
    assert result.frames[-1].end_us == 1_050_000
    assert all(
        previous.end_us == current.start_us for previous, current in zip(result.frames, result.frames[1:], strict=False)
    )
    assert result.frames[-1].true_peak_dbtp > -3.0
    assert result.provider_payload["duration_us"] == 1_050_000
    assert result.provider_payload["analysis_duration_us"] == 1_100_000
    assert result.provider_payload["tail_padding_us"] == 50_000
    assert result.provider_payload["tail_padding_policy"] == "zero_pad_final_partial_hop"
    assert len(result.provider_payload["frames"]) == 11


def test_loudness_timeline_does_not_pad_an_exact_hop_boundary(tmp_path: Path) -> None:
    source = generate_spoken_word_fixture(tmp_path / "exact-hop.wav", duration_seconds=1.1)
    tools = FFmpegTools.discover()
    probe = probe_media(source, source_asset_id="asset:test", probe_id="probe:test", tools=tools)

    result = measure_loudness_timeline(source, duration_us=probe.duration_us, tools=tools)

    assert len(result.frames) == 11
    assert result.frames[-1].end_us == 1_100_000
    assert result.provider_payload["analysis_duration_us"] == 1_100_000
    assert result.provider_payload["tail_padding_us"] == 0
    assert result.provider_payload["tail_padding_policy"] == "none"


def test_loudness_timeline_still_fails_when_provider_frames_are_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(
        command: list[str],
        *,
        failure_message: str,
        invalid_media: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        del failure_message, invalid_media
        assert "apad=whole_dur=0.200000" in command[command.index("-af") + 1]
        return subprocess.CompletedProcess(
            command,
            0,
            stderr="[Parsed_ebur128] t: 0.1 M: -20.0 S: -21.0 FTPK: -1.0 dBFS\n",
        )

    monkeypatch.setattr(ffmpeg_module, "_run", fake_run)

    with pytest.raises(EngineError, match=r"returned 1 frames; 2 are required"):
        measure_loudness_timeline(
            Path("synthetic.wav"),
            duration_us=150_000,
            tools=FFmpegTools("ffmpeg", "ffprobe", "test-ffmpeg", "test-ffprobe"),
        )


def test_loudness_timeline_rejects_a_discontinuous_provider_grid(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(
        command: list[str],
        *,
        failure_message: str,
        invalid_media: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        del failure_message, invalid_media
        return subprocess.CompletedProcess(
            command,
            0,
            stderr=(
                "[Parsed_ebur128] t: 0.1 M: -20.0 S: -21.0 FTPK: -1.0 dBFS\n"
                "[Parsed_ebur128] t: 0.3 M: -20.0 S: -21.0 FTPK: -1.0 dBFS\n"
            ),
        )

    monkeypatch.setattr(ffmpeg_module, "_run", fake_run)

    with pytest.raises(EngineError, match=r"timeline is discontinuous at frame 2"):
        measure_loudness_timeline(
            Path("synthetic.wav"),
            duration_us=200_000,
            tools=FFmpegTools("ffmpeg", "ffprobe", "test-ffmpeg", "test-ffprobe"),
        )
