from __future__ import annotations

import json
import shutil
import threading
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import pytest
from ampersand_contracts import (
    ListeningCandidateRole,
    ListeningExperimentCandidate,
    ListeningExperimentItem,
    ListeningExperimentManifest,
    ListeningMode,
    ListeningRuntimeMetrics,
    PreparedListeningExperiment,
    write_manifest,
)
from ampersand_engine.hashing import sha256_file
from ampersand_listening.errors import ListeningLabError
from ampersand_listening.prepare import LOUDNESS_TOLERANCE_LU, prepare_experiment
from ampersand_listening.server import build_server
from ampersand_listening.store import close_session, load_report, session_status, submit_score
from ampersand_test_fixtures import generate_fixture_corpus
from pydantic import ValidationError


@pytest.fixture(scope="module")
def prepared_pair(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path, Path, PreparedListeningExperiment]:
    root = tmp_path_factory.mktemp("listening-harness")
    corpus_directory = root / "corpus"
    corpus = generate_fixture_corpus(
        corpus_directory,
        fixture_ids=("fixture:hvac-snr12-validation", "fixture:hum-60-validation"),
    )
    by_id = {fixture.fixture_id: fixture for fixture in corpus.fixtures}
    original = by_id["fixture:clean-voice-validation"]
    candidate = by_id["fixture:hvac-snr12-validation"]
    alternate = by_id["fixture:hum-60-validation"]
    experiment = ListeningExperimentManifest(
        experiment_id="listening-experiment:clean-preservation-control",
        experiment_version="0.1.0",
        corpus_id=corpus.corpus_id,
        corpus_version=corpus.corpus_version,
        randomization_seed=41_911,
        target_integrated_lufs=-20.0,
        max_true_peak_dbtp=-1.5,
        candidates=(
            ListeningExperimentCandidate(
                candidate_id="listening-candidate:original-control",
                relative_path=f"audio/{original.filename}",
                archived_sha256=original.sha256,
                role=ListeningCandidateRole.ORIGINAL,
                source_fixture_id=original.fixture_id,
                processor_id="processor:identity-control",
                processor_version="1.0.0",
                engine_build_id="engine:fixture-generator-0.2.0",
                runtime=_runtime(0.01),
                notes="Immutable synthetic clean-input control.",
            ),
            ListeningExperimentCandidate(
                candidate_id="listening-candidate:noise-control",
                relative_path=f"audio/{candidate.filename}",
                archived_sha256=candidate.sha256,
                role=ListeningCandidateRole.CANDIDATE,
                source_fixture_id=original.fixture_id,
                processor_id="processor:deterministic-noise-control",
                processor_version="0.1.0",
                recipe_version_id="recipe:noise-control:0.1.0",
                engine_build_id="engine:fixture-generator-0.2.0",
                runtime=_runtime(0.02),
                notes="Immutable synthetic degraded comparison control.",
            ),
            ListeningExperimentCandidate(
                candidate_id="listening-candidate:hum-control",
                relative_path=f"audio/{alternate.filename}",
                archived_sha256=alternate.sha256,
                role=ListeningCandidateRole.CANDIDATE,
                source_fixture_id=original.fixture_id,
                processor_id="processor:deterministic-hum-control",
                processor_version="0.1.0",
                recipe_version_id="recipe:hum-control:0.1.0",
                engine_build_id="engine:fixture-generator-0.2.0",
                runtime=_runtime(0.02),
                notes="Immutable synthetic alternate comparison control.",
            ),
        ),
        items=(
            ListeningExperimentItem(
                item_id="listening-item:clean-preservation-control",
                mode=ListeningMode.CLEAN_PRESERVATION,
                source_fixture_id=original.fixture_id,
                source_sha256=original.sha256,
                source_region_ids=tuple(region.fixture_region_id for region in original.regions),
                candidate_ids=(
                    "listening-candidate:original-control",
                    "listening-candidate:noise-control",
                ),
                evaluation_prompt=(
                    "Compare speech naturalness, background quality, and preservation of the clean signal."
                ),
            ),
            ListeningExperimentItem(
                item_id="listening-item:original-a-b-control",
                mode=ListeningMode.PAIRWISE_PREFERENCE,
                source_fixture_id=original.fixture_id,
                source_sha256=original.sha256,
                source_region_ids=tuple(region.fixture_region_id for region in original.regions),
                candidate_ids=(
                    "listening-candidate:original-control",
                    "listening-candidate:noise-control",
                    "listening-candidate:hum-control",
                ),
                evaluation_prompt="Choose among the original and two processed controls without using identities.",
            ),
        ),
        prohibited_sources=(
            "hosted_processor_service",
            "hosted_processor_output",
            "production_customer_media",
        ),
        hypothesis="The degraded control should not pass a clean-input preservation comparison.",
    )
    manifest_path = corpus_directory / "listening-experiment.json"
    write_manifest(manifest_path, experiment)
    archived_before = {candidate.candidate_id: candidate.archived_sha256 for candidate in experiment.candidates}

    first = root / "prepared-first"
    second = root / "prepared-second"
    prepared = prepare_experiment(manifest_path, first)
    repeated = prepare_experiment(manifest_path, second)
    assert prepared == repeated
    assert {
        candidate.candidate_id: sha256_file(corpus_directory / candidate.relative_path)
        for candidate in experiment.candidates
    } == archived_before
    return first, second, manifest_path, prepared


