from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from ampersand_contracts import (
    AdaptiveLevelerSettings,
    AudiogramSettings,
    CleanupSettings,
    ExportSettings,
    GainEnvelope,
    JobStep,
    LevelerStatistics,
    MasteringSettings,
    OutputManifest,
    OutputMetadataSettings,
    ProcessingPlan,
    ProcessingReport,
    ProcessingRouterReport,
    ProcessingRouterSettings,
    ProductionSettings,
    ProviderNativeArtifactManifest,
    read_manifest,
    read_semantic_map,
)
from ampersand_engine.errors import EngineError, InvalidMedia
from ampersand_engine.ffmpeg import FFmpegTools, render_audiogram_mp4
from ampersand_engine.hashing import sha256_file
from ampersand_engine.pipeline import process_source
from ampersand_test_fixtures import generate_spoken_word_fixture


@pytest.fixture
def synthetic_source(tmp_path: Path) -> Path:
    return generate_spoken_word_fixture(tmp_path / "synthetic-spoken-word.wav")


def test_pipeline_emits_valid_deterministic_manifests_and_media(
    tmp_path: Path,
    synthetic_source: Path,
) -> None:
    source_before = sha256_file(synthetic_source)
    first = process_source(synthetic_source, tmp_path / "run-one")
    second = process_source(synthetic_source, tmp_path / "run-two")

    assert sha256_file(synthetic_source) == source_before
    assert first.production_id == second.production_id
    assert first.run_id == second.run_id
    assert first.wav_sha256 == second.wav_sha256
    assert first.mp3_sha256 == second.mp3_sha256

    first_json = _json_artifacts(first.output_directory)
    second_json = _json_artifacts(second.output_directory)
    assert first_json.keys() == second_json.keys()
    for relative_path in first_json:
        assert first_json[relative_path] == second_json[relative_path], relative_path
    assert (first.output_directory / "semantic-map-debug.html").read_bytes() == (
        second.output_directory / "semantic-map-debug.html"
    ).read_bytes()

    output = read_manifest(first.output_directory / "output-manifest.json", OutputManifest)
    report = read_manifest(first.output_directory / "processing-report.json", ProcessingReport)
    semantic_map = read_semantic_map(first.output_directory / "semantic-map-v0.json")
    leveler_settings = read_manifest(first.output_directory / "leveler-settings.json", AdaptiveLevelerSettings)
    gain_envelope = read_manifest(first.output_directory / "gain-envelope.json", GainEnvelope)
    leveler_statistics = read_manifest(first.output_directory / "leveler-statistics.json", LevelerStatistics)
    router_settings = read_manifest(first.output_directory / "router-settings.json", ProcessingRouterSettings)
    processing_plan = read_manifest(first.output_directory / "processing-plan.json", ProcessingPlan)
    router_report = read_manifest(
        first.output_directory / "processing-router-report.json",
        ProcessingRouterReport,
    )
    router_step = read_manifest(first.output_directory / "steps/processing-router-v0-shadow.json", JobStep)
    leveler_step = read_manifest(first.output_directory / "steps/adaptive-leveler-shadow.json", JobStep)
    assert output.validation_status == "valid"
    assert abs(output.loudness_after.integrated_lufs - output.target_integrated_lufs) <= 0.35
    assert output.loudness_after.true_peak_dbtp <= output.max_true_peak_dbtp + 0.20
    assert report.external_api_cost_usd == 0
    assert report.gain_envelope_id == gain_envelope.gain_envelope_id
    assert report.leveler_statistics_id == leveler_statistics.leveler_statistics_id
    assert "no network" in report.privacy_summary.lower()
    assert {artifact.kind.value for artifact in output.artifacts} == {"master_wav", "master_mp3"}
    assert semantic_map.schema_version == "1.1.0"
    assert semantic_map.regions[0].start_us == 0
    assert semantic_map.regions[-1].end_us == semantic_map.duration_us
    assert {"speech_probability", "silence_probability", "momentary_loudness", "true_peak"} <= {
        observation.kind.value for observation in semantic_map.observations
    }
    assert semantic_map.provider_native_artifact_ids
    assert leveler_settings.activation_mode == "shadow"
    assert leveler_statistics.activation_mode == "shadow"
    assert leveler_statistics.settings_sha256 == report.artifact_sha256["leveler_settings"]
    assert router_report.settings_sha256 == report.artifact_sha256["router_settings"]
    assert router_report.processing_plan_sha256 == report.artifact_sha256["processing_plan"]
    assert report.artifact_sha256["processing_router_report"]
    assert processing_plan.processing_plan_id == router_report.processing_plan_id
    assert processing_plan.regions[0].start_us == 0
    assert processing_plan.regions[-1].end_us == processing_plan.duration_us
    assert all(region.planning_only for region in processing_plan.regions)
    assert router_settings.planning_mode == "shadow"
    assert router_report.planning_only
    assert router_report.production_audio_changed is False
    assert router_report.denoise_region_count == 0
    assert leveler_statistics.eligible_region_count > 0
    assert leveler_statistics.changed_region_count > 0
    assert leveler_statistics.maximum_gain_slope_db_per_second <= leveler_settings.max_gain_slope_db_per_second
    assert (
        leveler_statistics.maximum_gain_acceleration_db_per_second2
        <= leveler_settings.max_gain_acceleration_db_per_second2
    )
    assert leveler_step.step_key == "adaptive-leveler-shadow"
    assert leveler_step.metrics["applied_to_audio"] is False
    assert router_step.step_key == "processing-router-v0-shadow"
    assert router_step.metrics["applied_to_audio"] is False
    assert (first.output_directory / "loudness-before.json").is_file()
    assert (first.output_directory / "loudness-after.json").is_file()
    assert {provenance.provider_id for provenance in semantic_map.provenance_sources} == {
        "provider:ampersand-energy-vad",
        "provider:ffmpeg-ebur128",
    }
    assert (first.output_directory / "provider-native/ffmpeg-ebur128.json").is_file()
    assert (first.output_directory / "provider-native/ampersand-energy-vad-v0.json").is_file()
    provider_payloads = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted((first.output_directory / "provider-native").glob("*.json"))
    )
    assert str(synthetic_source) not in provider_payloads
    assert "authorization" not in provider_payloads.lower()
    for manifest_name in ("ffmpeg-ebur128.manifest.json", "ampersand-energy-vad-v0.manifest.json"):
        provider_manifest = read_manifest(
            first.output_directory / "provider-native" / manifest_name,
            ProviderNativeArtifactManifest,
        )
        assert sha256_file(first.output_directory / provider_manifest.relative_path) == provider_manifest.sha256


