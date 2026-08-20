from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from ampersand_contracts import (
    CandidateListeningSummary,
    ListeningArtifactFlag,
    ListeningCandidateRole,
    ListeningReport,
    ListeningScore,
    ListeningSessionManifest,
    ListeningSessionState,
    PreparedListeningExperiment,
    manifest_sha256,
    read_manifest,
    write_manifest,
)
from ampersand_engine.hashing import sha256_file

from .errors import ListeningLabError


def submit_score(workspace: Path, payload: dict[str, Any]) -> ListeningScore:
    workspace = workspace.expanduser().resolve(strict=True)
    session = _load_session(workspace)
    state = _load_state(workspace)
    if state.state != "open":
        raise ListeningLabError("This listening session is closed.")
    trial_id = payload.get("trial_id")
    trial = next((trial for trial in session.trials if trial.trial_id == trial_id), None)
    if trial is None:
        raise ListeningLabError("The submitted trial does not belong to this session.")
    listener_id = payload.get("listener_id")
    existing = _load_scores(workspace)
    if any(score.listener_id == listener_id and score.trial_id == trial.trial_id for score in existing):
        raise ListeningLabError("This listener already submitted a score for the trial.")
    sequence = max((score.submission_sequence for score in existing), default=0) + 1
    normalized = dict(payload)
    normalized.update(
        {
            "score_id": _stable_id(
                "listening-score", session.session_id, str(listener_id), trial.trial_id, str(sequence)
            ),
            "session_id": session.session_id,
            "trial_id": trial.trial_id,
            "mode": trial.mode.value,
            "submission_sequence": sequence,
        }
    )
    score = ListeningScore.model_validate(normalized)
    presented = {option.option_id for option in trial.options}
    rated = {rating.option_id for rating in score.option_ratings}
    if rated != presented:
        raise ListeningLabError("A score must rate every presented option exactly once.")
    allowed_flags = set(session.artifact_flags)
    if not set(score.trial_artifact_flags) <= allowed_flags or any(
        not set(rating.artifact_flags) <= allowed_flags for rating in score.option_ratings
    ):
        raise ListeningLabError("A score contains an artifact flag outside the session taxonomy.")

    score_path = workspace / "private/scores" / f"{score.score_id.replace(':', '-')}.json"
    if score_path.exists():
        raise ListeningLabError("The score identity already exists.")
    write_manifest(score_path, score)
    all_scores = tuple(sorted((*existing, score), key=lambda value: value.submission_sequence))
    updated_state = ListeningSessionState(
        session_id=session.session_id,
        state="open",
        next_submission_sequence=sequence + 1,
        score_ids=tuple(value.score_id for value in all_scores),
    )
    write_manifest(workspace / "private/state.json", updated_state)
    return score


def close_session(workspace: Path) -> ListeningReport:
    workspace = workspace.expanduser().resolve(strict=True)
    state = _load_state(workspace)
    report_path = workspace / "report.json"
    if state.state == "closed":
        return load_report(workspace)
    if report_path.exists():
        recovered = read_manifest(report_path, ListeningReport)
        recovered_state = ListeningSessionState(
            session_id=state.session_id,
            state="closed",
            next_submission_sequence=state.next_submission_sequence,
            score_ids=state.score_ids,
            report_sha256=sha256_file(report_path),
        )
        write_manifest(workspace / "private/state.json", recovered_state)
        return recovered

    prepared = read_manifest(workspace / "private/prepared-experiment.json", PreparedListeningExperiment)
    scores = _load_scores(workspace)
    report = _build_report(prepared, scores)
    write_manifest(report_path, report)
    report_hash = sha256_file(report_path)
    closed_state = ListeningSessionState(
        session_id=state.session_id,
        state="closed",
        next_submission_sequence=max((score.submission_sequence for score in scores), default=0) + 1,
        score_ids=tuple(score.score_id for score in scores),
        report_sha256=report_hash,
    )
    write_manifest(workspace / "private/state.json", closed_state)
    return report


def load_report(workspace: Path) -> ListeningReport:
    workspace = workspace.expanduser().resolve(strict=True)
    state = _load_state(workspace)
    if state.state != "closed":
        raise ListeningLabError("Candidate identities remain hidden until the session closes.")
    report_path = workspace / "report.json"
    if not report_path.is_file() or sha256_file(report_path) != state.report_sha256:
        raise ListeningLabError("The closed listening report is missing or failed integrity validation.")
    return read_manifest(report_path, ListeningReport)


def session_status(workspace: Path) -> dict[str, Any]:
    workspace = workspace.expanduser().resolve(strict=True)
    state = _load_state(workspace)
    scores = _load_scores(workspace)
    return {
        "session_id": state.session_id,
        "state": state.state,
        "score_count": len(scores),
        "submitted_trial_ids": sorted({score.trial_id for score in scores}),
    }


def _load_session(workspace: Path) -> ListeningSessionManifest:
    return read_manifest(workspace / "public/session.json", ListeningSessionManifest)