def test_preparation_is_deterministic_loudness_matched_and_identity_opaque(
    prepared_pair: tuple[Path, Path, Path, PreparedListeningExperiment],
) -> None:
    first, second, _manifest_path, prepared = prepared_pair
    first_audio = {path.name: path.read_bytes() for path in sorted((first / "public/audio").glob("*.wav"))}
    second_audio = {path.name: path.read_bytes() for path in sorted((second / "public/audio").glob("*.wav"))}
    assert first_audio == second_audio
    assert len(first_audio) == 5
    assert not (first / "private/diagnostics").exists()
    assert not (first / "private/segments").exists()

    for trial in prepared.session.trials:
        for option in trial.options:
            assert abs(option.loudness.integrated_lufs - prepared.experiment.target_integrated_lufs) <= (
                LOUDNESS_TOLERANCE_LU
            )
            assert option.loudness.true_peak_dbtp <= prepared.experiment.max_true_peak_dbtp + 0.2
            assert option.audio_relative_path.startswith("audio/listening-option-")
    assert all(metric.diagnostic_only for metric in prepared.objective_metrics)
    assert all(metric.runtime.external_cost_usd == 0 for metric in prepared.objective_metrics)
    assert all(metric.loudness_frame_count == 80 for metric in prepared.objective_metrics)
    assert all(metric.momentary_lufs_min <= metric.momentary_lufs_max for metric in prepared.objective_metrics)
    assert all(metric.short_term_lufs_min <= metric.short_term_lufs_max for metric in prepared.objective_metrics)
    assert {trial.mode for trial in prepared.session.trials} == {
        ListeningMode.CLEAN_PRESERVATION,
        ListeningMode.PAIRWISE_PREFERENCE,
    }

    public_text = (first / "public/session.json").read_text(encoding="utf-8") + (first / "public/index.html").read_text(
        encoding="utf-8"
    )
    for candidate in prepared.experiment.candidates:
        assert candidate.candidate_id not in public_text
        assert candidate.processor_id not in public_text
        assert Path(candidate.relative_path).name not in public_text
    assert not (first / "report.json").exists()


