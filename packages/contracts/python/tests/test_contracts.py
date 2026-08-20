from __future__ import annotations

from pathlib import Path

import pytest
from ampersand_contracts import (
    AnalysisManifest,
    AssetKind,
    AssetManifest,
    DependencyManifest,
    GainEnvelope,
    GainPoint,
    JobStatus,
    JobStep,
    LoudnessMeasurement,
    ManifestAdmissionState,
    MediaProbe,
    ModelManifest,
    OutputArtifact,
    OutputManifest,
    ProcessingPlan,
    ProcessingRegion,
    ProcessingReport,
    Production,
    ProductionRun,
    RecipeVersion,
    RunStatus,
    SemanticMap,
    SemanticRegion,
    WaveformLevel,
    WaveformPeaks,
    canonical_json_bytes,
)
from ampersand_contracts.schema_export import EXPORTED_MODELS, export_json_schemas
from pydantic import BaseModel, ValidationError

SHA = "a" * 64


def test_every_required_contract_round_trips_with_a_version() -> None:
    fixtures = _contract_fixtures()
    required = {
        AssetManifest,
        MediaProbe,
        Production,
        ProductionRun,
        JobStep,
        RecipeVersion,
        SemanticMap,
        SemanticRegion,
        ProcessingPlan,
        ProcessingRegion,
        GainEnvelope,
        ProcessingReport,
        OutputManifest,
        ModelManifest,
    }
    assert required <= {type(model) for model in fixtures}

    for model in fixtures:
        restored = type(model).model_validate_json(canonical_json_bytes(model))
        assert restored == model
        expected_version = "1.1.0" if isinstance(restored, (SemanticMap, SemanticRegion)) else "1.0.0"
        assert restored.schema_version == expected_version


def test_contracts_reject_provider_native_extra_fields() -> None:
    payload = _semantic_region().model_dump(mode="json")
    payload["provider_native_blob"] = {"speaker": "vendor-specific"}
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        SemanticRegion.model_validate(payload)


def test_timeline_contracts_enforce_half_open_nonempty_intervals() -> None:
    payload = _semantic_region().model_dump(mode="json")
    payload["end_us"] = payload["start_us"]
    with pytest.raises(ValidationError, match="half-open"):
        SemanticRegion.model_validate(payload)


def test_gain_envelope_requires_exact_timeline_span() -> None:
    with pytest.raises(ValidationError, match=r"span \[0, duration_us\]"):
        GainEnvelope(
            gain_envelope_id="gain-envelope:test",
            run_id="run:test",
            duration_us=1_000_000,
            purpose="unity_baseline",
            points=(GainPoint(at_us=10, gain_db=0), GainPoint(at_us=1_000_000, gain_db=0)),
        )


def test_canonical_serialization_is_key_order_independent() -> None:
    first = JobStep(
        step_id="step:test",
        run_id="run:test",
        step_key="test-step",
        implementation_version="engine:1.0.0",
        input_manifest_hash=SHA,
        idempotency_key=SHA,
        status=JobStatus.SUCCEEDED,
        metrics={"z": 1, "a": 2},
    )
    second = first.model_copy(update={"metrics": {"a": 2, "z": 1}})
    assert canonical_json_bytes(first) == canonical_json_bytes(second)


def test_schema_export_covers_every_public_contract(tmp_path: Path) -> None:
    written = export_json_schemas(tmp_path)
    assert len(written) == len(EXPORTED_MODELS)
    assert all(path.read_text(encoding="utf-8").endswith("\n") for path in written)