def _load_state(workspace: Path) -> ListeningSessionState:
    return read_manifest(workspace / "private/state.json", ListeningSessionState)


def _load_scores(workspace: Path) -> tuple[ListeningScore, ...]:
    scores = tuple(
        read_manifest(path, ListeningScore) for path in sorted((workspace / "private/scores").glob("*.json"))
    )
    sequences = [score.submission_sequence for score in scores]
    if len(sequences) != len(set(sequences)):
        raise ListeningLabError("Listening score submission sequences are not unique.")
    return tuple(sorted(scores, key=lambda score: score.submission_sequence))


def _build_report(
    prepared: PreparedListeningExperiment,
    scores: tuple[ListeningScore, ...],
) -> ListeningReport:
    experiment = prepared.experiment
    session = prepared.session
    reveals = {(reveal.trial_id, reveal.option_id): reveal for reveal in prepared.identity_reveals}
    candidate_ids = [candidate.candidate_id for candidate in experiment.candidates]
    exposures: Counter[str] = Counter()
    wins: Counter[str] = Counter()
    speech: defaultdict[str, list[int]] = defaultdict(list)
    background: defaultdict[str, list[int]] = defaultdict(list)
    overall: defaultdict[str, list[int]] = defaultdict(list)
    artifacts: defaultdict[str, Counter[ListeningArtifactFlag]] = defaultdict(Counter)
    clean_degradation: Counter[str] = Counter()
    clean_preferred: Counter[str] = Counter()

    for score in scores:
        for rating in score.option_ratings:
            reveal = reveals[(score.trial_id, rating.option_id)]
            candidate_id = reveal.candidate_id
            exposures[candidate_id] += 1
            speech[candidate_id].append(rating.speech_quality)
            background[candidate_id].append(rating.background_quality)
            overall[candidate_id].append(rating.overall_quality)
            artifacts[candidate_id].update(rating.artifact_flags)
        if score.preferred_option_id is not None:
            wins[reveals[(score.trial_id, score.preferred_option_id)].candidate_id] += 1
        if score.mode.value == "clean_preservation":
            processed = next(
                reveal
                for reveal in prepared.identity_reveals
                if reveal.trial_id == score.trial_id and reveal.role is ListeningCandidateRole.CANDIDATE
            )
            if score.audible_degradation:
                clean_degradation[processed.candidate_id] += 1
            if score.processing_preferred:
                clean_preferred[processed.candidate_id] += 1

    summaries = tuple(
        CandidateListeningSummary(
            candidate_id=candidate_id,
            exposures=exposures[candidate_id],
            preference_wins=wins[candidate_id],
            mean_speech_quality=_mean(speech[candidate_id]),
            mean_background_quality=_mean(background[candidate_id]),
            mean_overall_quality=_mean(overall[candidate_id]),
            artifact_flag_counts=dict(sorted(artifacts[candidate_id].items(), key=lambda item: item[0].value)),
            clean_audible_degradation_count=clean_degradation[candidate_id],
            clean_processing_preferred_count=clean_preferred[candidate_id],
        )
        for candidate_id in candidate_ids
    )
    score_identity = "|".join(manifest_sha256(score) for score in scores) or "no-scores"
    warnings: list[str] = [
        "This is a descriptive pilot report; it cannot automatically promote a processor or recipe.",
        "Objective diagnostics are context only and are not combined into an approval score.",
    ]
    if not scores:
        warnings.append("The session closed without any listener scores.")
    covered_trials = {score.trial_id for score in scores}
    if len(covered_trials) < len(session.trials):
        warnings.append("At least one trial received no listener score.")
    external_cost = sum(candidate.runtime.external_cost_usd for candidate in experiment.candidates)
    return ListeningReport(
        listening_report_id=_stable_id("listening-report", session.session_id, score_identity),
        experiment_id=experiment.experiment_id,
        experiment_version=experiment.experiment_version,
        corpus_id=experiment.corpus_id,
        corpus_version=experiment.corpus_version,
        session_id=session.session_id,
        experiment_commitment_sha256=prepared.experiment_commitment_sha256,
        scores=scores,
        identity_reveals=prepared.identity_reveals,
        item_reveals=prepared.item_reveals,
        objective_metrics=prepared.objective_metrics,
        candidate_summaries=summaries,
        trial_count=len(session.trials),
        score_count=len(scores),
        no_preference_count=sum(score.no_meaningful_preference for score in scores),
        uncertainty_summary=(
            "Small internal pilot: report raw counts, per-candidate descriptive means, and per-item failures. "
            "No confidence interval or population-level inference is claimed until listener/item counts support it."
        ),
        human_approval_status="pilot_only" if scores else "not_evaluated",
        external_api_cost_usd=round(external_cost, 6),
        warnings=tuple(warnings),
    )


def _mean(values: list[int]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 6)


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return f"{prefix}:{digest[:24]}"
