from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from .models import (
    AdaptiveLevelerSettings,
    AnalysisManifest,
    AssetManifest,
    AudiogramSettings,
    CandidateListeningSummary,
    CleanupSettings,
    DependencyManifest,
    EvidenceProvenance,
    ExportSettings,
    FixtureAssetManifest,
    FixtureCorpusManifest,
    FixtureRegion,
    FixtureTransform,
    GainEnvelope,
    GainRenderManifest,
    GainRenderRuntimeReport,
    JobStep,
    LevelerStatistics,
    ListeningExperimentCandidate,
    ListeningExperimentItem,
    ListeningExperimentManifest,
    ListeningIdentityReveal,
    ListeningItemReveal,
    ListeningObjectiveMetrics,
    ListeningOption,
    ListeningOptionRating,
    ListeningReport,
    ListeningRuntimeMetrics,
    ListeningScore,
    ListeningSessionManifest,
    ListeningSessionState,
    ListeningTrial,
    MasteringSettings,
    MediaProbe,
    ModelManifest,
    OutputManifest,
    OutputMetadataSettings,
    PreparedListeningExperiment,
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
    ProviderNativeArtifactManifest,
    RecipeVersion,
    ResolvedProductionSettings,
    SemanticConflict,
    SemanticMap,
    SemanticObservation,
    SemanticRegion,
    SignificantGainCorrection,
    SpeakerLevelStatistics,
    StudioTemplate,
    StudioTemplateVersion,
    WaveformPeaks,
)

EXPORTED_MODELS: tuple[type[BaseModel], ...] = (
    AssetManifest,
    ProviderNativeArtifactManifest,
    MediaProbe,
    Production,
    ProductionRun,
    JobStep,
    RecipeVersion,
    MasteringSettings,
    CleanupSettings,
    OutputMetadataSettings,
    AudiogramSettings,
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
    ListeningRuntimeMetrics,
    ListeningExperimentCandidate,
    ListeningExperimentItem,
    ListeningExperimentManifest,
    ListeningOption,
    ListeningTrial,
    ListeningSessionManifest,
    ListeningOptionRating,
    ListeningScore,
    ListeningSessionState,
    ListeningObjectiveMetrics,
    ListeningIdentityReveal,
    ListeningItemReveal,
    PreparedListeningExperiment,
    CandidateListeningSummary,
    ListeningReport,
    EvidenceProvenance,
    SemanticObservation,
    SemanticConflict,
    SemanticMap,
    SemanticRegion,
    ProcessingPlan,
    ProcessingRegion,
    ProcessingRouterSettings,
    ProcessingRouteOverride,
    ProcessingRouteDecision,
    ProcessingRouterReport,
    GainEnvelope,
    GainRenderManifest,
    GainRenderRuntimeReport,
    ProcessingReport,
    OutputManifest,
    ModelManifest,
    DependencyManifest,
    AnalysisManifest,
    WaveformPeaks,
)


def export_json_schemas(destination: Path) -> tuple[Path, ...]:
    destination.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for model_type in EXPORTED_MODELS:
        filename = _kebab_case(model_type.__name__) + ".schema.json"
        target = destination / filename
        target.write_text(
            json.dumps(model_type.model_json_schema(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        written.append(target)
    return tuple(written)


def _kebab_case(value: str) -> str:
    parts: list[str] = []
    current = ""
    for character in value:
        if character.isupper() and current:
            parts.append(current.lower())
            current = character
        else:
            current += character
    if current:
        parts.append(current.lower())
    return "-".join(parts)
