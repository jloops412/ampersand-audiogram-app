from __future__ import annotations

from pathlib import Path

import pytest
from ampersand_contracts import (
    AdaptiveLevelerSettings,
    AnalysisManifest,
    AssetKind,
    AssetManifest,
    DependencyManifest,
    ExportSettings,
    FixtureAssetManifest,
    FixtureConsentStatus,
    FixtureCorpusManifest,
    FixturePartition,
    FixtureRegion,
    FixtureRelationship,
    FixtureRightsStatus,
    FixtureSourceKind,
    FixtureTransform,
    GainEnvelope,
    GainPoint,
    JobStatus,
    JobStep,
    LevelerStatistics,
    LoudnessMeasurement,
    ManifestAdmissionState,
    MasteringSettings,
    MediaProbe,
    ModelManifest,
    OutputArtifact,
    OutputManifest,
    ProcessingPlan,
    ProcessingRegion,
    ProcessingReport,
    ProcessingRouteDecision,
    ProcessingRouteOverride,
    ProcessingRouterReport,
    ProcessingRouterSettings,
    Production,
    ProductionRun,
    ProductionSettings,
    ProductionSettingsOverride,
    RecipeVersion,
    ResolvedProductionSettings,
    RunStatus,
    SemanticMap,
    SemanticRegion,
    SignificantGainCorrection,
    SpeakerLevelStatistics,
    StudioTemplate,
    StudioTemplateVersion,
    WaveformLevel,
    WaveformPeaks,
    canonical_json_bytes,
    manifest_sha256,
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
        MasteringSettings,
        ExportSettings,
        ProductionSettings,
        ProductionSettingsOverride,
        StudioTemplate,
        StudioTemplateVersion,
        ResolvedProductionSettings,
        FixtureRegion,
        FixtureTransform,
        FixtureAssetManifest,
        FixtureCorpusManifest,
        AdaptiveLevelerSettings,
        SpeakerLevelStatistics,
        SignificantGainCorrection,
        LevelerStatistics,
        SemanticMap,
        SemanticRegion,
        ProcessingPlan,
        ProcessingRegion,
        ProcessingRouterSettings,
        ProcessingRouteOverride,
        ProcessingRouteDecision,
        ProcessingRouterReport,
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


def test_processing_plans_require_ordered_contiguous_full_coverage() -> None:
    with pytest.raises(ValidationError, match="ordered, contiguous"):
        ProcessingPlan(
            processing_plan_id="processing-plan:gapped",
            run_id="run:gapped",
            recipe_version_id="recipe:gapped:1.0.0",
            semantic_map_id="semantic-map:gapped",
            duration_us=1_000_000,
            regions=(
                ProcessingRegion(
                    processing_region_id="processing-region:gapped",
                    start_us=100_000,
                    end_us=1_000_000,
                    action="protect",
                    processor_id="processor:no-op-v0",
                    confidence=1,
                    reason="A deliberately gapped contract fixture.",
                ),
            ),
            global_steps=("final-master",),
        )


def test_gain_envelope_requires_exact_timeline_span() -> None:
    with pytest.raises(ValidationError, match=r"span \[0, duration_us\]"):
        GainEnvelope(
            gain_envelope_id="gain-envelope:test",
            run_id="run:test",
            duration_us=1_000_000,
            purpose="unity_baseline",
            points=(GainPoint(at_us=10, gain_db=0), GainPoint(at_us=1_000_000, gain_db=0)),
        )


def test_leveler_settings_reject_reversed_target_range() -> None:
    with pytest.raises(ValidationError, match="cannot exceed"):
        AdaptiveLevelerSettings(
            settings_id="leveler-settings:test",
            algorithm_version="0.1.0",
            target_speech_min_lufs=-18,
            target_speech_max_lufs=-30,
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
    settings = ProductionSettings(
        mastering=MasteringSettings(
            target_integrated_lufs=-16,
            max_true_peak_dbtp=-1,
            target_loudness_range_lu=11,
        ),
        export=ExportSettings(),
    )
    settings_sha = manifest_sha256(settings)
    settings_override = ProductionSettingsOverride(target_integrated_lufs=-18)
    template = StudioTemplate(
        template_id="template:test",
        workspace_id="workspace:local",
        name="Test template",
        current_version_id="template-version:test:1",
    )
    template_version = StudioTemplateVersion(
        template_version_id=template.current_version_id,
        template_id=template.template_id,
        version=1,
        recipe_version_id=production.recipe_version_id,
        settings=settings,
        settings_sha256=settings_sha,
        change_summary="Initial immutable contract fixture.",
    )
    resolved_settings = ResolvedProductionSettings(
        resolved_settings_id="resolved-settings:test",
        recipe_version_id=production.recipe_version_id,
        intent="podcast",
        template_version_id=template_version.template_version_id,
        settings=settings,
        settings_sha256=settings_sha,
        field_provenance={
            "mastering.target_integrated_lufs": "template",
            "mastering.max_true_peak_dbtp": "template",
            "mastering.target_loudness_range_lu": "template",
            "export.wav": "template",
            "export.mp3": "template",
            "export.mp3_bitrate_kbps": "template",
        },
    )
    run = ProductionRun(
        run_id="run:test",
        production_id=production.production_id,
        recipe_version_id=production.recipe_version_id,
        resolved_settings_id=resolved_settings.resolved_settings_id,
        resolved_settings_sha256=resolved_settings.settings_sha256,
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
    fixture_region = FixtureRegion(
        fixture_region_id="fixture-region:test:0",
        start_us=0,
        end_us=1_000_000,
        expected_role="speech",
        speaker_label="speaker:synthetic-test",
        target_relative_level_db=0,
        notes="Synthetic voice-shaped contract control.",
    )
    fixture_transform = FixtureTransform(
        transform_id="transform:test-noise",
        family="stationary-noise",
        implementation_version="0.1.0",
        seed=42,
        parameters={"nominal_snr_db": 12.0},
    )
    fixture_asset = FixtureAssetManifest(
        fixture_id="fixture:test-clean",
        corpus_version="0.1.0",
        partition=FixturePartition.DEVELOPMENT,
        visibility="development_visible",
        filename="fixture-test-clean.wav",
        sha256=SHA,
        size_bytes=1,
        duration_us=1_000_000,
        sample_rate_hz=48_000,
        channels=1,
        sample_width_bits=16,
        source_kind=FixtureSourceKind.SYNTHETIC_CONTROL,
        rights_status=FixtureRightsStatus.MATHEMATICAL_GENERATION,
        consent_status=FixtureConsentStatus.NOT_APPLICABLE_SYNTHETIC,
        contains_personal_data=False,
        contains_customer_media=False,
        contains_copyrighted_music=False,
        session_group_id="session:synthetic-test",
        speaker_group_ids=("speaker:synthetic-test",),
        relationship=FixtureRelationship.CLEAN_CONTROL,
        regions=(fixture_region,),
        generator_id="generator:synthetic-test",
        generator_version="0.1.0",
        generation_command=("generate", "<output>"),
        permitted_environments=("environment:local-test",),
        permitted_processor_classes=("processor-class:test",),
        retention_class="retention:regenerable",
        deletion_policy="Regenerate from source code after deletion.",
    )
    fixture_corpus = FixtureCorpusManifest(
        corpus_id="fixture-corpus:test",
        corpus_version="0.1.0",
        generator_id="generator:synthetic-test",
        generator_version="0.1.0",
        fixtures=(fixture_asset,),
        partitions_present=(FixturePartition.DEVELOPMENT,),
        prohibited_sources=("hosted_processor_service", "hosted_processor_output", "production_customer_media"),
        governance_summary="Synthetic contract fixture only; no recorded or customer media.",
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
    router_settings = ProcessingRouterSettings(
        settings_id="router-settings:test",
        algorithm_version="0.1.0",
    )
    route_override = ProcessingRouteOverride(
        override_id="route-override:test",
        start_us=0,
        end_us=1_000_000,
        action="protect",
        reason="The test operator preserves this synthetic interval.",
    )
    route_decision = ProcessingRouteDecision(
        decision_id="route-decision:test",
        processing_region_id=processing_region.processing_region_id,
        semantic_region_ids=(region.region_id,),
        action=processing_region.action,
        processor_id=processing_region.processor_id,
        reason_code="router:protect-test",
        reason=processing_region.reason,
        confidence=processing_region.confidence,
    )
    router_report = ProcessingRouterReport(
        processing_router_report_id="router-report:test",
        run_id=run.run_id,
        semantic_map_id=semantic_map.semantic_map_id,
        recipe_version_id=recipe.recipe_version_id,
        settings_id=router_settings.settings_id,
        settings_sha256=manifest_sha256(router_settings),
        algorithm_version="0.1.0",
        processing_plan_id=plan.processing_plan_id,
        processing_plan_sha256=manifest_sha256(plan),
        decisions=(route_decision,),
        override_ids=(route_override.override_id,),
        protected_region_count=1,
        bypassed_region_count=0,
        deterministic_filter_region_count=0,
        denoise_region_count=0,
        leveler_region_count=0,
    )
    envelope = GainEnvelope(
        gain_envelope_id="gain-envelope:test",
        run_id=run.run_id,
        duration_us=1_000_000,
        purpose="unity_baseline",
        points=(GainPoint(at_us=0, gain_db=0), GainPoint(at_us=1_000_000, gain_db=0)),
    )
    leveler_settings = AdaptiveLevelerSettings(
        settings_id="leveler-settings:test",
        algorithm_version="0.1.0",
    )
    speaker_statistics = SpeakerLevelStatistics(
        speaker_label="speaker:test",
        observation_count=1,
        eligible_duration_us=1_000_000,
        robust_speech_level_lufs=-24,
        relative_offset_db=2,
        used_global_fallback=False,
    )
    significant_correction = SignificantGainCorrection(
        correction_id="gain-correction:test",
        start_us=0,
        end_us=1_000_000,
        peak_gain_db=2,
        reason="Raised reliable test speech below the comfort band.",
    )
    leveler_statistics = LevelerStatistics(
        leveler_statistics_id="leveler-statistics:test",
        run_id=run.run_id,
        semantic_map_id=semantic_map.semantic_map_id,
        settings_id=leveler_settings.settings_id,
        settings_sha256=SHA,
        algorithm_version="0.1.0",
        activation_mode="shadow",
        target_speech_level_lufs=-22,
        comfort_band_low_lufs=-24,
        comfort_band_high_lufs=-20,
        total_duration_us=1_000_000,
        eligible_duration_us=1_000_000,
        changed_duration_us=1_000_000,
        eligible_region_count=1,
        protected_region_count=0,
        changed_region_count=1,
        gain_min_db=2,
        gain_mean_db=2,
        gain_max_db=2,
        maximum_gain_slope_db_per_second=0,
        maximum_gain_acceleration_db_per_second2=0,
        peak_limited_region_count=0,
        speaker_statistics=(speaker_statistics,),
        significant_corrections=(significant_correction,),
        reasoning=("Contract fixture.",),
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
        resolved_settings_id=resolved_settings.resolved_settings_id,
        resolved_settings_sha256=resolved_settings.settings_sha256,
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
        resolved_settings_id=resolved_settings.resolved_settings_id,
        resolved_settings_sha256=resolved_settings.settings_sha256,
        engine_build_id="engine:1.0.0",
        status=RunStatus.SUCCEEDED,
        loudness_before=loudness,
        loudness_after=loudness,
        gain_envelope_id=envelope.gain_envelope_id,
        leveler_statistics_id=leveler_statistics.leveler_statistics_id,
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
        settings.mastering,
        settings.export,
        settings,
        settings_override,
        template,
        template_version,
        resolved_settings,
        run,
        step,
        recipe,
        fixture_region,
        fixture_transform,
        fixture_asset,
        fixture_corpus,
        region,
        semantic_map,
        processing_region,
        plan,
        router_settings,
        route_override,
        route_decision,
        router_report,
        envelope,
        leveler_settings,
        speaker_statistics,
        significant_correction,
        leveler_statistics,
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
