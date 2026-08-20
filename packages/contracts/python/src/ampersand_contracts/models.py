from __future__ import annotations

from enum import StrEnum
from pathlib import PurePosixPath
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

SCHEMA_VERSION: Literal["1.0.0"] = "1.0.0"

Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
Identifier = Annotated[str, StringConstraints(pattern=r"^[a-z0-9][a-z0-9._:-]{1,127}$")]
Microseconds = Annotated[int, Field(ge=0)]
Probability = Annotated[float, Field(ge=0.0, le=1.0)]
JsonScalar = str | int | float | bool | None


class ContractModel(BaseModel):
    """Strict, immutable base for Ampersand-owned serialized contracts."""

    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION


class AssetKind(StrEnum):
    SOURCE = "source"
    CANONICAL_AUDIO = "canonical_audio"
    WAVEFORM = "waveform"
    MASTER_WAV = "master_wav"
    MASTER_MP3 = "master_mp3"
    MANIFEST = "manifest"


class RunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BYPASSED = "bypassed"


class ManifestAdmissionState(StrEnum):
    UNREVIEWED = "unreviewed"
    LAB_CANDIDATE = "lab_candidate"
    PRODUCTION_CANDIDATE = "production_candidate"
    APPROVED = "approved"
    DEPRECATED = "deprecated"
    REVOKED = "revoked"


class AssetManifest(ContractModel):
    asset_id: Identifier
    kind: AssetKind
    uri: str = Field(min_length=1, max_length=1024)
    sha256: Sha256
    size_bytes: int = Field(ge=0)
    mime_type: str = Field(min_length=1, max_length=128)
    filename: str = Field(min_length=1, max_length=255)
    source_asset_id: Identifier | None = None
    created_by_step_id: Identifier | None = None
    retention_class: str = Field(default="local_fixture", min_length=1, max_length=64)
    provenance: dict[str, JsonScalar] = Field(default_factory=dict)


class MediaProbe(ContractModel):
    probe_id: Identifier
    source_asset_id: Identifier
    format_name: str = Field(min_length=1, max_length=128)
    codec_name: str = Field(min_length=1, max_length=64)
    sample_format: str | None = Field(default=None, max_length=64)
    duration_us: Microseconds
    sample_rate_hz: int = Field(gt=0, le=768_000)
    channels: int = Field(gt=0, le=64)
    channel_layout: str | None = Field(default=None, max_length=128)
    bit_rate_bps: int | None = Field(default=None, ge=0)
    ffprobe_version: str = Field(min_length=1, max_length=256)

    @model_validator(mode="after")
    def positive_duration(self) -> Self:
        if self.duration_us <= 0:
            raise ValueError("duration_us must be positive")
        return self


class Production(ContractModel):
    production_id: Identifier
    workspace_id: Identifier
    title: str = Field(min_length=1, max_length=160)
    source_asset_id: Identifier
    recipe_version_id: Identifier
    current_run_id: Identifier
    status: RunStatus


class ProductionRun(ContractModel):
    run_id: Identifier
    production_id: Identifier
    recipe_version_id: Identifier
    engine_build_id: Identifier
    idempotency_key: Sha256
    status: RunStatus
    step_ids: tuple[Identifier, ...]


class JobStep(ContractModel):
    step_id: Identifier
    run_id: Identifier
    step_key: Identifier
    implementation_version: str = Field(min_length=1, max_length=128)
    input_manifest_hash: Sha256
    idempotency_key: Sha256
    status: JobStatus
    attempt: int = Field(default=1, ge=1)
    output_manifest_ids: tuple[Identifier, ...] = ()
    metrics: dict[str, JsonScalar] = Field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    failure_code: str | None = Field(default=None, max_length=128)


class RecipeVersion(ContractModel):
    recipe_version_id: Identifier
    slug: Identifier
    recipe_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    display_name: str = Field(min_length=1, max_length=128)
    description: str = Field(min_length=1, max_length=512)
    analysis_steps: tuple[Identifier, ...]
    processing_steps: tuple[Identifier, ...]
    target_integrated_lufs: float = Field(ge=-70.0, le=-5.0)
    max_true_peak_dbtp: float = Field(ge=-12.0, le=0.0)
    target_loudness_range_lu: float = Field(ge=1.0, le=30.0)
    output_formats: tuple[Literal["wav", "mp3"], ...]
    dependency_manifest_ids: tuple[Identifier, ...] = ()
    model_manifest_ids: tuple[Identifier, ...] = ()
    allows_neural_processing: bool = False
    preserves_source: Literal[True] = True


