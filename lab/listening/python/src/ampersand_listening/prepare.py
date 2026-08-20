from __future__ import annotations

import hashlib
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ampersand_contracts import (
    ListeningArtifactFlag,
    ListeningCandidateRole,
    ListeningExperimentCandidate,
    ListeningExperimentItem,
    ListeningExperimentManifest,
    ListeningIdentityReveal,
    ListeningItemReveal,
    ListeningObjectiveMetrics,
    ListeningOption,
    ListeningSessionManifest,
    ListeningSessionState,
    ListeningTrial,
    LoudnessMeasurement,
    PreparedListeningExperiment,
    RecipeVersion,
    manifest_sha256,
    read_manifest,
    write_manifest,
)
from ampersand_engine.ffmpeg import (
    FFmpegTools,
    measure_loudness,
    measure_loudness_timeline,
    probe_media,
    render_master_wav,
    subprocess_environment,
)
from ampersand_engine.hashing import sha256_file
from ampersand_engine.settings import default_production_settings

from .diagnostics import decode_float32, full_reference_metrics, measure_pcm
from .errors import ListeningLabError
from .ui import INDEX_HTML

RANDOMIZATION_ALGORITHM: Literal["sha256-seed-item-candidate-v1"] = "sha256-seed-item-candidate-v1"
LOUDNESS_TOLERANCE_LU = 0.35
TRUE_PEAK_TOLERANCE_DB = 0.20


@dataclass(frozen=True)
class _PreparedCandidate:
    candidate: ListeningExperimentCandidate
    item: ListeningExperimentItem
    trial_id: str
    option: ListeningOption
    reveal: ListeningIdentityReveal
    raw_diagnostic_path: Path
    loudness_before: LoudnessMeasurement
    momentary_lufs_min: float
    momentary_lufs_max: float
    short_term_lufs_min: float
    short_term_lufs_max: float
    loudness_frame_count: int


