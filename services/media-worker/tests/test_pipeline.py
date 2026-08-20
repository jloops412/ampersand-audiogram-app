from __future__ import annotations

import json
from pathlib import Path

import pytest
from ampersand_contracts import (
    OutputManifest,
    ProcessingReport,
    ProviderNativeArtifactManifest,
    read_manifest,
    read_semantic_map,
)
from ampersand_engine.errors import EngineError, InvalidMedia
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
    assert output.validation_status == "valid"
    assert abs(output.loudness_after.integrated_lufs - output.target_integrated_lufs) <= 0.35
    assert output.loudness_after.true_peak_dbtp <= output.max_true_peak_dbtp + 0.20
    assert report.external_api_cost_usd == 0
    assert "no network" in report.privacy_summary.lower()
    assert {artifact.kind.value for artifact in output.artifacts} == {"master_wav", "master_mp3"}
    assert semantic_map.schema_version == "1.1.0"
    assert semantic_map.regions[0].start_us == 0
    assert semantic_map.regions[-1].end_us == semantic_map.duration_us
    assert {"speech_probability", "silence_probability", "momentary_loudness", "true_peak"} <= {
        observation.kind.value for observation in semantic_map.observations
    }
    assert semantic_map.provider_native_artifact_ids
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
    assert "not the adaptive leveler" in warning
    assert "denoise" in warning


def _json_artifacts(directory: Path) -> dict[str, bytes]:
    return {str(path.relative_to(directory)): path.read_bytes() for path in sorted(directory.rglob("*.json"))}
