from __future__ import annotations

import json
import wave
from pathlib import Path

import numpy as np
import pytest
from ampersand_contracts import (
    GainEnvelope,
    GainPoint,
    GainRenderManifest,
    GainRenderRuntimeReport,
    read_manifest,
    write_manifest,
)
from ampersand_engine.cli import main
from ampersand_engine.errors import OutputValidationError
from ampersand_engine.gain_renderer import render_leveler_candidate
from ampersand_engine.hashing import sha256_file
from ampersand_test_fixtures.audio import write_pcm16_fixture

SECOND = 1_000_000


def test_renderer_is_sample_accurate_channel_linked_immutable_and_deterministic(tmp_path: Path) -> None:
    source = _stereo_source(tmp_path / "stereo.wav", duration_seconds=2.0)
    source_before = sha256_file(source)
    envelope = GainEnvelope(
        gain_envelope_id="gain-envelope:stereo-evaluation",
        run_id="run:stereo-evaluation",
        duration_us=2 * SECOND,
        points=(
            GainPoint(at_us=0, gain_db=0.0),
            GainPoint(at_us=SECOND, gain_db=6.0),
            GainPoint(at_us=2 * SECOND, gain_db=0.0),
        ),
        purpose="adaptive_leveler",
    )

    first = render_leveler_candidate(source, envelope, tmp_path / "first")
    second = render_leveler_candidate(source, envelope, tmp_path / "second")

    assert sha256_file(source) == source_before
    assert first.candidate_path.read_bytes() == second.candidate_path.read_bytes()
    assert first.manifest == second.manifest
    assert first.runtime.gain_render_manifest_id == first.manifest.gain_render_manifest_id
    assert first.runtime.wall_seconds > 0
    assert first.runtime.real_time_factor >= 0
    assert first.runtime.external_api_cost_usd == 0
    assert first.runtime.peak_working_buffer_mb < 20
    assert first.manifest.evaluation_only
    assert not first.manifest.production_approved
    assert not first.manifest.final_loudness_applied
    assert first.manifest.listening_loudness_match_required
    assert first.manifest.channel_linked
    assert first.manifest.sample_accurate
    assert first.manifest.clipping_sample_count == 0
    assert first.manifest.maximum_adjacent_gain_delta_db <= 6.0 / 48_000 + 1e-10
    assert read_manifest(first.output_directory / "gain-render-manifest.json", GainRenderManifest) == first.manifest
    assert isinstance(
        read_manifest(first.output_directory / "gain-render-runtime.json", GainRenderRuntimeReport),
        GainRenderRuntimeReport,
    )

    frames = _read_pcm24(first.candidate_path)
    assert frames.shape == (96_000, 2)
    assert frames[48_000, 0] == pytest.approx(frames[0, 0] * 10 ** (6 / 20), rel=3e-4)
    input_channel_ratio = frames[0, 1] / frames[0, 0]
    assert frames[48_000, 1] / frames[48_000, 0] == pytest.approx(input_channel_ratio, abs=2e-6)


