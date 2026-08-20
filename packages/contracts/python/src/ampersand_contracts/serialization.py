from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from pydantic import BaseModel


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