def prepare_experiment(
    manifest_path: Path,
    destination: Path,
    *,
    tools: FFmpegTools | None = None,
) -> PreparedListeningExperiment:
    """Prepare loudness-matched opaque listening copies without modifying archived candidates."""

    if destination.exists():
        raise FileExistsError(f"refusing to overwrite existing listening workspace: {destination}")
    manifest_path = manifest_path.expanduser().resolve(strict=True)
    experiment = read_manifest(manifest_path, ListeningExperimentManifest)
    experiment_directory = manifest_path.parent
    selected_tools = tools or FFmpegTools.discover()
    candidate_paths = _resolve_candidates(experiment, experiment_directory)
    _validate_prompts_do_not_reveal_identities(experiment)
    _validate_original_hashes(experiment)
    commitment = manifest_sha256(experiment)
    session_id = _stable_id("listening-session", commitment, RANDOMIZATION_ALGORITHM)
    recipe = _listening_recipe(experiment)

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{destination.name}-", dir=destination.parent))
    try:
        public = temporary / "public"
        private = temporary / "private"
        audio_directory = public / "audio"
        segments_directory = private / "segments"
        diagnostics_directory = private / "diagnostics"
        scores_directory = private / "scores"
        audio_directory.mkdir(parents=True)
        segments_directory.mkdir(parents=True)
        diagnostics_directory.mkdir(parents=True)
        scores_directory.mkdir(parents=True)

        by_candidate = {candidate.candidate_id: candidate for candidate in experiment.candidates}
        prepared_by_item: dict[str, list[_PreparedCandidate]] = {}
        for item in experiment.items:
            trial_id = _stable_id("listening-trial", str(experiment.randomization_seed), item.item_id)
            item_prepared: list[_PreparedCandidate] = []
            for candidate_id in item.candidate_ids:
                candidate = by_candidate[candidate_id]
                source = candidate_paths[candidate_id]
                listening_source = _segment_source(
                    source,
                    candidate=candidate,
                    item=item,
                    destination=segments_directory,
                    tools=selected_tools,
                )
                loudness_before = measure_loudness(listening_source, selected_tools)
                option_id = _stable_id(
                    "listening-option",
                    str(experiment.randomization_seed),
                    item.item_id,
                    candidate.candidate_id,
                )
                output_name = option_id.replace(":", "-") + ".wav"
                output = audio_directory / output_name
                render_master_wav(
                    listening_source,
                    output,
                    measurement=loudness_before,
                    settings=default_production_settings(recipe).mastering,
                    tools=selected_tools,
                )
                loudness_after = measure_loudness(output, selected_tools)
                _validate_listening_loudness(loudness_after.integrated_lufs, loudness_after.true_peak_dbtp, experiment)
                output_hash = sha256_file(output)
                probe = probe_media(
                    output,
                    source_asset_id=_stable_id("asset", output_hash),
                    probe_id=_stable_id("probe", output_hash),
                    tools=selected_tools,
                )
                loudness_timeline = measure_loudness_timeline(
                    output,
                    duration_us=probe.duration_us,
                    tools=selected_tools,
                )
                momentary = tuple(frame.momentary_lufs for frame in loudness_timeline.frames)
                short_term = tuple(frame.short_term_lufs for frame in loudness_timeline.frames)
                option = ListeningOption(
                    option_id=option_id,
                    audio_relative_path=f"audio/{output_name}",
                    listening_sha256=output_hash,
                    loudness=loudness_after,
                    duration_us=probe.duration_us,
                    sample_rate_hz=probe.sample_rate_hz,
                    channels=probe.channels,
                )
                reveal = ListeningIdentityReveal(
                    trial_id=trial_id,
                    option_id=option_id,
                    candidate_id=candidate.candidate_id,
                    role=candidate.role,
                    processor_id=candidate.processor_id,
                    processor_version=candidate.processor_version,
                    recipe_version_id=candidate.recipe_version_id,
                    model_manifest_ids=candidate.model_manifest_ids,
                    engine_build_id=candidate.engine_build_id,
                )
                raw_path = diagnostics_directory / f"{option_id.replace(':', '-')}.f32"
                decode_float32(output, raw_path, selected_tools)
                item_prepared.append(
                    _PreparedCandidate(
                        candidate=candidate,
                        item=item,
                        trial_id=trial_id,
                        option=option,
                        reveal=reveal,
                        raw_diagnostic_path=raw_path,
                        loudness_before=loudness_before,
                        momentary_lufs_min=min(momentary),
                        momentary_lufs_max=max(momentary),
                        short_term_lufs_min=min(short_term),
                        short_term_lufs_max=max(short_term),
                        loudness_frame_count=len(loudness_timeline.frames),
                    )
                )
            prepared_by_item[item.item_id] = item_prepared

        trials = _public_trials(experiment, prepared_by_item)
        session = ListeningSessionManifest(
            session_id=session_id,
            experiment_commitment_sha256=commitment,
            randomization_algorithm=RANDOMIZATION_ALGORITHM,
            target_integrated_lufs=experiment.target_integrated_lufs,
            max_true_peak_dbtp=experiment.max_true_peak_dbtp,
            trials=trials,
            artifact_flags=tuple(ListeningArtifactFlag),
            instructions=(
                "Use the same playback device and level for every option.",
                "Rate what you hear; candidate identities remain hidden until the session closes.",
                "Objective measurements are diagnostic and cannot approve a processor.",
                "Flag critical artifacts even when you otherwise prefer an option.",
            ),
        )
        reveals = tuple(prepared.reveal for item in experiment.items for prepared in prepared_by_item[item.item_id])
        item_reveals = tuple(
            ListeningItemReveal(
                trial_id=prepared_by_item[item.item_id][0].trial_id,
                item_id=item.item_id,
                source_fixture_id=item.source_fixture_id,
                source_sha256=item.source_sha256,
                source_region_ids=item.source_region_ids,
                segment_start_us=item.segment_start_us,
                segment_end_us=item.segment_end_us,
                evaluation_prompt=item.evaluation_prompt,
            )
            for item in experiment.items
        )
        objective_metrics = _objective_metrics(experiment, prepared_by_item)
        prepared = PreparedListeningExperiment(
            prepared_experiment_id=_stable_id("prepared-listening", commitment, session_id),
            experiment_commitment_sha256=commitment,
            experiment=experiment,
            session=session,
            identity_reveals=reveals,
            item_reveals=item_reveals,
            objective_metrics=objective_metrics,
        )
        state = ListeningSessionState(
            session_id=session_id,
            state="open",
            next_submission_sequence=1,
        )
        write_manifest(public / "session.json", session)
        (public / "index.html").write_text(INDEX_HTML, encoding="utf-8")
        write_manifest(private / "prepared-experiment.json", prepared)
        write_manifest(private / "state.json", state)
        shutil.rmtree(diagnostics_directory)
        shutil.rmtree(segments_directory)
        _verify_archived_candidates_unchanged(experiment, candidate_paths)
        if destination.exists():
            raise FileExistsError(
                f"refusing to overwrite listening workspace created during preparation: {destination}"
            )
        temporary.replace(destination)
        return prepared
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def _resolve_candidates(experiment: ListeningExperimentManifest, base: Path) -> dict[str, Path]:
    resolved: dict[str, Path] = {}
    for candidate in experiment.candidates:
        path = (base / candidate.relative_path).resolve(strict=True)
        if not path.is_relative_to(base) or not path.is_file():
            raise ListeningLabError("Listening candidates must be regular files beneath the experiment directory.")
        if sha256_file(path) != candidate.archived_sha256:
            raise ListeningLabError(f"Archived candidate hash mismatch for {candidate.candidate_id}.")
        resolved[candidate.candidate_id] = path
    return resolved


