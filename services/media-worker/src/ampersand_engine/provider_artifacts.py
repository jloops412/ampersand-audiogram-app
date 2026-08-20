from __future__ import annotations

import json
from pathlib import Path, PurePosixPath

from ampersand_contracts import ProviderNativeArtifactManifest

from .hashing import sha256_file, stable_id
from .semantic_types import JsonValue


def write_provider_artifact(
    root: Path,
    *,
    relative_path: str,
    payload: dict[str, JsonValue],
    provider_id: str,
    provider_version: str,
    adapter_id: str,
    adapter_version: str,
    redaction_summary: str,
    contains_transcript_text: bool = False,
) -> ProviderNativeArtifactManifest:
    portable = PurePosixPath(relative_path)
    if portable.is_absolute() or ".." in portable.parts:
        raise ValueError("provider artifact path must be portable and relative")
    target = root.joinpath(*portable.parts)
    target.parent.mkdir(parents=True, exist_ok=True)
    serialized = (
        json.dumps(
            payload,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )
    target.write_bytes(serialized)
    digest = sha256_file(target)
    return ProviderNativeArtifactManifest(
        artifact_id=stable_id("provider-artifact", digest, length=24),
        provider_id=provider_id,
        provider_version=provider_version,
        adapter_id=adapter_id,
        adapter_version=adapter_version,
        relative_path=portable.as_posix(),
        sha256=digest,
        size_bytes=len(serialized),
        mime_type="application/json",
        redaction_summary=redaction_summary,
        contains_transcript_text=contains_transcript_text,
    )