def test_pipeline_refuses_to_overwrite_existing_output(
    tmp_path: Path,
    synthetic_source: Path,
) -> None:
    output = tmp_path / "already-there"
    output.mkdir()
    with pytest.raises(EngineError, match="will not overwrite"):
        process_source(synthetic_source, output)


def test_invalid_media_leaves_no_partial_output(tmp_path: Path) -> None:
    source = tmp_path / "not-audio.txt"
    source.write_text("This is not media.", encoding="utf-8")
    output = tmp_path / "should-not-exist"
    with pytest.raises(InvalidMedia):
        process_source(source, output)
    assert not output.exists()


def test_report_makes_baseline_limitations_explicit(tmp_path: Path, synthetic_source: Path) -> None:
    result = process_source(synthetic_source, tmp_path / "reported")
    payload = json.loads((result.output_directory / "processing-report.json").read_text(encoding="utf-8"))
    warning = " ".join(payload["warnings"]).lower()
    assert "shadow-only" in warning
    assert "human listening" in warning
    assert "denoise" in warning


def test_pipeline_applies_cleanup_metadata_and_renders_audiogram(
    tmp_path: Path,
    synthetic_source: Path,
) -> None:
    settings = ProductionSettings(
        cleanup=CleanupSettings(
            noise_reduction="light",
            rumble_filter=True,
            hum_reduction="60hz",
            declip=True,
            noise_gate="light",
            deesser="light",
            voice_enhancement="natural",
            compression="gentle",
        ),
        mastering=MasteringSettings(
            target_integrated_lufs=-16,
            max_true_peak_dbtp=-1,
            target_loudness_range_lu=11,
        ),
        metadata=OutputMetadataSettings(
            artist="Ampersand Test Artist",
            album="Ampersand Test Series",
            genre="Spoken Word",
            date="2026-08-20",
            track_number="7",
        ),
        audiogram=AudiogramSettings(
            enabled=True,
            aspect_ratio="square",
            waveform_style="mirrored",
            background_mode="artwork",
            headline="Test audiogram",
            subtitle="Independent renderer",
        ),
        export=ExportSettings(wav=True, mp3=True, mp3_bitrate_kbps=192),
    )
    artwork = tmp_path / "background.png"
    subprocess.run(
        [
            "ffmpeg",
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=c=0x203040:s=640x640",
            "-frames:v",
            "1",
            "-y",
            str(artwork),
        ],
        check=True,
    )
    result = process_source(
        synthetic_source,
        tmp_path / "audiogram-run",
        title="Tagged production",
        artwork=artwork,
        settings=settings,
        settings_source="run_override",
    )

    assert result.audiogram_sha256 is not None
    assert (result.output_directory / "artifacts/audiogram.mp4").is_file()
    output = read_manifest(result.output_directory / "output-manifest.json", OutputManifest)
    assert {artifact.kind.value for artifact in output.artifacts} == {
        "master_wav",
        "master_mp3",
        "audiogram_mp4",
    }
    cleanup_step = read_manifest(result.output_directory / "steps/deterministic-cleanup-v1.json", JobStep)
    audiogram_step = read_manifest(result.output_directory / "steps/render-audiogram.json", JobStep)
    assert cleanup_step.metrics["applied_to_audio"] is True
    assert audiogram_step.status.value == "succeeded"
    report = read_manifest(result.output_directory / "processing-report.json", ProcessingReport)
    cleanup_decision = next(decision for decision in report.decisions if "cleanup chain" in decision)
    assert "hum 60hz" in cleanup_decision
    assert "de-esser light" in cleanup_decision
    assert "voice enhancement natural" in cleanup_decision

    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format_tags=title,artist,album,genre,date,track",
            "-of",
            "json",
            str(result.output_directory / "artifacts/master.mp3"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    tags = json.loads(completed.stdout)["format"]["tags"]
    assert tags["title"] == "Tagged production"
    assert tags["artist"] == "Ampersand Test Artist"
    assert tags["album"] == "Ampersand Test Series"


def test_audiogram_renderer_loops_video_and_executes_rich_spec(
    tmp_path: Path,
    synthetic_source: Path,
) -> None:
    background = tmp_path / "background.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=s=640x360:r=24:d=0.4",
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-y",
            str(background),
        ],
        check=True,
    )
    output = tmp_path / "rich-audiogram.mp4"
    render_audiogram_mp4(
        synthetic_source,
        output,
        title="Rich renderer",
        metadata=OutputMetadataSettings(artist="Ampersand"),
        settings=AudiogramSettings(
            enabled=True,
            aspect_ratio="feed_portrait",
            waveform_style="dots",
            waveform_scale="log",
            waveform_position="bottom",
            waveform_width_percent=70,
            waveform_height_percent=20,
            waveform_opacity=0.65,
            background_mode="video",
            background_fit="contain",
            background_dim=0.2,
            text_align="left",
            headline_size_percent=6.0,
            subtitle_size_percent=3.0,
            subtitle="Video background",
            frame_rate=24,
            render_quality="draft",
        ),
        artwork=background,
        tools=FFmpegTools.discover(),
    )
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "stream=codec_type,width,height,r_frame_rate",
            "-of",
            "json",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    streams = json.loads(completed.stdout)["streams"]
    video = next(stream for stream in streams if stream["codec_type"] == "video")
    assert (video["width"], video["height"], video["r_frame_rate"]) == (1080, 1350, "24/1")
    assert any(stream["codec_type"] == "audio" for stream in streams)


def _json_artifacts(directory: Path) -> dict[str, bytes]:
    return {str(path.relative_to(directory)): path.read_bytes() for path in sorted(directory.rglob("*.json"))}
