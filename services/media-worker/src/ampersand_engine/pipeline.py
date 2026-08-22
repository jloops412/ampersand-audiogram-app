from __future__ import annotations

import mimetypes
import os
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from ampersand_contracts import (
    AdaptiveLevelerSettings,
    AnalysisManifest,
    AssetKind,
    AssetManifest,
    EvidenceProvenance,
    GainEnvelope,
    JobStatus,
    JobStep,
    LevelerStatistics,
    LoudnessMeasurement,
    OutputArtifact,
    OutputManifest,
    ProcessingPlan,
    ProcessingReport,
    ProcessingRouterReport,
    ProcessingRouterSettings,
    Production,
    ProductionRun,
    ProductionSettings,
    RunStatus,
    SemanticMap,
    manifest_sha256,
    write_manifest,
)

from . import __version__
from .energy_vad import analyze_energy_vad
from .errors import EngineError, OutputValidationError
from .ffmpeg import (
    FFmpegTools,
    canonicalize_audio,
    encode_master_mp3,
    measure_loudness,
    measure_loudness_timeline,
    probe_media,
    render_audiogram_mp4,
    render_cleanup_wav,
    render_master_wav,
    requires_canonical_audio,
)
from .hashing import sha256_file, sha256_text, stable_id
from .leveler import build_adaptive_leveler, default_leveler_settings
from .provider_artifacts import write_provider_artifact
from .recipe_loader import load_recipe
from .router import build_processing_router
from .semantic_adapters import normalize_loudness_frames, normalize_vad_frames
from .semantic_debug import write_semantic_debug_report
from .semantic_fusion import fuse_semantic_map
from .settings import ProductionIntent, SettingsSource, resolve_production_settings
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
    wav_sha256: str | None
    mp3_sha256: str | None
    audiogram_sha256: str | None


