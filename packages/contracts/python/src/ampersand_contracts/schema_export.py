from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from .models import (
    AnalysisManifest,
    AssetManifest,
    DependencyManifest,
    GainEnvelope,
    JobStep,
    MediaProbe,
    ModelManifest,
    OutputManifest,
    ProcessingPlan,
    ProcessingRegion,
    ProcessingReport,
    Production,
    ProductionRun,
    RecipeVersion,
    SemanticMap,
    SemanticRegion,
    WaveformPeaks,
)

EXPORTED_MODELS: tuple[type[BaseModel], ...] = (
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