def test_scoring_stays_blind_until_close_and_report_is_descriptive(
    prepared_pair: tuple[Path, Path, Path, PreparedListeningExperiment], tmp_path: Path
) -> None:
    source, _second, _manifest_path, prepared = prepared_pair
    workspace = _copy_workspace(source, tmp_path / "score-workspace")
    trial = next(trial for trial in prepared.session.trials if trial.mode is ListeningMode.CLEAN_PRESERVATION)
    candidate_option = next(
        reveal.option_id
        for reveal in prepared.identity_reveals
        if reveal.trial_id == trial.trial_id and reveal.role is ListeningCandidateRole.CANDIDATE
    )
    payload = _score_payload(prepared, preferred_option_id=candidate_option)

    with pytest.raises(ListeningLabError, match="hidden"):
        load_report(workspace)
    score = submit_score(workspace, payload)
    assert score.submission_sequence == 1
    assert session_status(workspace)["score_count"] == 1
    with pytest.raises(ListeningLabError, match="already submitted"):
        submit_score(workspace, payload)

    report = close_session(workspace)
    assert report.decision == "descriptive_pilot_only"
    assert report.human_approval_status == "pilot_only"
    assert report.objective_metrics_diagnostic_only
    assert report.external_api_cost_usd == 0
    assert report.score_count == 1
    assert len(report.identity_reveals) == 5
    assert len(report.item_reveals) == 2
    assert report.item_reveals[0].source_fixture_id == "fixture:clean-voice-validation"
    assert report.item_reveals[0].source_sha256 == prepared.experiment.items[0].source_sha256
    assert report.item_reveals[0].source_region_ids == prepared.experiment.items[0].source_region_ids
    candidate_summary = next(
        summary for summary in report.candidate_summaries if summary.candidate_id == "listening-candidate:noise-control"
    )
    assert candidate_summary.exposures == 1
    assert candidate_summary.preference_wins == 1
    assert candidate_summary.clean_audible_degradation_count == 1
    assert candidate_summary.artifact_flag_counts["musical_noise"] == 1
    assert load_report(workspace) == report
    assert close_session(workspace) == report
    with pytest.raises(ListeningLabError, match="closed"):
        submit_score(workspace, payload | {"listener_id": "listener:second"})

    (workspace / "report.json").write_bytes((workspace / "report.json").read_bytes() + b" ")
    with pytest.raises(ListeningLabError, match="integrity"):
        load_report(workspace)


