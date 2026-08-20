from __future__ import annotations

import hashlib
import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from .models import SemanticMap


def canonical_json_bytes(model: BaseModel) -> bytes:
    """Serialize a contract identically across runs and platforms."""

    payload = model.model_dump(mode="json", exclude_none=True)
    return json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def manifest_sha256(model: BaseModel) -> str:
    return hashlib.sha256(canonical_json_bytes(model)).hexdigest()


def write_manifest(path: Path, model: BaseModel) -> str:
    """Atomically write a canonical manifest and return its SHA-256."""

    path.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_json_bytes(model) + b"\n"
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_bytes(payload)
    os.replace(temporary, path)
    return hashlib.sha256(payload.rstrip(b"\n")).hexdigest()


def read_manifest[ModelT: BaseModel](path: Path, model_type: type[ModelT]) -> ModelT:
    return model_type.model_validate_json(path.read_bytes())


def read_semantic_map(path: Path) -> SemanticMap:
    """Read Semantic Map 1.1, explicitly upgrading the issue-21 placeholder when needed."""

    try:
        payload: Any = json.loads(path.read_bytes())
    except json.JSONDecodeError as error:
        raise ValueError("semantic map is not valid JSON") from error
    if not isinstance(payload, dict):
        raise ValueError("semantic map must be a JSON object")
    migrated = migrate_semantic_map_payload(payload)
    return SemanticMap.model_validate(migrated)


def migrate_semantic_map_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Upgrade the protected issue-21 Semantic Map 1.0 placeholder to schema 1.1."""

    version = payload.get("schema_version")
    if version == "1.1.0":
        return deepcopy(payload)
    if version != "1.0.0":
        raise ValueError(f"unsupported semantic-map schema_version: {version!r}")

    migrated = deepcopy(payload)
    migrated["schema_version"] = "1.1.0"
    migrated["semantic_map_version"] = "0.1.0"
    duration_us = migrated.get("duration_us")
    if not isinstance(duration_us, int) or duration_us <= 0:
        raise ValueError("legacy semantic map has no positive duration_us")
    migrated["analysis_hop_us"] = duration_us
    migrated["provenance_sources"] = []
    migrated["observations"] = []
    migrated["conflicts"] = []
    migrated["unavailable_adapters"] = []
    migrated["coverage"] = "full"
    warnings = migrated.setdefault("warnings", [])
    if not isinstance(warnings, list):
        raise ValueError("legacy semantic map warnings must be a list")
    warnings.append("Explicitly migrated from the protected issue-21 Semantic Map 1.0 placeholder.")

    regions = migrated.get("regions")
    if not isinstance(regions, list):
        raise ValueError("legacy semantic map regions must be a list")
    for region in regions:
        if not isinstance(region, dict):
            raise ValueError("legacy semantic map region must be an object")
        region["schema_version"] = "1.1.0"
        region["processing_eligibility"] = "protect" if region.get("protected", True) else "eligible"
        region["observation_ids"] = []
        region["conflict_ids"] = []
    return migrated