def _validate_prompts_do_not_reveal_identities(experiment: ListeningExperimentManifest) -> None:
    sensitive = {
        token.lower()
        for candidate in experiment.candidates
        for token in (
            candidate.candidate_id,
            candidate.processor_id,
            candidate.recipe_version_id,
            Path(candidate.relative_path).name,
            *candidate.model_manifest_ids,
        )
        if token
    }
    sensitive.update(
        token.lower()
        for item in experiment.items
        for token in (item.source_fixture_id, item.source_sha256, *item.source_region_ids)
    )
    for item in experiment.items:
        prompt = item.evaluation_prompt.lower()
        if any(token in prompt for token in sensitive):
            raise ListeningLabError("Evaluation prompts cannot expose candidate, source, region, or filename identity.")


def _validate_original_hashes(experiment: ListeningExperimentManifest) -> None:
    candidates = {candidate.candidate_id: candidate for candidate in experiment.candidates}
    for item in experiment.items:
        source_controls = [
            candidates[candidate_id]
            for candidate_id in item.candidate_ids
            if candidates[candidate_id].role in {ListeningCandidateRole.ORIGINAL, ListeningCandidateRole.REFERENCE}
        ]
        if source_controls and all(candidate.archived_sha256 != item.source_sha256 for candidate in source_controls):
            raise ListeningLabError(
                "Item source_sha256 must match its original/reference candidate when one is present."
            )


def _segment_source(
    source: Path,
    *,
    candidate: ListeningExperimentCandidate,
    item: ListeningExperimentItem,
    destination: Path,
    tools: FFmpegTools,
) -> Path:
    if item.segment_start_us == 0 and item.segment_end_us is None:
        return source
    probe = probe_media(
        source,
        source_asset_id=_stable_id("asset", candidate.archived_sha256),
        probe_id=_stable_id("probe", candidate.archived_sha256),
        tools=tools,
    )
    end_us = item.segment_end_us if item.segment_end_us is not None else probe.duration_us
    if end_us > probe.duration_us:
        raise ListeningLabError("A requested listening segment exceeds a candidate duration.")
    output = destination / f"{item.item_id.replace(':', '-')}-{candidate.candidate_id.replace(':', '-')}.wav"
    command = [
        tools.ffmpeg,
        "-nostdin",
        "-hide_banner",
        "-loglevel",
        "error",
        "-protocol_whitelist",
        "file,pipe",
        "-i",
        str(source),
        "-ss",
        f"{item.segment_start_us / 1_000_000:.6f}",
        "-t",
        f"{(end_us - item.segment_start_us) / 1_000_000:.6f}",
        "-map",
        "0:a:0",
        "-vn",
        "-map_metadata",
        "-1",
        "-ar",
        "48000",
        "-c:a",
        "pcm_s24le",
        "-y",
        str(output),
    ]
    try:
        completed = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=7_200,
            env=subprocess_environment(),
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ListeningLabError("FFmpeg could not create a requested listening segment.") from error
    if completed.returncode != 0:
        raise ListeningLabError("FFmpeg could not create a requested listening segment.")
    return output


def _listening_recipe(experiment: ListeningExperimentManifest) -> RecipeVersion:
    return RecipeVersion(
        recipe_version_id=_stable_id(
            "recipe-version",
            "listening-loudness-match:1.0.0",
            f"{experiment.target_integrated_lufs:.6f}",
            f"{experiment.max_true_peak_dbtp:.6f}",
        ),
        slug="listening-loudness-match",
        recipe_version="1.0.0",
        display_name="Listening loudness match",
        description="Linear two-pass loudness matching for blinded local comparison copies.",
        analysis_steps=("measure-loudness",),
        processing_steps=("loudness-match-only",),
        target_integrated_lufs=experiment.target_integrated_lufs,
        max_true_peak_dbtp=experiment.max_true_peak_dbtp,
        target_loudness_range_lu=30.0,
        output_formats=("wav",),
    )