def _contract_fixtures() -> tuple[BaseModel, ...]:
    loudness = LoudnessMeasurement(
        integrated_lufs=-16,
        true_peak_dbtp=-1.2,
        loudness_range_lu=4,
        threshold_lufs=-26,
        measurement_backend="test",
        backend_version="test:1",
    )
    region = _semantic_region()
    processing_region = ProcessingRegion(
        processing_region_id="processing-region:test",
        start_us=0,
        end_us=1_000_000,
        action="protect",
        processor_id="processor:no-op",
        confidence=1,
        reason="Unknown test content remains protected.",
    )
    source = AssetManifest(
        asset_id="asset:source",
        kind=AssetKind.SOURCE,
        uri=f"sha256://{SHA}",
        sha256=SHA,
        size_bytes=1,
        mime_type="audio/wav",
        filename="fixture.wav",
    )
    probe = MediaProbe(
        probe_id="probe:test",
        source_asset_id=source.asset_id,
        format_name="wav",
        codec_name="pcm_s16le",
        duration_us=1_000_000,
        sample_rate_hz=48_000,
        channels=1,
        ffprobe_version="ffprobe:6.1",
    )
    production = Production(
        production_id="production:test",
        workspace_id="workspace:local",
        title="Fixture",
        source_asset_id=source.asset_id,
        recipe_version_id="recipe:test:1.0.0",
        current_run_id="run:test",
        status=RunStatus.SUCCEEDED,
    )
    run = ProductionRun(
        run_id="run:test",
        production_id=production.production_id,
        recipe_version_id=production.recipe_version_id,
        engine_build_id="engine:1.0.0",
        idempotency_key=SHA,
        status=RunStatus.SUCCEEDED,
        step_ids=("step:test",),
    )
    step = JobStep(
        step_id="step:test",
        run_id=run.run_id,
        step_key="validate-probe",
        implementation_version="engine:1.0.0",
        input_manifest_hash=SHA,
        idempotency_key=SHA,
        status=JobStatus.SUCCEEDED,
    )
    recipe = RecipeVersion(
        recipe_version_id="recipe:test:1.0.0",
        slug="recipe-test",
        recipe_version="1.0.0",
        display_name="Test recipe",
        description="A deterministic contract-test recipe.",
        analysis_steps=("validate-probe",),
        processing_steps=("final-master",),
        target_integrated_lufs=-16,
        max_true_peak_dbtp=-1,
        target_loudness_range_lu=11,
        output_formats=("wav", "mp3"),
    )
    semantic_map = SemanticMap(
        semantic_map_id="semantic-map:test",
        source_asset_id=source.asset_id,
        duration_us=1_000_000,
        analysis_hop_us=1_000_000,
        regions=(region,),
    )
    plan = ProcessingPlan(
        processing_plan_id="processing-plan:test",
        run_id=run.run_id,
        recipe_version_id=recipe.recipe_version_id,
        semantic_map_id=semantic_map.semantic_map_id,
        duration_us=1_000_000,
        regions=(processing_region,),
        global_steps=("final-master",),
    )
    envelope = GainEnvelope(
        gain_envelope_id="gain-envelope:test",
        run_id=run.run_id,
        duration_us=1_000_000,
        purpose="unity_baseline",
        points=(GainPoint(at_us=0, gain_db=0), GainPoint(at_us=1_000_000, gain_db=0)),
    )
    waveform = WaveformPeaks(
        waveform_id="waveform:test",
        source_asset_id=source.asset_id,
        sample_rate_hz=48_000,
        channels=1,
        duration_us=1_000_000,
        levels=(WaveformLevel(samples_per_window=960, windows=(((-0.5, 0.5),),)),),
    )
    analysis = AnalysisManifest(
        analysis_manifest_id="analysis:test",
        run_id=run.run_id,
        source_asset_id=source.asset_id,
        media_probe_id=probe.probe_id,
        waveform_id=waveform.waveform_id,
        loudness_before=loudness,
    )
    artifact = OutputArtifact(
        artifact_id="asset:master-wav",
        kind=AssetKind.MASTER_WAV,
        relative_path="artifacts/master.wav",
        sha256=SHA,
        size_bytes=1,
        mime_type="audio/wav",
        duration_us=1_000_000,
        validation_status="valid",
    )
    output = OutputManifest(
        output_manifest_id="output:test",
        run_id=run.run_id,
        source_asset_id=source.asset_id,
        recipe_version_id=recipe.recipe_version_id,
        artifacts=(artifact,),
        loudness_after=loudness,
        target_integrated_lufs=-16,
        max_true_peak_dbtp=-1,
        validation_status="valid",
    )
    report = ProcessingReport(
        processing_report_id="report:test",
        production_id=production.production_id,
        run_id=run.run_id,
        source_asset_id=source.asset_id,
        recipe_version_id=recipe.recipe_version_id,
        engine_build_id="engine:1.0.0",
        status=RunStatus.SUCCEEDED,
        loudness_before=loudness,
        loudness_after=loudness,
        step_ids=(step.step_id,),
        decisions=("No-op protected baseline.",),
        artifact_sha256={"master_wav": SHA},
        privacy_summary="Local synthetic fixture only.",
        reproducibility_summary="Exact versions and checksums are recorded.",
    )
    model = ModelManifest(
        model_manifest_id="model:test:1.0.0",
        model_name="Test model",
        model_version="1.0.0",
        source_url="https://example.invalid/model",
        artifact_sha256=SHA,
        code_license="MIT",
        checkpoint_license="MIT",
        training_data_terms="Synthetic test manifest only.",
        admission_state=ManifestAdmissionState.UNREVIEWED,
    )
    dependency = DependencyManifest(
        dependency_manifest_id="dependency:test",
        dependency_name="Test dependency",
        dependency_version="1.0.0",
        source_url="https://example.invalid/dependency",
        artifact_sha256=SHA,
        code_license="MIT",
        admission_state=ManifestAdmissionState.UNREVIEWED,
        scope="development",
        transitive_native_review="No native dependencies in the synthetic contract fixture.",
    )
    return (
        source,
        probe,
        production,
        run,
        step,
        recipe,
        region,
        semantic_map,
        processing_region,
        plan,
        envelope,
        loudness,
        waveform,
        analysis,
        artifact,
        output,
        report,
        model,
        dependency,
    )


def _semantic_region() -> SemanticRegion:
    return SemanticRegion(
        region_id="semantic-region:test",
        start_us=0,
        end_us=1_000_000,
        content_label="unknown",
        confidence=0,
        protected=True,
    )