class SemanticRegion(ContractModel):
    region_id: Identifier
    start_us: Microseconds
    end_us: Microseconds
    content_label: Literal["unknown", "speech", "silence", "music", "ambience", "noise", "mixed"]
    confidence: Probability
    speech_probability: Probability | None = None
    music_probability: Probability | None = None
    silence_probability: Probability | None = None
    protected: bool = True
    observations: dict[str, JsonScalar] = Field(default_factory=dict)
    provider_refs: tuple[str, ...] = ()

    @model_validator(mode="after")
    def half_open_interval(self) -> Self:
        if self.end_us <= self.start_us:
            raise ValueError("semantic regions use non-empty half-open [start_us, end_us) intervals")
        return self


class SemanticMap(ContractModel):
    semantic_map_id: Identifier
    source_asset_id: Identifier
    duration_us: Microseconds
    regions: tuple[SemanticRegion, ...]
    provider_native_artifact_ids: tuple[Identifier, ...] = ()
    warnings: tuple[str, ...] = ()

    @model_validator(mode="after")
    def regions_fit_timeline(self) -> Self:
        if self.duration_us <= 0:
            raise ValueError("duration_us must be positive")
        for region in self.regions:
            if region.end_us > self.duration_us:
                raise ValueError(f"region {region.region_id} exceeds the semantic-map duration")
        return self


class ProcessingRegion(ContractModel):
    processing_region_id: Identifier
    start_us: Microseconds
    end_us: Microseconds
    action: Literal["bypass", "protect", "deterministic_filter", "level", "final_master"]
    processor_id: Identifier
    confidence: Probability
    reason: str = Field(min_length=1, max_length=512)
    parameters: dict[str, JsonScalar] = Field(default_factory=dict)
    transition_us: Microseconds = 0
    source: Literal["recipe", "automatic", "user_override"] = "automatic"

    @model_validator(mode="after")
    def half_open_interval(self) -> Self:
        if self.end_us <= self.start_us:
            raise ValueError("processing regions use non-empty half-open [start_us, end_us) intervals")
        if self.transition_us * 2 > self.end_us - self.start_us:
            raise ValueError("transition_us cannot consume more than the processing region")
        return self


class ProcessingPlan(ContractModel):
    processing_plan_id: Identifier
    run_id: Identifier
    recipe_version_id: Identifier
    semantic_map_id: Identifier
    duration_us: Microseconds
    regions: tuple[ProcessingRegion, ...]
    global_steps: tuple[Identifier, ...]
    no_op_is_valid: Literal[True] = True

    @model_validator(mode="after")
    def regions_fit_timeline(self) -> Self:
        if self.duration_us <= 0:
            raise ValueError("duration_us must be positive")
        for region in self.regions:
            if region.end_us > self.duration_us:
                raise ValueError(f"region {region.processing_region_id} exceeds the plan duration")
        return self


class GainPoint(ContractModel):
    at_us: Microseconds
    gain_db: float = Field(ge=-60.0, le=24.0)


class GainEnvelope(ContractModel):
    gain_envelope_id: Identifier
    run_id: Identifier
    duration_us: Microseconds
    interpolation: Literal["linear"] = "linear"
    points: tuple[GainPoint, ...]
    purpose: Literal["unity_baseline", "adaptive_leveler"]

    @model_validator(mode="after")
    def ordered_points(self) -> Self:
        if self.duration_us <= 0:
            raise ValueError("duration_us must be positive")
        if len(self.points) < 2:
            raise ValueError("gain envelopes require at least two points")
        positions = [point.at_us for point in self.points]
        if positions != sorted(set(positions)):
            raise ValueError("gain-envelope points must have unique ascending time positions")
        if positions[0] != 0 or positions[-1] != self.duration_us:
            raise ValueError("gain-envelope points must span [0, duration_us]")
        return self


class LoudnessMeasurement(ContractModel):
    integrated_lufs: float
    true_peak_dbtp: float
    loudness_range_lu: float = Field(ge=0.0)
    threshold_lufs: float
    measurement_backend: str = Field(min_length=1, max_length=128)
    backend_version: str = Field(min_length=1, max_length=256)