def process_source(
    source: Path,
    output_directory: Path,
    *,
    recipe_slug: str = "smart-spoken-word-v0",
    title: str | None = None,
    artwork: Path | None = None,
    settings: ProductionSettings | None = None,
    intent: ProductionIntent = "podcast",
    template_version_id: str | None = None,
    settings_source: SettingsSource = "recipe",
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
    resolved_settings = resolve_production_settings(
        recipe,
        settings=settings,
        intent=intent,
        template_version_id=template_version_id,
        settings_source=settings_source,
    )
    production_title = (title or source_path.stem).strip()[:160] or "Untitled production"
    artwork_path = artwork.expanduser().resolve(strict=True) if artwork is not None else None
    if artwork_path is not None and not artwork_path.is_file():
        raise EngineError("The audiogram background asset must be a local regular file.")
    audiogram_settings = resolved_settings.settings.audiogram
    if (
        audiogram_settings.enabled
        and audiogram_settings.background_mode in {"artwork", "video"}
        and artwork_path is None
    ):
        raise EngineError("Audiogram artwork and video modes require --artwork.")
    if audiogram_settings.enabled and audiogram_settings.background_mode == "color" and artwork_path is not None:
        raise EngineError("Audiogram color mode does not accept a background asset.")
    if not audiogram_settings.enabled and artwork_path is not None:
        raise EngineError("Background artwork is valid only when audiogram rendering is enabled.")
    source_sha = sha256_file(source_path)
    artwork_sha = sha256_file(artwork_path) if artwork_path is not None else None
    recipe_sha = manifest_sha256(recipe)
    resolved_settings_manifest_sha = manifest_sha256(resolved_settings)
    run_fingerprint = sha256_text(
        "|".join(
            (
                source_sha,
                artwork_sha or "no-artwork",
                recipe_sha,
                resolved_settings_manifest_sha,
                ENGINE_BUILD_ID,
                tools.ffmpeg_version,
                tools.ffprobe_version,
            )
        )
    )
    production_id = stable_id("production", sha256_text(f"{source_sha}|{recipe.recipe_version_id}"))
    run_id = stable_id("run", run_fingerprint)
    source_asset_id = stable_id("asset", source_sha)
    probe_id = stable_id("probe", run_fingerprint)
    waveform_id = stable_id("waveform", run_fingerprint)
    semantic_map_id = stable_id("semantic-map", run_fingerprint)
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
        if artwork_path is not None and artwork_sha is not None:
            artwork_manifest = AssetManifest(
                asset_id=stable_id("asset", artwork_sha),
                kind=AssetKind.BACKGROUND_ARTWORK,
                uri=f"sha256://{artwork_sha}",
                sha256=artwork_sha,
                size_bytes=artwork_path.stat().st_size,
                mime_type=mimetypes.guess_type(artwork_path.name)[0] or "application/octet-stream",
                filename=artwork_path.name[:255],
                retention_class="local_fixture",
                provenance={
                    "ingest_mode": "local_cli",
                    "immutable": True,
                    "network_used": False,
                    "purpose": f"audiogram_{audiogram_settings.background_mode}_background",
                },
            )
            write_manifest(stage / "background-artwork-manifest.json", artwork_manifest)
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

        _notify(progress, "measure, build waveform, and analyze semantics")
        loudness_before = measure_loudness(analysis_input, tools)
        write_manifest(stage / "loudness-before.json", loudness_before)
        loudness_timeline = measure_loudness_timeline(
            analysis_input,
            duration_us=probe.duration_us,
            tools=tools,
        )
        vad_analysis = analyze_energy_vad(
            analysis_input,
            duration_us=probe.duration_us,
            tools=tools,
        )
        waveform = generate_waveform_peaks(
            analysis_input,
            waveform_id=waveform_id,
            source_asset_id=source_asset_id,
            channels=probe.channels,
            duration_us=probe.duration_us,
            tools=tools,
        )
        write_manifest(stage / "waveform-peaks.json", waveform)

        ebur128_artifact = write_provider_artifact(
            stage,
            relative_path="provider-native/ffmpeg-ebur128.json",
            payload=loudness_timeline.provider_payload,
            provider_id="provider:ffmpeg-ebur128",
            provider_version=tools.ffmpeg_version,
            adapter_id="adapter:ffmpeg-ebur128-v0",
            adapter_version=ENGINE_BUILD_ID,
            redaction_summary="Retains parsed metric frames only; excludes command lines and local paths.",
        )
        energy_vad_artifact = write_provider_artifact(
            stage,
            relative_path="provider-native/ampersand-energy-vad-v0.json",
            payload=vad_analysis.provider_payload,
            provider_id="provider:ampersand-energy-vad",
            provider_version="0.1.0",
            adapter_id="adapter:ampersand-energy-vad-v0",
            adapter_version=ENGINE_BUILD_ID,
            redaction_summary="First-party numeric frame features only; contains no path, transcript, or credential.",
        )
        write_manifest(stage / "provider-native/ffmpeg-ebur128.manifest.json", ebur128_artifact)
        write_manifest(stage / "provider-native/ampersand-energy-vad-v0.manifest.json", energy_vad_artifact)

        ebur128_provenance = EvidenceProvenance(
            provenance_id=stable_id("provenance", sha256_text(ebur128_artifact.artifact_id)),
            provider_id=ebur128_artifact.provider_id,
            provider_version=ebur128_artifact.provider_version,
            adapter_id=ebur128_artifact.adapter_id,
            adapter_version=ebur128_artifact.adapter_version,
            native_artifact_id=ebur128_artifact.artifact_id,
            deterministic=True,
        )
        energy_vad_provenance = EvidenceProvenance(
            provenance_id=stable_id("provenance", sha256_text(energy_vad_artifact.artifact_id)),
            provider_id=energy_vad_artifact.provider_id,
            provider_version=energy_vad_artifact.provider_version,
            adapter_id=energy_vad_artifact.adapter_id,
            adapter_version=energy_vad_artifact.adapter_version,
            native_artifact_id=energy_vad_artifact.artifact_id,
            deterministic=True,
        )
        semantic_map = fuse_semantic_map(
            semantic_map_id=semantic_map_id,
            source_asset_id=source_asset_id,
            duration_us=probe.duration_us,
            provenance_sources=(ebur128_provenance, energy_vad_provenance),
            observations=(
                *normalize_loudness_frames(
                    loudness_timeline.frames,
                    provenance=ebur128_provenance,
                    id_seed=run_fingerprint,
                ),
                *normalize_vad_frames(
                    vad_analysis.frames,
                    provenance=energy_vad_provenance,
                    id_seed=run_fingerprint,
                ),
            ),
            provider_native_artifact_ids=(ebur128_artifact.artifact_id, energy_vad_artifact.artifact_id),
            unavailable_adapters=(
                "adapter:asr-unavailable",
                "adapter:diarization-unavailable",
                "adapter:music-classifier-unavailable",
            ),
            warnings=(
                "The built-in energy/spectral VAD is confidence-bounded and cannot reliably separate "
                "music from speech.",
                "ASR, diarization, and music classification are optional and unavailable in this local baseline.",
                "Uncertain, conflicting, and unsupported content remains protected.",
            ),
        )
        write_manifest(stage / "semantic-map-v0.json", semantic_map)
        write_semantic_debug_report(stage / "semantic-map-debug.html", semantic_map)

        _notify(progress, "build Processing Router V0 shadow plan")
        router_result = build_processing_router(
            semantic_map,
            run_id=run_id,
            recipe=recipe,
        )
        router_settings = router_result.settings
        processing_plan = router_result.processing_plan
        router_report = router_result.report
        write_manifest(stage / "router-settings.json", router_settings)
        write_manifest(stage / "processing-plan.json", processing_plan)
        write_manifest(stage / "processing-router-report.json", router_report)

        _notify(progress, "plan Adaptive Leveler shadow candidate")
        leveler_settings = default_leveler_settings(activation_mode="shadow")
        leveler_result = build_adaptive_leveler(
            semantic_map,
            run_id=run_id,
            settings=leveler_settings,
        )
        gain_envelope = leveler_result.gain_envelope
        leveler_statistics = leveler_result.statistics
        write_manifest(stage / "leveler-settings.json", leveler_settings)
        write_manifest(stage / "gain-envelope.json", gain_envelope)
        write_manifest(stage / "leveler-statistics.json", leveler_statistics)

        analysis = AnalysisManifest(
            analysis_manifest_id=analysis_manifest_id,
            run_id=run_id,
            source_asset_id=source_asset_id,
            media_probe_id=probe_id,
            waveform_id=waveform_id,
            loudness_before=loudness_before,
            warnings=(
                "Semantic Map V0 includes deterministic loudness/peak evidence and a conservative first-party VAD.",
                "Processing Router V0 emits an auditable shadow plan and does not change production audio.",
                "Adaptive Leveler V0 emits a deterministic shadow candidate that is not rendered into the master.",
                "ASR, diarization, music classification, and advanced defect classification remain "
                "optional/unavailable.",
            ),
        )
        write_manifest(stage / "analysis.json", analysis)

        write_manifest(stage / "recipe.json", recipe)
        write_manifest(stage / "resolved-settings.json", resolved_settings)

        cleanup_settings = resolved_settings.settings.cleanup
        cleanup_applied = (
            cleanup_settings.rumble_filter
            or cleanup_settings.noise_reduction != "off"
            or cleanup_settings.hum_reduction != "off"
            or cleanup_settings.declip
            or cleanup_settings.noise_gate != "off"
            or cleanup_settings.deesser != "off"
            or cleanup_settings.voice_enhancement != "off"
            or cleanup_settings.compression != "off"
        )
        mastering_input = analysis_input
        if cleanup_applied:
            _notify(progress, "apply deterministic cleanup and compression")
            cleanup_path = stage / "cleanup-working.wav"
            render_cleanup_wav(
                analysis_input,
                cleanup_path,
                settings=cleanup_settings,
                tools=tools,
            )
            mastering_input = cleanup_path
        cleanup_input_loudness = measure_loudness(mastering_input, tools)
        write_manifest(stage / "pre-master-loudness.json", cleanup_input_loudness)

        _notify(progress, "render deterministic WAV and MP3")
        export_settings = resolved_settings.settings.export
        metadata_settings = resolved_settings.settings.metadata
        mastering_settings = resolved_settings.settings.mastering
        wav_path = artifacts / "master.wav" if export_settings.wav else stage / "master-for-encode.wav"
        mp3_path = artifacts / "master.mp3"
        audiogram_path = artifacts / "audiogram.mp4"
        render_master_wav(
            mastering_input,
            wav_path,
            measurement=cleanup_input_loudness,
            settings=mastering_settings,
            title=production_title,
            metadata=metadata_settings,
            tools=tools,
        )
        if export_settings.mp3:
            encode_master_mp3(
                wav_path,
                mp3_path,
                tools,
                bitrate_kbps=export_settings.mp3_bitrate_kbps,
                title=production_title,
                metadata=metadata_settings,
            )
        if audiogram_settings.enabled:
            _notify(progress, "render audiogram MP4")
            render_audiogram_mp4(
                wav_path,
                audiogram_path,
                title=production_title,
                metadata=metadata_settings,
                settings=audiogram_settings,
                artwork=artwork_path,
                tools=tools,
            )

        _notify(progress, "validate outputs and report")
        wav_sha = sha256_file(wav_path) if export_settings.wav else None
        mp3_sha = sha256_file(mp3_path) if export_settings.mp3 else None
        audiogram_sha = sha256_file(audiogram_path) if audiogram_settings.enabled else None
        wav_asset_id = stable_id("asset", wav_sha) if wav_sha is not None else None
        mp3_asset_id = stable_id("asset", mp3_sha) if mp3_sha is not None else None
        audiogram_asset_id = stable_id("asset", audiogram_sha) if audiogram_sha is not None else None
        wav_probe = probe_media(
            wav_path,
            source_asset_id=wav_asset_id or stable_id("asset", sha256_file(wav_path)),
            probe_id=stable_id("probe", sha256_file(wav_path)),
            tools=tools,
        )
        mp3_probe = (
            probe_media(
                mp3_path,
                source_asset_id=mp3_asset_id,
                probe_id=stable_id("probe", mp3_sha),
                tools=tools,
            )
            if mp3_asset_id is not None and mp3_sha is not None
            else None
        )
        audiogram_probe = (
            probe_media(
                audiogram_path,
                source_asset_id=audiogram_asset_id,
                probe_id=stable_id("probe", audiogram_sha),
                tools=tools,
            )
            if audiogram_asset_id is not None and audiogram_sha is not None
            else None
        )
        loudness_after = measure_loudness(wav_path, tools)
        write_manifest(stage / "loudness-after.json", loudness_after)
        validation_notes = _validate_outputs(
            source_duration_us=probe.duration_us,
            wav_duration_us=wav_probe.duration_us,
            mp3_duration_us=mp3_probe.duration_us if mp3_probe is not None else None,
            audiogram_duration_us=audiogram_probe.duration_us if audiogram_probe is not None else None,
            target_integrated_lufs=mastering_settings.target_integrated_lufs,
            max_true_peak_dbtp=mastering_settings.max_true_peak_dbtp,
            loudness_after=loudness_after,
        )

        output_artifacts: list[OutputArtifact] = []
        if wav_asset_id is not None and wav_sha is not None:
            output_artifacts.append(
                OutputArtifact(
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
            )
        if mp3_asset_id is not None and mp3_sha is not None and mp3_probe is not None:
            output_artifacts.append(
                OutputArtifact(
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
            )
        if audiogram_asset_id is not None and audiogram_sha is not None and audiogram_probe is not None:
            output_artifacts.append(
                OutputArtifact(
                    artifact_id=audiogram_asset_id,
                    kind=AssetKind.AUDIOGRAM_MP4,
                    relative_path="artifacts/audiogram.mp4",
                    sha256=audiogram_sha,
                    size_bytes=audiogram_path.stat().st_size,
                    mime_type="video/mp4",
                    duration_us=audiogram_probe.duration_us,
                    validation_status="valid",
                    validation_notes=("H.264 video, AAC audio, duration, and checksum validated.",),
                )
            )
        output_manifest = OutputManifest(
            output_manifest_id=output_manifest_id,
            run_id=run_id,
            source_asset_id=source_asset_id,
            recipe_version_id=recipe.recipe_version_id,
            resolved_settings_id=resolved_settings.resolved_settings_id,
            resolved_settings_sha256=resolved_settings.settings_sha256,
            artifacts=tuple(output_artifacts),
            loudness_after=loudness_after,
            target_integrated_lufs=mastering_settings.target_integrated_lufs,
            max_true_peak_dbtp=mastering_settings.max_true_peak_dbtp,
            validation_status="valid",
        )
        write_manifest(stage / "output-manifest.json", output_manifest)
        if not export_settings.wav:
            wav_path.unlink()
        if cleanup_applied:
            mastering_input.unlink()

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
            recipe_hash=recipe_sha,
            router_settings=router_settings,
            router_report=router_report,
            leveler_settings=leveler_settings,
            leveler_statistics=leveler_statistics,
            gain_envelope=gain_envelope,
            cleanup_applied=cleanup_applied,
            cleanup_settings_hash=manifest_sha256(cleanup_settings),
            audiogram_enabled=audiogram_settings.enabled,
            output_manifest=output_manifest,
        )
        for step in steps:
            write_manifest(steps_directory / f"{step.step_key}.json", step)

        production = Production(
            production_id=production_id,
            workspace_id="workspace:local",
            title=production_title,
            source_asset_id=source_asset_id,
            recipe_version_id=recipe.recipe_version_id,
            current_run_id=run_id,
            status=RunStatus.SUCCEEDED,
        )
        production_run = ProductionRun(
            run_id=run_id,
            production_id=production_id,
            recipe_version_id=recipe.recipe_version_id,
            resolved_settings_id=resolved_settings.resolved_settings_id,
            resolved_settings_sha256=resolved_settings.settings_sha256,
            engine_build_id=ENGINE_BUILD_ID,
            idempotency_key=run_fingerprint,
            status=RunStatus.SUCCEEDED,
            step_ids=tuple(step.step_id for step in steps),
        )
        write_manifest(stage / "production.json", production)
        write_manifest(stage / "production-run.json", production_run)

        artifact_hashes = {
            "source": source_sha,
            "resolved_settings": resolved_settings_manifest_sha,
            "semantic_map_v0": manifest_sha256(semantic_map),
            "semantic_debug": sha256_file(stage / "semantic-map-debug.html"),
            "provider_ffmpeg_ebur128": ebur128_artifact.sha256,
            "provider_ampersand_energy_vad": energy_vad_artifact.sha256,
            "loudness_before": manifest_sha256(loudness_before),
            "pre_master_loudness": manifest_sha256(cleanup_input_loudness),
            "router_settings": manifest_sha256(router_settings),
            "processing_plan": manifest_sha256(processing_plan),
            "processing_router_report": manifest_sha256(router_report),
            "leveler_settings": manifest_sha256(leveler_settings),
            "gain_envelope": manifest_sha256(gain_envelope),
            "leveler_statistics": manifest_sha256(leveler_statistics),
            "loudness_after": manifest_sha256(loudness_after),
            "output_manifest": manifest_sha256(output_manifest),
        }
        if wav_sha is not None:
            artifact_hashes["master_wav"] = wav_sha
        if mp3_sha is not None:
            artifact_hashes["master_mp3"] = mp3_sha
        if artwork_sha is not None:
            artifact_hashes["background_artwork"] = artwork_sha
        if audiogram_sha is not None:
            artifact_hashes["audiogram_mp4"] = audiogram_sha
        enabled_output_names = ", ".join(
            format_name.upper() for format_name in recipe.output_formats if getattr(export_settings, format_name)
        )

        report = ProcessingReport(
            processing_report_id=processing_report_id,
            production_id=production_id,
            run_id=run_id,
            source_asset_id=source_asset_id,
            recipe_version_id=recipe.recipe_version_id,
            resolved_settings_id=resolved_settings.resolved_settings_id,
            resolved_settings_sha256=resolved_settings.settings_sha256,
            engine_build_id=ENGINE_BUILD_ID,
            status=RunStatus.SUCCEEDED,
            loudness_before=loudness_before,
            loudness_after=loudness_after,
            gain_envelope_id=gain_envelope.gain_envelope_id,
            leveler_statistics_id=leveler_statistics.leveler_statistics_id,
            step_ids=tuple(step.step_id for step in steps),
            decisions=(
                "Preserved the source bytes and recorded their SHA-256 before processing.",
                "Canonicalized once to 48 kHz float PCM because the source was not already canonical."
                if canonical_was_created
                else "Used the source directly because it already matched the canonical working format.",
                (
                    f"Built Semantic Map V0 with {len(semantic_map.regions)} full-coverage regions, "
                    f"{len(semantic_map.observations)} normalized observations, and "
                    f"{len(semantic_map.conflicts)} explicit conflicts."
                ),
                (
                    f"Built Processing Router V0 in shadow mode with {router_report.protected_region_count} "
                    f"protected, {router_report.bypassed_region_count} bypassed, "
                    f"{router_report.deterministic_filter_region_count} deterministic-filter, "
                    f"{router_report.denoise_region_count} denoise, and "
                    f"{router_report.leveler_region_count} Leveler candidate regions."
                ),
                (
                    f"Planned Adaptive Leveler V0 in shadow mode: {leveler_statistics.eligible_region_count} "
                    f"eligible regions, {leveler_statistics.changed_region_count} proposed changes, and "
                    f"{leveler_statistics.gain_min_db:.2f} to {leveler_statistics.gain_max_db:.2f} dB gain."
                ),
                (
                    f"Applied the deterministic V1 cleanup chain globally: noise reduction "
                    f"{cleanup_settings.noise_reduction}, rumble "
                    f"{'on' if cleanup_settings.rumble_filter else 'off'}, hum "
                    f"{cleanup_settings.hum_reduction}, declip "
                    f"{'on' if cleanup_settings.declip else 'off'}, gate {cleanup_settings.noise_gate}, "
                    f"de-esser {cleanup_settings.deesser}, voice enhancement "
                    f"{cleanup_settings.voice_enhancement}, and compression {cleanup_settings.compression}."
                    if cleanup_applied
                    else "Bypassed deterministic cleanup because every cleanup control was off."
                ),
                "Did not render the shadow Adaptive Leveler gain envelope; applied the selected cleanup chain "
                "followed by the standards-based two-pass final loudness master.",
                (
                    f"Resolved the {resolved_settings.intent} intent to "
                    f"{mastering_settings.target_integrated_lufs:.1f} LUFS, "
                    f"{mastering_settings.max_true_peak_dbtp:.1f} dBTP, and "
                    f"{enabled_output_names} "
                    "delivery outputs."
                ),
                (
                    f"Wrote portable delivery metadata and rendered a {audiogram_settings.aspect_ratio} "
                    f"{audiogram_settings.waveform_style} audiogram with "
                    f"{audiogram_settings.background_mode} background."
                    if audiogram_settings.enabled
                    else "Wrote portable delivery metadata; audiogram rendering was not requested."
                ),
            ),
            artifact_sha256=artifact_hashes,
            warnings=(
                "Processing Router V0 and Adaptive Leveler V0 are shadow-only in this pipeline until admitted "
                "processors, music/protected-content evidence, and human listening gates authorize regional rendering; "
                "no regional cleanup or Leveler gain is applied.",
                "The deterministic FFT denoiser targets steady background noise. It does not perform true "
                "background-music separation or dereverberation, and strong settings require listening review.",
                "The bootstrap VAD is conservative; ASR, diarization, and music classification are not required "
                "for mastering.",
                *resolved_settings.warnings,
                *router_report.warnings,
            ),
            external_api_cost_usd=0.0,
            privacy_summary=(
                "Local files only; no network processor, model, credential, transcript, "
                "or customer-media training path is used."
            ),
            reproducibility_summary=(
                "IDs and JSON manifests derive from source, resolved settings, recipe, engine, "
                "and native-tool versions; "
                "incidental source metadata is stripped and requested output metadata is written explicitly. "
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
        audiogram_sha256=audiogram_sha,
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
    recipe_hash: str,
    router_settings: ProcessingRouterSettings,
    router_report: ProcessingRouterReport,
    leveler_settings: AdaptiveLevelerSettings,
    leveler_statistics: LevelerStatistics,
    gain_envelope: GainEnvelope,
    cleanup_applied: bool,
    cleanup_settings_hash: str,
    audiogram_enabled: bool,
    output_manifest: OutputManifest,
) -> tuple[JobStep, ...]:
    source_hash = manifest_sha256(source_manifest)
    analysis_asset_hash = manifest_sha256(analysis_asset)
    analysis_hash = manifest_sha256(analysis)
    semantic_hash = manifest_sha256(semantic_map)
    plan_hash = manifest_sha256(processing_plan)
    router_settings_hash = manifest_sha256(router_settings)
    router_report_hash = manifest_sha256(router_report)
    leveler_settings_hash = manifest_sha256(leveler_settings)
    leveler_statistics_hash = manifest_sha256(leveler_statistics)
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
        (
            "semantic-map-v0",
            analysis_hash,
            JobStatus.SUCCEEDED,
            (semantic_map.semantic_map_id, *semantic_map.provider_native_artifact_ids),
            {
                "region_count": len(semantic_map.regions),
                "observation_count": len(semantic_map.observations),
                "conflict_count": len(semantic_map.conflicts),
                "coverage": semantic_map.coverage,
            },
        ),
        (
            "processing-router-v0-shadow",
            sha256_text(f"{semantic_hash}|{router_settings_hash}|{recipe_hash}"),
            JobStatus.SUCCEEDED,
            (processing_plan.processing_plan_id, router_report.processing_router_report_id),
            {
                "planning_mode": router_settings.planning_mode,
                "protected_region_count": router_report.protected_region_count,
                "bypassed_region_count": router_report.bypassed_region_count,
                "deterministic_filter_region_count": router_report.deterministic_filter_region_count,
                "denoise_region_count": router_report.denoise_region_count,
                "leveler_region_count": router_report.leveler_region_count,
                "processing_plan_hash": plan_hash,
                "router_report_hash": router_report_hash,
                "applied_to_audio": False,
            },
        ),
        (
            "adaptive-leveler-shadow",
            sha256_text(f"{semantic_hash}|{leveler_settings_hash}"),
            JobStatus.SUCCEEDED,
            (gain_envelope.gain_envelope_id, leveler_statistics.leveler_statistics_id),
            {
                "activation_mode": leveler_statistics.activation_mode,
                "eligible_region_count": leveler_statistics.eligible_region_count,
                "changed_region_count": leveler_statistics.changed_region_count,
                "gain_min_db": leveler_statistics.gain_min_db,
                "gain_max_db": leveler_statistics.gain_max_db,
                "gain_envelope_hash": gain_hash,
                "statistics_hash": leveler_statistics_hash,
                "applied_to_audio": False,
            },
        ),
        (
            "deterministic-cleanup-v1",
            sha256_text(f"{analysis_hash}|{cleanup_settings_hash}"),
            JobStatus.SUCCEEDED if cleanup_applied else JobStatus.BYPASSED,
            (),
            {
                "settings_hash": cleanup_settings_hash,
                "applied_to_audio": cleanup_applied,
                "scope": "global",
            },
        ),
        (
            "two-pass-loudness-master",
            sha256_text(f"{analysis_hash}|{plan_hash}|{cleanup_settings_hash}|shadow-unity-render"),
            JobStatus.SUCCEEDED,
            (),
            {},
        ),
        (
            "render-audiogram",
            output_hash,
            JobStatus.SUCCEEDED if audiogram_enabled else JobStatus.BYPASSED,
            (),
            {"enabled": audiogram_enabled},
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
    mp3_duration_us: int | None,
    audiogram_duration_us: int | None,
    target_integrated_lufs: float,
    max_true_peak_dbtp: float,
    loudness_after: LoudnessMeasurement,
) -> list[str]:
    integrated_lufs = loudness_after.integrated_lufs
    true_peak_dbtp = loudness_after.true_peak_dbtp
    if abs(wav_duration_us - source_duration_us) > 10_000:
        raise OutputValidationError("The WAV master duration differs from the source by more than 10 ms.")
    if mp3_duration_us is not None and abs(mp3_duration_us - source_duration_us) > 120_000:
        raise OutputValidationError("The MP3 master duration differs from the source by more than 120 ms.")
    if audiogram_duration_us is not None and abs(audiogram_duration_us - source_duration_us) > 150_000:
        raise OutputValidationError("The audiogram duration differs from the source by more than 150 ms.")
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
        "Audiogram duration matches the source within 150 ms."
        if audiogram_duration_us is not None
        else "Audiogram output was not requested.",
    ]


def _step_id(run_fingerprint: str, step_key: str) -> str:
    return stable_id(f"step:{step_key}", sha256_text(f"{run_fingerprint}|{step_key}"), length=16)


def _notify(progress: ProgressCallback | None, message: str) -> None:
    if progress is not None:
        progress(message)
