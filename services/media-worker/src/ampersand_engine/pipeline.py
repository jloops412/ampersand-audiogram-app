from __future__ import annotations

import mimetypes
import os
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from ampersand_contracts import (
    AnalysisManifest,
    AssetKind,
    AssetManifest,
    GainEnvelope,
    GainPoint,
    JobStatus,
    JobStep,
    LoudnessMeasurement,
    OutputArtifact,
    OutputManifest,
    ProcessingPlan,
    ProcessingRegion,
    ProcessingReport,
    Production,
    ProductionRun,
    RunStatus,
    SemanticMap,
    SemanticRegion,
    manifest_sha256,
    write_manifest,
)

from . import __version__
from .errors import EngineError, OutputValidationError
from .ffmpeg import (
    FFmpegTools,
    canonicalize_audio,
    encode_master_mp3,
    measure_loudness,
    probe_media,
    render_master_wav,
    requires_canonical_audio,
)
from .hashing import sha256_file, sha256_text, stable_id
from .recipe_loader import load_recipe
from .waveform import generate_waveform_peaks

ENGINE_BUILD_ID = f"ampersand-media-worker:{__version__}"
ProgressCallback = Callable[[str], None]
StepMetrics = dict[str, str | int | float | bool | None]
StepDefinition = tuple[str, str, JobStatus, tuple[str, ...], StepMetrics]


@dataclass(frozen=True)
class PipelineResult:
    output_directory: Path
    production_id: str
    run_id: str
    source_sha256: str
    wav_sha256: str
    mp3_sha256: str