class WaveformLevel(ContractModel):
    samples_per_window: int = Field(gt=0)
    windows: tuple[tuple[tuple[float, float], ...], ...]

    @model_validator(mode="after")
    def valid_min_max(self) -> Self:
        for window in self.windows:
            if not window:
                raise ValueError("waveform windows must contain at least one channel")
            for minimum, maximum in window:
                if not (-1.1 <= minimum <= maximum <= 1.1):
                    raise ValueError("waveform min/max values must be ordered normalized PCM values")
        return self


class WaveformPeaks(ContractModel):
    waveform_id: Identifier
    source_asset_id: Identifier
    sample_rate_hz: int = Field(gt=0)
    channels: int = Field(gt=0)
    duration_us: Microseconds
    levels: tuple[WaveformLevel, ...]


class AnalysisManifest(ContractModel):
    analysis_manifest_id: Identifier
    run_id: Identifier
    source_asset_id: Identifier
    media_probe_id: Identifier
    waveform_id: Identifier
    loudness_before: LoudnessMeasurement
    warnings: tuple[str, ...] = ()


class OutputArtifact(ContractModel):
    artifact_id: Identifier
    kind: AssetKind
    relative_path: str = Field(min_length=1, max_length=512)
    sha256: Sha256
    size_bytes: int = Field(gt=0)
    mime_type: str = Field(min_length=1, max_length=128)
    duration_us: Microseconds
    validation_status: Literal["valid", "warning", "invalid"]
    validation_notes: tuple[str, ...] = ()

    @model_validator(mode="after")
    def portable_relative_path(self) -> Self:
        path = PurePosixPath(self.relative_path)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("output artifact paths must be portable relative paths")
        return self


class OutputManifest(ContractModel):
    output_manifest_id: Identifier
    run_id: Identifier
    source_asset_id: Identifier
    recipe_version_id: Identifier
    artifacts: tuple[OutputArtifact, ...]
    loudness_after: LoudnessMeasurement
    target_integrated_lufs: float
    max_true_peak_dbtp: float
    validation_status: Literal["valid", "warning", "invalid"]
    warnings: tuple[str, ...] = ()


class ProcessingReport(ContractModel):
    processing_report_id: Identifier
    production_id: Identifier
    run_id: Identifier
    source_asset_id: Identifier
    recipe_version_id: Identifier
    engine_build_id: Identifier
    status: RunStatus
    loudness_before: LoudnessMeasurement
    loudness_after: LoudnessMeasurement
    step_ids: tuple[Identifier, ...]
    decisions: tuple[str, ...]
    artifact_sha256: dict[str, Sha256]
    warnings: tuple[str, ...] = ()
    external_api_cost_usd: float = Field(default=0.0, ge=0.0)
    privacy_summary: str = Field(min_length=1, max_length=512)
    reproducibility_summary: str = Field(min_length=1, max_length=512)


class ModelManifest(ContractModel):
    model_manifest_id: Identifier
    model_name: str = Field(min_length=1, max_length=256)
    model_version: str = Field(min_length=1, max_length=128)
    source_url: str = Field(min_length=1, max_length=1024)
    artifact_sha256: Sha256
    code_license: str = Field(min_length=1, max_length=128)
    checkpoint_license: str = Field(min_length=1, max_length=128)
    training_data_terms: str = Field(min_length=1, max_length=1024)
    admission_state: ManifestAdmissionState
    approved_runtime_profiles: tuple[str, ...] = ()
    commercial_hosted_use_reviewed: bool = False
    no_runtime_download: Literal[True] = True
    known_limitations: tuple[str, ...] = ()
    approval_reference: str | None = Field(default=None, max_length=256)


class DependencyManifest(ContractModel):
    dependency_manifest_id: Identifier
    dependency_name: str = Field(min_length=1, max_length=256)
    dependency_version: str = Field(min_length=1, max_length=128)
    source_url: str = Field(min_length=1, max_length=1024)
    artifact_sha256: Sha256 | None = None
    code_license: str = Field(min_length=1, max_length=128)
    admission_state: ManifestAdmissionState
    scope: Literal["runtime", "development", "system"]
    transitive_native_review: str = Field(min_length=1, max_length=1024)
    commercial_hosted_use_reviewed: bool = False
    approval_reference: str | None = Field(default=None, max_length=256)