def test_renderer_refuses_duration_mismatch_clipping_wrong_purpose_and_overwrite(tmp_path: Path) -> None:
    source = _stereo_source(tmp_path / "source.wav", duration_seconds=2.0, left=0.75, right=-0.25)
    short = GainEnvelope(
        gain_envelope_id="gain-envelope:short",
        run_id="run:short",
        duration_us=SECOND,
        points=(GainPoint(at_us=0, gain_db=0), GainPoint(at_us=SECOND, gain_db=0)),
        purpose="adaptive_leveler",
    )
    with pytest.raises(OutputValidationError, match="duration"):
        render_leveler_candidate(source, short, tmp_path / "duration-mismatch")
    assert not (tmp_path / "duration-mismatch").exists()

    clipping = GainEnvelope(
        gain_envelope_id="gain-envelope:clipping",
        run_id="run:clipping",
        duration_us=2 * SECOND,
        points=(GainPoint(at_us=0, gain_db=6), GainPoint(at_us=2 * SECOND, gain_db=6)),
        purpose="adaptive_leveler",
    )
    with pytest.raises(OutputValidationError, match="clip"):
        render_leveler_candidate(source, clipping, tmp_path / "clipping")
    assert not (tmp_path / "clipping").exists()

    too_fast = GainEnvelope(
        gain_envelope_id="gain-envelope:too-fast",
        run_id="run:too-fast",
        duration_us=2 * SECOND,
        points=(
            GainPoint(at_us=0, gain_db=0),
            GainPoint(at_us=1_000, gain_db=6),
            GainPoint(at_us=2 * SECOND, gain_db=0),
        ),
        purpose="adaptive_leveler",
    )
    with pytest.raises(OutputValidationError, match="too quickly"):
        render_leveler_candidate(
            _stereo_source(tmp_path / "quiet.wav", duration_seconds=2.0, left=0.1, right=-0.05),
            too_fast,
            tmp_path / "too-fast",
        )
    assert not (tmp_path / "too-fast").exists()

    unity = clipping.model_copy(
        update={
            "gain_envelope_id": "gain-envelope:unity",
            "purpose": "unity_baseline",
        }
    )
    with pytest.raises(ValueError, match="adaptive_leveler"):
        render_leveler_candidate(source, unity, tmp_path / "wrong-purpose")

    existing = tmp_path / "existing"
    existing.mkdir()
    with pytest.raises(FileExistsError, match="overwrite"):
        render_leveler_candidate(source, clipping, existing)


def test_small_working_blocks_remain_bounded_for_a_longer_control(tmp_path: Path) -> None:
    source = _stereo_source(tmp_path / "longer.wav", duration_seconds=16.0)
    envelope = GainEnvelope(
        gain_envelope_id="gain-envelope:longer",
        run_id="run:longer",
        duration_us=16 * SECOND,
        points=(
            GainPoint(at_us=0, gain_db=0),
            GainPoint(at_us=8 * SECOND, gain_db=3),
            GainPoint(at_us=16 * SECOND, gain_db=0),
        ),
        purpose="adaptive_leveler",
    )

    result = render_leveler_candidate(source, envelope, tmp_path / "longer", block_frames=1_024)

    assert result.manifest.rendered_frame_count == 16 * 48_000
    assert result.runtime.working_block_frames == 1_024
    assert result.runtime.peak_working_buffer_mb < 0.2


def test_cli_writes_an_explicit_evaluation_only_candidate(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = _stereo_source(tmp_path / "cli-source.wav", duration_seconds=1.0)
    envelope = GainEnvelope(
        gain_envelope_id="gain-envelope:cli",
        run_id="run:cli",
        duration_us=SECOND,
        points=(GainPoint(at_us=0, gain_db=0), GainPoint(at_us=SECOND, gain_db=0)),
        purpose="adaptive_leveler",
    )
    envelope_path = tmp_path / "gain-envelope.json"
    write_manifest(envelope_path, envelope)

    status = main(
        (
            "render-leveler-candidate",
            str(source),
            str(envelope_path),
            "--output",
            str(tmp_path / "cli-output"),
        )
    )

    assert status == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "evaluation_only"
    assert (tmp_path / "cli-output/candidate.wav").is_file()


def _stereo_source(
    path: Path,
    *,
    duration_seconds: float,
    left: float = 0.10,
    right: float = -0.05,
) -> Path:
    return write_pcm16_fixture(
        path,
        duration_seconds=duration_seconds,
        sample_rate_hz=48_000,
        channels=2,
        sample_at=lambda _frame, channel: left if channel == 0 else right,
    )


def _read_pcm24(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as source:
        assert source.getsampwidth() == 3
        channels = source.getnchannels()
        payload = source.readframes(source.getnframes())
    triples = np.frombuffer(payload, dtype=np.uint8).reshape((-1, 3))
    extended = np.empty((triples.shape[0], 4), dtype=np.uint8)
    extended[:, :3] = triples
    extended[:, 3] = np.where((triples[:, 2] & 0x80) != 0, 0xFF, 0x00)
    signed = extended.reshape(-1).view("<i4").reshape((-1, channels))
    return signed.astype(np.float64) / 8_388_607.0
