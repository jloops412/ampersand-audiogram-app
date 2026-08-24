from __future__ import annotations

from pathlib import Path

import pytest
from ampersand_engine.energy_vad import analyze_energy_vad
from ampersand_engine.errors import EngineError
from ampersand_engine.ffmpeg import FFmpegTools, probe_media
from ampersand_test_fixtures import generate_spoken_word_fixture
from ampersand_test_fixtures.audio import write_pcm16_fixture


def test_energy_vad_normalizes_a_subsample_source_tail(tmp_path: Path) -> None:
    source = generate_spoken_word_fixture(tmp_path / "subsample-tail.wav", duration_seconds=1.00002)
    tools = FFmpegTools.discover()
    probe = probe_media(source, source_asset_id="asset:test", probe_id="probe:test", tools=tools)

    result = analyze_energy_vad(source, duration_us=probe.duration_us, tools=tools)

    assert probe.duration_us == 1_000_021
    assert len(result.frames) == 11
    assert result.frames[-1].start_us == 1_000_000
    assert result.frames[-1].end_us == probe.duration_us
    assert result.provider_payload["analysis_duration_us"] == 1_100_000
    assert result.provider_payload["tail_padding_us"] == 99_979
    assert result.provider_payload["tail_padding_policy"] == "zero_pad_final_partial_hop"
    assert result.provider_payload["decoded_sample_count"] == 16_000
    assert result.provider_payload["analysis_zero_padding_samples"] == 1_600


def test_energy_vad_measures_a_tail_transient_before_padding(tmp_path: Path) -> None:
    sample_rate_hz = 48_000
    tail_impulse_start = round(1.02 * sample_rate_hz)
    source = write_pcm16_fixture(
        tmp_path / "tail-transient.wav",
        duration_seconds=1.05,
        sample_rate_hz=sample_rate_hz,
        channels=1,
        sample_at=lambda frame_index, _channel: (
            0.8 if tail_impulse_start <= frame_index < tail_impulse_start + 480 else 0.0
        ),
    )
    tools = FFmpegTools.discover()
    probe = probe_media(source, source_asset_id="asset:test", probe_id="probe:test", tools=tools)

    result = analyze_energy_vad(source, duration_us=probe.duration_us, tools=tools)

    assert len(result.frames) == 11
    assert result.frames[-1].end_us == 1_050_000
    assert result.frames[-1].sample_peak_dbfs > -3.0
    assert result.provider_payload["tail_padding_us"] == 50_000
    assert result.provider_payload["analysis_zero_padding_samples"] == 800


def test_energy_vad_does_not_pad_an_exact_hop_boundary(tmp_path: Path) -> None:
    source = generate_spoken_word_fixture(tmp_path / "exact-hop.wav", duration_seconds=1.0)
    tools = FFmpegTools.discover()
    probe = probe_media(source, source_asset_id="asset:test", probe_id="probe:test", tools=tools)

    result = analyze_energy_vad(source, duration_us=probe.duration_us, tools=tools)

    assert len(result.frames) == 10
    assert result.frames[-1].end_us == 1_000_000
    assert result.provider_payload["tail_padding_us"] == 0
    assert result.provider_payload["tail_padding_policy"] == "none"
    assert result.provider_payload["analysis_zero_padding_samples"] == 0


def test_energy_vad_rejects_coverage_missing_beyond_the_final_partial_hop(tmp_path: Path) -> None:
    source = generate_spoken_word_fixture(tmp_path / "short.wav", duration_seconds=1.0)

    with pytest.raises(EngineError, match=r"returned 10 frames; 12 are required"):
        analyze_energy_vad(source, duration_us=1_200_000, tools=FFmpegTools.discover())