def _validate_listening_loudness(
    integrated_lufs: float, true_peak_dbtp: float, experiment: ListeningExperimentManifest
) -> None:
    if abs(integrated_lufs - experiment.target_integrated_lufs) > LOUDNESS_TOLERANCE_LU:
        raise ListeningLabError("A listening copy missed the configured loudness-match tolerance.")
    if true_peak_dbtp > experiment.max_true_peak_dbtp + TRUE_PEAK_TOLERANCE_DB:
        raise ListeningLabError("A listening copy exceeded the configured true-peak tolerance.")


def _public_trials(
    experiment: ListeningExperimentManifest,
    prepared_by_item: dict[str, list[_PreparedCandidate]],
) -> tuple[ListeningTrial, ...]:
    trials: list[ListeningTrial] = []
    for item in experiment.items:
        prepared = prepared_by_item[item.item_id]
        ordered = sorted(
            prepared,
            key=lambda value: _digest(
                str(experiment.randomization_seed),
                "option-order",
                item.item_id,
                value.candidate.candidate_id,
            ),
        )
        trials.append(
            ListeningTrial(
                trial_id=prepared[0].trial_id,
                source_token=_stable_id("source-token", str(experiment.randomization_seed), item.source_fixture_id),
                mode=item.mode,
                evaluation_prompt=item.evaluation_prompt,
                options=tuple(value.option for value in ordered),
            )
        )
    return tuple(
        sorted(
            trials,
            key=lambda trial: _digest(str(experiment.randomization_seed), "trial-order", trial.trial_id),
        )
    )


def _objective_metrics(
    experiment: ListeningExperimentManifest,
    prepared_by_item: dict[str, list[_PreparedCandidate]],
) -> tuple[ListeningObjectiveMetrics, ...]:
    metrics: list[ListeningObjectiveMetrics] = []
    for item in experiment.items:
        prepared = prepared_by_item[item.item_id]
        reference = next(
            (
                value
                for role in (ListeningCandidateRole.ORIGINAL, ListeningCandidateRole.REFERENCE)
                for value in prepared
                if value.candidate.role is role
            ),
            None,
        )
        for value in prepared:
            pcm = measure_pcm(value.raw_diagnostic_path)
            snr_db: float | None = None
            si_sdr_db: float | None = None
            if reference is not None and reference.candidate.candidate_id != value.candidate.candidate_id:
                snr_db, si_sdr_db = full_reference_metrics(
                    reference.raw_diagnostic_path,
                    reference.option.channels,
                    value.raw_diagnostic_path,
                    value.option.channels,
                )
            metrics.append(
                ListeningObjectiveMetrics(
                    item_id=item.item_id,
                    candidate_id=value.candidate.candidate_id,
                    archived_sha256=value.candidate.archived_sha256,
                    listening_sha256=value.option.listening_sha256,
                    loudness_before=value.loudness_before,
                    loudness_after=value.option.loudness,
                    duration_us=value.option.duration_us,
                    sample_rate_hz=value.option.sample_rate_hz,
                    channels=value.option.channels,
                    loudness_hop_us=100_000,
                    loudness_frame_count=value.loudness_frame_count,
                    momentary_lufs_min=value.momentary_lufs_min,
                    momentary_lufs_max=value.momentary_lufs_max,
                    short_term_lufs_min=value.short_term_lufs_min,
                    short_term_lufs_max=value.short_term_lufs_max,
                    sample_peak_dbfs=pcm.sample_peak_dbfs,
                    clipping_sample_count=pcm.clipping_sample_count,
                    snr_db=snr_db,
                    si_sdr_db=si_sdr_db,
                    runtime=value.candidate.runtime,
                )
            )
    return tuple(metrics)


def _verify_archived_candidates_unchanged(
    experiment: ListeningExperimentManifest,
    paths: dict[str, Path],
) -> None:
    for candidate in experiment.candidates:
        if sha256_file(paths[candidate.candidate_id]) != candidate.archived_sha256:
            raise ListeningLabError("An archived candidate changed during listening preparation.")


def _stable_id(prefix: str, *parts: str) -> str:
    return f"{prefix}:{_digest(*parts)[:24]}"


def _digest(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