def process_source(
    source: Path,
    output_directory: Path,
    *,
    recipe_slug: str = "smart-spoken-word-v0",
    title: str | None = None,
    progress: ProgressCallback | None = None,
) -> PipelineResult:
    source_path = source.expanduser().resolve(strict=True)
    output_path = output_directory.expanduser().resolve(strict=False)
    if not source_path.is_file():
        raise EngineError("The source must be a local regular file.")
    if source_path.stat().st_size <= 0:
        raise EngineError("The source file is empty.")
    if output_path.exists():
        raise EngineError("The output directory already exists; Ampersand will not overwrite it.")
    if output_path == source_path:
        raise EngineError("The output directory cannot replace the immutable source.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tools = FFmpegTools.discover()
    recipe = load_recipe(recipe_slug)
    source_sha = sha256_file(source_path)
    recipe_sha = manifest_sha256(recipe)
    run_fingerprint = sha256_text(
        "|".join((source_sha, recipe_sha, ENGINE_BUILD_ID, tools.ffmpeg_version, tools.ffprobe_version))
    )
    production_id = stable_id("production", sha256_text(f"{source_sha}|{recipe.recipe_version_id}"))
    run_id = stable_id("run", run_fingerprint)
    source_asset_id = stable_id("asset", source_sha)
    probe_id = stable_id("probe", run_fingerprint)
    waveform_id = stable_id("waveform", run_fingerprint)
    semantic_map_id = stable_id("semantic-map", run_fingerprint)
    processing_plan_id = stable_id("processing-plan", run_fingerprint)
    gain_envelope_id = stable_id("gain-envelope", run_fingerprint)
    analysis_manifest_id = stable_id("analysis", run_fingerprint)
    output_manifest_id = stable_id("output", run_fingerprint)
    processing_report_id = stable_id("report", run_fingerprint)

    temporary_prefix = f".{output_path.name}.building-"
    with tempfile.TemporaryDirectory(prefix=temporary_prefix, dir=output_path.parent) as temporary:
        stage = Path(temporary)
        artifacts = stage / "artifacts"
        steps_directory = stage / "steps"

        _notify(progress, "validate/probe")
        source_manifest = AssetManifest(
            asset_id=source_asset_id,
            kind=AssetKind.SOURCE,
            uri=f"sha256://{source_sha}",
            sha256=source_sha,
            size_bytes=source_path.stat().st_size,
            mime_type=mimetypes.guess_type(source_path.name)[0] or "application/octet-stream",
            filename=source_path.name[:255],
            retention_class="local_fixture",
            provenance={
                "ingest_mode": "local_cli",
                "immutable": True,
                "network_used": False,
            },
        )
        write_manifest(stage / "source-manifest.json", source_manifest)
        probe = probe_media(source_path, source_asset_id=source_asset_id, probe_id=probe_id, tools=tools)
        write_manifest(stage / "probe.json", probe)

        _notify(progress, "canonicalize if needed")
        analysis_input = source_path
        analysis_asset = source_manifest
        canonical_was_created = requires_canonical_audio(probe)
        if canonical_was_created:
            canonical_path = artifacts / "canonical.wav"
            canonicalize_audio(source_path, canonical_path, tools)
            canonical_sha = sha256_file(canonical_path)
            canonical_step_id = _step_id(run_fingerprint, "canonicalize-if-needed")
            analysis_asset = AssetManifest(
                asset_id=stable_id("asset", canonical_sha),
                kind=AssetKind.CANONICAL_AUDIO,
                uri=f"artifact://{run_id}/canonical.wav",
                sha256=canonical_sha,
                size_bytes=canonical_path.stat().st_size,
                mime_type="audio/wav",
                filename="canonical.wav",
                source_asset_id=source_asset_id,
                created_by_step_id=canonical_step_id,
                retention_class="local_derived",
                provenance={
                    "engine_build_id": ENGINE_BUILD_ID,
                    "ffmpeg_version": tools.ffmpeg_version,
                    "sample_rate_hz": 48_000,
                    "sample_format": "float32",
                },
            )
            write_manifest(stage / "canonical-manifest.json", analysis_asset)
            analysis_input = canonical_path

        _notify(progress, "measure and build waveform")
        loudness_before = measure_loudness(analysis_input, tools)
        waveform = generate_waveform_peaks(
            analysis_input,
            waveform_id=waveform_id,
            source_asset_id=source_asset_id,
            channels=probe.channels,
            duration_us=probe.duration_us,
            tools=tools,
        )
        write_manifest(stage / "waveform-peaks.json", waveform)
        analysis = AnalysisManifest(
            analysis_manifest_id=analysis_manifest_id,
            run_id=run_id,
            source_asset_id=source_asset_id,
            media_probe_id=probe_id,
            waveform_id=waveform_id,
            loudness_before=loudness_before,
            warnings=(
                "Baseline semantic analysis does not yet include VAD, ASR, diarization, or defect classification.",
            ),
        )
        write_manifest(stage / "analysis.json", analysis)

        _notify(progress, "build protected semantic map and plan")
        semantic_region = SemanticRegion(
            region_id=stable_id("semantic-region", run_fingerprint),
            start_us=0,
            end_us=probe.duration_us,
            content_label="unknown",
            confidence=0.0,
            protected=True,
            observations={
                "baseline": True,
                "reason": "No admitted content classifier is active in issue 21.",
            },
        )
        semantic_map = SemanticMap(
            semantic_map_id=semantic_map_id,
            source_asset_id=source_asset_id,
            duration_us=probe.duration_us,
            regions=(semantic_region,),
            warnings=("Unknown content is protected and receives no enhancement.",),
        )
        write_manifest(stage / "semantic-map.json", semantic_map)

        processing_region = ProcessingRegion(
            processing_region_id=stable_id("processing-region", run_fingerprint),
            start_us=0,
            end_us=probe.duration_us,
            action="protect",
            processor_id="processor:no-op-v0",
            confidence=1.0,
            reason="No admitted regional processor is active; preserve source content before final mastering.",
            parameters={"wet_mix": 0.0},
            transition_us=0,
            source="recipe",
        )
        processing_plan = ProcessingPlan(
            processing_plan_id=processing_plan_id,
            run_id=run_id,
            recipe_version_id=recipe.recipe_version_id,
            semantic_map_id=semantic_map_id,
            duration_us=probe.duration_us,
            regions=(processing_region,),
            global_steps=("two-pass-loudness-master", "output-validation"),
        )
        write_manifest(stage / "processing-plan.json", processing_plan)

        gain_envelope = GainEnvelope(
            gain_envelope_id=gain_envelope_id,
            run_id=run_id,
            duration_us=probe.duration_us,
            points=(
                GainPoint(at_us=0, gain_db=0.0),
                GainPoint(at_us=probe.duration_us, gain_db=0.0),
            ),
            purpose="unity_baseline",
        )
        write_manifest(stage / "gain-envelope.json", gain_envelope)
        write_manifest(stage / "recipe.json", recipe)

        _notify(progress, "render deterministic WAV and MP3")
        wav_path = artifacts / "master.wav"
        mp3_path = artifacts / "master.mp3"
        render_master_wav(
            analysis_input,
            wav_path,
            measurement=loudness_before,
            recipe=recipe,
            tools=tools,
        )
        encode_master_mp3(wav_path, mp3_path, tools)

        _notify(progress, "validate outputs and report")
        wav_sha = sha256_file(wav_path)
        mp3_sha = sha256_file(mp3_path)
        wav_asset_id = stable_id("asset", wav_sha)
        mp3_asset_id = stable_id("asset", mp3_sha)
        wav_probe = probe_media(
            wav_path,
            source_asset_id=wav_asset_id,
            probe_id=stable_id("probe", wav_sha),
            tools=tools,
        )
        mp3_probe = probe_media(
            mp3_path,
            source_asset_id=mp3_asset_id,
            probe_id=stable_id("probe", mp3_sha),
            tools=tools,
        )
        loudness_after = measure_loudness(wav_path, tools)
        validation_notes = _validate_outputs(
            source_duration_us=probe.duration_us,
            wav_duration_us=wav_probe.duration_us,
            mp3_duration_us=mp3_probe.duration_us,
            target_integrated_lufs=recipe.target_integrated_lufs,
            max_true_peak_dbtp=recipe.max_true_peak_dbtp,
            loudness_after=loudness_after,
        )

        wav_artifact = OutputArtifact(
            artifact_id=wav_asset_id,
            kind=AssetKind.MASTER_WAV,
            relative_path="artifacts/master.wav",
            sha256=wav_sha,
            size_bytes=wav_path.stat().st_size,
            mime_type="audio/wav",
            duration_us=wav_probe.duration_us,
            validation_status="valid",
            validation_notes=tuple(validation_notes),
        )
        mp3_artifact = OutputArtifact(
            artifact_id=mp3_asset_id,
            kind=AssetKind.MASTER_MP3,
            relative_path="artifacts/master.mp3",
            sha256=mp3_sha,
            size_bytes=mp3_path.stat().st_size,
            mime_type="audio/mpeg",
            duration_us=mp3_probe.duration_us,
            validation_status="valid",
            validation_notes=("Container, audio stream, duration, and checksum validated.",),
        )
        output_manifest = OutputManifest(
            output_manifest_id=output_manifest_id,
            run_id=run_id,
            source_asset_id=source_asset_id,
            recipe_version_id=recipe.recipe_version_id,
            artifacts=(wav_artifact, mp3_artifact),
            loudness_after=loudness_after,
            target_integrated_lufs=recipe.target_integrated_lufs,
            max_true_peak_dbtp=recipe.max_true_peak_dbtp,
            validation_status="valid",
        )
        write_manifest(stage / "output-manifest.json", output_manifest)

        steps = _build_steps(
            run_id=run_id,
            run_fingerprint=run_fingerprint,
            source_manifest=source_manifest,
            probe_hash=manifest_sha256(probe),
            analysis_asset=analysis_asset,
            canonical_was_created=canonical_was_created,
            waveform_hash=manifest_sha256(waveform),
            analysis=analysis,
            semantic_map=semantic_map,
            processing_plan=processing_plan,
            gain_envelope=gain_envelope,
            output_manifest=output_manifest,
        )
        for step in steps:
            write_manifest(steps_directory / f"{step.step_key}.json", step)

        production = Production(
            production_id=production_id,
            workspace_id="workspace:local",
            title=(title or source_path.stem).strip()[:160] or "Untitled production",
            source_asset_id=source_asset_id,
            recipe_version_id=recipe.recipe_version_id,
            current_run_id=run_id,
            status=RunStatus.SUCCEEDED,
        )
        production_run = ProductionRun(
            run_id=run_id,
            production_id=production_id,
            recipe_version_id=recipe.recipe_version_id,
            engine_build_id=ENGINE_BUILD_ID,
            idempotency_key=run_fingerprint,
            status=RunStatus.SUCCEEDED,
            step_ids=tuple(step.step_id for step in steps),
        )
        write_manifest(stage / "production.json", production)
        write_manifest(stage / "production-run.json", production_run)

        report = ProcessingReport(
            processing_report_id=processing_report_id,
            production_id=production_id,
            run_id=run_id,
            source_asset_id=source_asset_id,
            recipe_version_id=recipe.recipe_version_id,
            engine_build_id=ENGINE_BUILD_ID,
            status=RunStatus.SUCCEEDED,
            loudness_before=loudness_before,
            loudness_after=loudness_after,
            step_ids=tuple(step.step_id for step in steps),
            decisions=(
                "Preserved the source bytes and recorded their SHA-256 before processing.",
                "Canonicalized once to 48 kHz float PCM because the source was not already canonical."
                if canonical_was_created
                else "Used the source directly because it already matched the canonical working format.",
                "Protected the full unknown-content region from enhancement.",
                "Applied only the recipe's standards-based two-pass final loudness master.",
            ),
            artifact_sha256={
                "source": source_sha,
                "master_wav": wav_sha,
                "master_mp3": mp3_sha,
                "output_manifest": manifest_sha256(output_manifest),
            },
            warnings=(
                "This issue-21 baseline is not the Adaptive Leveler and performs no denoise, VAD, ASR, or diarization.",
            ),
            external_api_cost_usd=0.0,
            privacy_summary=(
                "Local files only; no network processor, model, credential, transcript, "
                "or customer-media training path is used."
            ),
            reproducibility_summary=(
                "IDs and JSON manifests derive from source, recipe, engine, and native-tool versions; "
                "media metadata is stripped. "
                "Exact binary hashes require the same admitted FFmpeg build and runtime architecture."
            ),
        )
        write_manifest(stage / "processing-report.json", report)

        os.replace(stage, output_path)

    _notify(progress, "complete")
    return PipelineResult(
        output_directory=output_path,
        production_id=production_id,
        run_id=run_id,
        source_sha256=source_sha,
        wav_sha256=wav_sha,
        mp3_sha256=mp3_sha,
    )


def _build_steps(
    *,
    run_id: str,
    run_fingerprint: str,
    source_manifest: AssetManifest,
    probe_hash: str,
    analysis_asset: AssetManifest,
    canonical_was_created: bool,
    waveform_hash: str,
    analysis: AnalysisManifest,
    semantic_map: SemanticMap,
    processing_plan: ProcessingPlan,
    gain_envelope: GainEnvelope,
    output_manifest: OutputManifest,
) -> tuple[JobStep, ...]:
    source_hash = manifest_sha256(source_manifest)
    analysis_asset_hash = manifest_sha256(analysis_asset)
    analysis_hash = manifest_sha256(analysis)
    semantic_hash = manifest_sha256(semantic_map)
    plan_hash = manifest_sha256(processing_plan)
    gain_hash = manifest_sha256(gain_envelope)
    output_hash = manifest_sha256(output_manifest)
    definitions: tuple[StepDefinition, ...] = (
        ("validate-probe", source_hash, JobStatus.SUCCEEDED, (source_manifest.asset_id,), {"probe_hash": probe_hash}),
        (
            "canonicalize-if-needed",
            source_hash,
            JobStatus.SUCCEEDED if canonical_was_created else JobStatus.BYPASSED,
            (analysis_asset.asset_id,),
            {"canonicalized": canonical_was_created},
        ),
        (
            "waveform-peaks",
            analysis_asset_hash,
            JobStatus.SUCCEEDED,
            ("manifest:waveform",),
            {"manifest_hash": waveform_hash},
        ),
        ("loudness-before", analysis_asset_hash, JobStatus.SUCCEEDED, (analysis.analysis_manifest_id,), {}),
        ("semantic-map-baseline", analysis_hash, JobStatus.SUCCEEDED, (semantic_map.semantic_map_id,), {}),
        ("regional-protect-baseline", semantic_hash, JobStatus.SUCCEEDED, (processing_plan.processing_plan_id,), {}),
        ("unity-gain-envelope", plan_hash, JobStatus.SUCCEEDED, (gain_envelope.gain_envelope_id,), {}),
        (
            "two-pass-loudness-master",
            sha256_text(f"{analysis_hash}|{plan_hash}|{gain_hash}"),
            JobStatus.SUCCEEDED,
            (),
            {},
        ),
        ("output-validation", output_hash, JobStatus.SUCCEEDED, (output_manifest.output_manifest_id,), {}),
    )
    return tuple(
        JobStep(
            step_id=_step_id(run_fingerprint, step_key),
            run_id=run_id,
            step_key=step_key,
            implementation_version=ENGINE_BUILD_ID,
            input_manifest_hash=input_hash,
            idempotency_key=sha256_text(f"{input_hash}|{step_key}|{ENGINE_BUILD_ID}"),
            status=status,
            output_manifest_ids=output_ids,
            metrics=metrics,
        )
        for step_key, input_hash, status, output_ids, metrics in definitions
    )


def _validate_outputs(
    *,
    source_duration_us: int,
    wav_duration_us: int,
    mp3_duration_us: int,
    target_integrated_lufs: float,
    max_true_peak_dbtp: float,
    loudness_after: LoudnessMeasurement,
) -> list[str]:
    integrated_lufs = loudness_after.integrated_lufs
    true_peak_dbtp = loudness_after.true_peak_dbtp
    if abs(wav_duration_us - source_duration_us) > 10_000:
        raise OutputValidationError("The WAV master duration differs from the source by more than 10 ms.")
    if abs(mp3_duration_us - source_duration_us) > 120_000:
        raise OutputValidationError("The MP3 master duration differs from the source by more than 120 ms.")
    if abs(integrated_lufs - target_integrated_lufs) > 0.35:
        raise OutputValidationError(
            f"The WAV master measured {integrated_lufs:.2f} LUFS; target tolerance is ±0.35 LU."
        )
    if true_peak_dbtp > max_true_peak_dbtp + 0.20:
        raise OutputValidationError(
            f"The WAV master measured {true_peak_dbtp:.2f} dBTP; ceiling tolerance is +0.20 dB."
        )
    return [
        "Container, audio stream, duration, and checksum validated.",
        f"Integrated loudness is within ±0.35 LU of {target_integrated_lufs:.2f} LUFS.",
        f"True peak does not exceed {max_true_peak_dbtp + 0.20:.2f} dBTP.",
    ]


def _step_id(run_fingerprint: str, step_key: str) -> str:
    return stable_id(f"step:{step_key}", sha256_text(f"{run_fingerprint}|{step_key}"), length=16)


def _notify(progress: ProgressCallback | None, message: str) -> None:
    if progress is not None:
        progress(message)