def test_local_server_whitelists_public_assets_supports_ranges_and_reveals_after_close(
    prepared_pair: tuple[Path, Path, Path, PreparedListeningExperiment], tmp_path: Path
) -> None:
    source, _second, _manifest_path, prepared = prepared_pair
    workspace = _copy_workspace(source, tmp_path / "server-workspace")
    with pytest.raises(ListeningLabError, match="localhost"):
        build_server(workspace, host="0.0.0.0")

    server = build_server(workspace, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        status, headers, session_payload = _urlopen(f"{base}/session.json")
        assert status == 200
        assert headers["Cache-Control"] == "no-store"
        assert json.loads(session_payload)["identity_hidden"] is True

        with pytest.raises(urllib.error.HTTPError) as missing:
            urllib.request.urlopen(f"{base}/%2e%2e/private/prepared-experiment.json", timeout=5)
        assert missing.value.code == 404
        with pytest.raises(urllib.error.HTTPError) as hidden:
            urllib.request.urlopen(f"{base}/api/reveal", timeout=5)
        assert hidden.value.code == 409

        option_path = prepared.session.trials[0].options[0].audio_relative_path
        request = urllib.request.Request(f"{base}/{option_path}", headers={"Range": "bytes=0-127"})
        with urllib.request.urlopen(request, timeout=5) as response:
            assert response.status == 206
            assert response.headers["Content-Range"].startswith("bytes 0-127/")
            assert len(response.read()) == 128

        score_payload = json.dumps(_score_payload(prepared, mode=ListeningMode.PAIRWISE_PREFERENCE)).encode("utf-8")
        request = urllib.request.Request(
            f"{base}/api/scores",
            data=score_payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            assert response.status == 201

        request = urllib.request.Request(f"{base}/api/close", data=b"", method="POST")
        with urllib.request.urlopen(request, timeout=5) as response:
            assert response.status == 200
        status, _headers, reveal_payload = _urlopen(f"{base}/api/reveal")
        assert status == 200
        assert len(json.loads(reveal_payload)["identity_reveals"]) == 5
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_preparation_rejects_hash_mismatch_identity_leak_and_overwrite(
    prepared_pair: tuple[Path, Path, Path, PreparedListeningExperiment], tmp_path: Path
) -> None:
    _first, _second, manifest_path, experiment = prepared_pair
    with pytest.raises(FileExistsError, match="overwrite"):
        prepare_experiment(manifest_path, tmp_path)

    wrong_hash_candidates = list(experiment.experiment.candidates)
    wrong_hash_candidates[1] = wrong_hash_candidates[1].model_copy(update={"archived_sha256": "0" * 64})
    wrong_hash = experiment.experiment.model_copy(update={"candidates": tuple(wrong_hash_candidates)})
    wrong_hash_manifest = manifest_path.with_name("listening-experiment-wrong-hash.json")
    write_manifest(wrong_hash_manifest, wrong_hash)
    with pytest.raises(ListeningLabError, match="hash mismatch"):
        prepare_experiment(wrong_hash_manifest, tmp_path / "wrong-hash")

    leaky_item = experiment.experiment.items[0].model_copy(
        update={"evaluation_prompt": "Prefer processor:deterministic-noise-control when it sounds cleaner."}
    )
    leaky = experiment.experiment.model_copy(update={"items": (leaky_item, experiment.experiment.items[1])})
    leaky_manifest = manifest_path.with_name("listening-experiment-leaky.json")
    write_manifest(leaky_manifest, leaky)
    with pytest.raises(ListeningLabError, match="cannot expose"):
        prepare_experiment(leaky_manifest, tmp_path / "leaky")


def test_contracts_reject_commitment_metric_and_score_integrity_failures(
    prepared_pair: tuple[Path, Path, Path, PreparedListeningExperiment], tmp_path: Path
) -> None:
    source, _second, _manifest_path, prepared = prepared_pair

    tampered = prepared.model_dump(mode="json")
    tampered["experiment"]["hypothesis"] = "Changed after the experiment commitment was created."
    with pytest.raises(ValidationError, match="commitment"):
        PreparedListeningExperiment.model_validate(tampered)

    incomplete = prepared.model_dump(mode="json")
    incomplete["objective_metrics"] = incomplete["objective_metrics"][:-1]
    with pytest.raises(ValidationError, match="exactly cover"):
        PreparedListeningExperiment.model_validate(incomplete)

    workspace = _copy_workspace(source, tmp_path / "invalid-score-workspace")
    invalid_score = _score_payload(prepared)
    invalid_score["option_ratings"][0]["artifact_flags"] = ["musical_noise", "musical_noise"]
    with pytest.raises(ValidationError, match="unique"):
        submit_score(workspace, invalid_score)
    assert session_status(workspace)["score_count"] == 0


def _runtime(wall_seconds: float) -> ListeningRuntimeMetrics:
    return ListeningRuntimeMetrics(
        wall_seconds=wall_seconds,
        peak_memory_mb=1.0,
        device_summary="local synthetic control",
        external_cost_usd=0,
    )


def _copy_workspace(source: Path, destination: Path) -> Path:
    shutil.copytree(source, destination)
    return destination


def _score_payload(
    prepared: PreparedListeningExperiment,
    *,
    preferred_option_id: str | None = None,
    mode: ListeningMode = ListeningMode.CLEAN_PRESERVATION,
) -> dict[str, Any]:
    trial = next(trial for trial in prepared.session.trials if trial.mode is mode)
    preference = preferred_option_id or trial.options[0].option_id
    candidate_options = {
        reveal.option_id for reveal in prepared.identity_reveals if reveal.role is ListeningCandidateRole.CANDIDATE
    }
    payload: dict[str, Any] = {
        "listener_id": "listener:local-test",
        "trial_id": trial.trial_id,
        "preferred_option_id": preference,
        "no_meaningful_preference": False,
        "option_ratings": [
            {
                "option_id": option.option_id,
                "speech_quality": 2 if option.option_id in candidate_options else 5,
                "background_quality": 2 if option.option_id in candidate_options else 5,
                "overall_quality": 2 if option.option_id in candidate_options else 5,
                "artifact_flags": ["musical_noise"] if option.option_id in candidate_options else [],
            }
            for option in trial.options
        ],
        "confidence": 4,
        "trial_artifact_flags": [],
        "notes": "Synthetic control pilot.",
    }
    if mode is ListeningMode.CLEAN_PRESERVATION:
        payload.update(
            {
                "audible_degradation": True,
                "voice_identity_changed": False,
                "speech_less_natural": True,
                "ambience_or_music_changed": True,
                "processing_preferred": False,
            }
        )
    return payload


def _urlopen(url: str) -> tuple[int, Any, bytes]:
    with urllib.request.urlopen(url, timeout=5) as response:
        return response.status, response.headers, response.read()
