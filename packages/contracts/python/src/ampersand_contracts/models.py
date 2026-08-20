from __future__ import annotations

import math
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

SCHEMA_VERSION: Literal["1.0.0"] = "1.0.0"
SEMANTIC_SCHEMA_VERSION: Literal["1.1.0"] = "1.1.0"

Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
Identifier = Annotated[str, StringConstraints(pattern=r"^[a-z0-9][a-z0-9._:-]{1,127}$")]
Microseconds = Annotated[int, Field(ge=0)]
Probability = Annotated[float, Field(ge=0.0, le=1.0)]
JsonScalar = str | int | float | bool | None


class ContractModel(BaseModel):
    """Strict, immutable base for Ampersand-owned serialized contracts."""

    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION


class SemanticContractModel(BaseModel):
    """Versioned base for the richer Semantic Audio Map introduced by issue #22."""

    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)
    schema_version: Literal["1.1.0"] = SEMANTIC_SCHEMA_VERSION


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


class ObservationKind(StrEnum):
    SPEECH_PROBABILITY = "speech_probability"
    SILENCE_PROBABILITY = "silence_probability"
    MUSIC_PROBABILITY = "music_probability"
    AMBIENCE_PROBABILITY = "ambience_probability"
    NOISE_PROBABILITY = "noise_probability"
    OVERLAP_PROBABILITY = "overlap_probability"
    ACTIVE_SPEAKER = "active_speaker"
    TRANSCRIPT_WORD = "transcript_word"
    TRANSCRIPT_SEGMENT = "transcript_segment"
    MOMENTARY_LOUDNESS = "momentary_loudness"
    SHORT_TERM_LOUDNESS = "short_term_loudness"
    SAMPLE_PEAK = "sample_peak"
    TRUE_PEAK = "true_peak"
    CLIPPING_PROBABILITY = "clipping_probability"
    RUMBLE_PROBABILITY = "rumble_probability"
    HUM_PROBABILITY = "hum_probability"
    REVERB_PROBABILITY = "reverb_probability"
    BANDWIDTH_LIMIT_PROBABILITY = "bandwidth_limit_probability"
    ACOUSTIC_EVENT = "acoustic_event"


class ObservationUnit(StrEnum):
    PROBABILITY = "probability"
    LUFS = "LUFS"
    DBTP = "dBTP"
    DBFS = "dBFS"
    LABEL = "label"
    TEXT = "text"


class ProcessingEligibility(StrEnum):
    ELIGIBLE = "eligible"
    PROTECT = "protect"
    NO_OP = "no_op"


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


class ProviderNativeArtifactManifest(ContractModel):
    """Audit pointer for provider-native output kept outside the Ampersand schema."""

    artifact_id: Identifier
    provider_id: Identifier
    provider_version: str = Field(min_length=1, max_length=256)
    adapter_id: Identifier
    adapter_version: str = Field(min_length=1, max_length=128)
    relative_path: str = Field(min_length=1, max_length=512)
    sha256: Sha256
    size_bytes: int = Field(gt=0)
    mime_type: str = Field(min_length=1, max_length=128)
    redaction_summary: str = Field(min_length=1, max_length=512)
    contains_transcript_text: bool = False

    @model_validator(mode="after")
    def portable_relative_path(self) -> Self:
        path = PurePosixPath(self.relative_path)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("provider artifact paths must be portable relative paths")
        return self


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


class EvidenceProvenance(SemanticContractModel):
    provenance_id: Identifier
    provider_id: Identifier
    provider_version: str = Field(min_length=1, max_length=256)
    adapter_id: Identifier
    adapter_version: str = Field(min_length=1, max_length=128)
    native_artifact_id: Identifier | None = None
    model_manifest_id: Identifier | None = None
    deterministic: bool


class SemanticObservation(SemanticContractModel):
    observation_id: Identifier
    kind: ObservationKind
    start_us: Microseconds
    end_us: Microseconds
    confidence: Probability
    value: JsonScalar
    unit: ObservationUnit
    provenance_ref: Identifier
    attributes: dict[str, JsonScalar] = Field(default_factory=dict)

    @model_validator(mode="after")
    def valid_observation(self) -> Self:
        if self.end_us <= self.start_us:
            raise ValueError("semantic observations use non-empty half-open [start_us, end_us) intervals")

        probability_kinds = {
            ObservationKind.SPEECH_PROBABILITY,
            ObservationKind.SILENCE_PROBABILITY,
            ObservationKind.MUSIC_PROBABILITY,
            ObservationKind.AMBIENCE_PROBABILITY,
            ObservationKind.NOISE_PROBABILITY,
            ObservationKind.OVERLAP_PROBABILITY,
            ObservationKind.CLIPPING_PROBABILITY,
            ObservationKind.RUMBLE_PROBABILITY,
            ObservationKind.HUM_PROBABILITY,
            ObservationKind.REVERB_PROBABILITY,
            ObservationKind.BANDWIDTH_LIMIT_PROBABILITY,
        }
        if self.kind in probability_kinds:
            if self.unit is not ObservationUnit.PROBABILITY:
                raise ValueError("probability observations must use the probability unit")
            if isinstance(self.value, bool) or not isinstance(self.value, (int, float)):
                raise ValueError("probability observations require a numeric value")
            if not 0.0 <= float(self.value) <= 1.0:
                raise ValueError("probability observation values must be within [0, 1]")

        measurement_units = {ObservationUnit.LUFS, ObservationUnit.DBTP, ObservationUnit.DBFS}
        if self.unit in measurement_units:
            if isinstance(self.value, bool) or not isinstance(self.value, (int, float)):
                raise ValueError("audio measurements require a numeric value")
            if not math.isfinite(float(self.value)):
                raise ValueError("audio measurements must be finite")

        expected_units = {
            ObservationKind.MOMENTARY_LOUDNESS: ObservationUnit.LUFS,
            ObservationKind.SHORT_TERM_LOUDNESS: ObservationUnit.LUFS,
            ObservationKind.SAMPLE_PEAK: ObservationUnit.DBFS,
            ObservationKind.TRUE_PEAK: ObservationUnit.DBTP,
            ObservationKind.ACTIVE_SPEAKER: ObservationUnit.LABEL,
            ObservationKind.ACOUSTIC_EVENT: ObservationUnit.LABEL,
            ObservationKind.TRANSCRIPT_WORD: ObservationUnit.TEXT,
            ObservationKind.TRANSCRIPT_SEGMENT: ObservationUnit.TEXT,
        }
        expected_unit = expected_units.get(self.kind)
        if expected_unit is not None and self.unit is not expected_unit:
            raise ValueError(f"{self.kind.value} observations must use the {expected_unit.value} unit")
        if self.unit in {ObservationUnit.LABEL, ObservationUnit.TEXT} and (
            not isinstance(self.value, str) or not self.value
        ):
            raise ValueError("label and text observations require a non-empty string value")
        return self


class SemanticConflict(SemanticContractModel):
    conflict_id: Identifier
    start_us: Microseconds
    end_us: Microseconds
    kinds: tuple[ObservationKind, ...]
    observation_ids: tuple[Identifier, ...]
    severity: Probability
    reason: str = Field(min_length=1, max_length=512)

    @model_validator(mode="after")
    def valid_conflict(self) -> Self:
        if self.end_us <= self.start_us:
            raise ValueError("semantic conflicts use non-empty half-open [start_us, end_us) intervals")
        if len(set(self.observation_ids)) < 2:
            raise ValueError("semantic conflicts require at least two distinct observations")
        if not self.kinds:
            raise ValueError("semantic conflicts require at least one observation kind")
        return self


class SemanticRegion(SemanticContractModel):
    region_id: Identifier
    start_us: Microseconds
    end_us: Microseconds
    content_label: Literal["unknown", "speech", "silence", "music", "ambience", "noise", "mixed"]
    confidence: Probability
    speech_probability: Probability | None = None
    music_probability: Probability | None = None
    silence_probability: Probability | None = None
    ambience_probability: Probability | None = None
    noise_probability: Probability | None = None
    overlap_probability: Probability | None = None
    active_speaker: str | None = Field(default=None, min_length=1, max_length=128)
    active_speaker_confidence: Probability | None = None
    protected: bool = True
    processing_eligibility: ProcessingEligibility = ProcessingEligibility.PROTECT
    observations: dict[str, JsonScalar] = Field(default_factory=dict)
    observation_ids: tuple[Identifier, ...] = ()
    conflict_ids: tuple[Identifier, ...] = ()
    provider_refs: tuple[Identifier, ...] = ()

    @model_validator(mode="after")
    def half_open_interval(self) -> Self:
        if self.end_us <= self.start_us:
            raise ValueError("semantic regions use non-empty half-open [start_us, end_us) intervals")
        if self.protected is (self.processing_eligibility is ProcessingEligibility.ELIGIBLE):
            raise ValueError("eligible semantic regions must be unprotected; protect/no-op regions must be protected")
        if (self.active_speaker is None) is not (self.active_speaker_confidence is None):
            raise ValueError("active speaker label and confidence must be present or absent together")
        return self


class SemanticMap(SemanticContractModel):
    semantic_map_id: Identifier
    semantic_map_version: Literal["0.1.0"] = "0.1.0"
    source_asset_id: Identifier
    duration_us: Microseconds
    analysis_hop_us: Microseconds
    regions: tuple[SemanticRegion, ...]
    provenance_sources: tuple[EvidenceProvenance, ...] = ()
    observations: tuple[SemanticObservation, ...] = ()
    conflicts: tuple[SemanticConflict, ...] = ()
    provider_native_artifact_ids: tuple[Identifier, ...] = ()
    unavailable_adapters: tuple[Identifier, ...] = ()
    coverage: Literal["full"] = "full"
    warnings: tuple[str, ...] = ()

    @model_validator(mode="after")
    def regions_fit_timeline(self) -> Self:
        if self.duration_us <= 0:
            raise ValueError("duration_us must be positive")
        if self.analysis_hop_us <= 0:
            raise ValueError("analysis_hop_us must be positive")
        if not self.regions:
            raise ValueError("semantic maps require at least one full-coverage region")

        expected_start = 0
        region_ids: set[str] = set()
        observation_ids = {observation.observation_id for observation in self.observations}
        conflict_ids = {conflict.conflict_id for conflict in self.conflicts}
        provenance_ids = {provenance.provenance_id for provenance in self.provenance_sources}
        provider_native_ids = set(self.provider_native_artifact_ids)
        if len(observation_ids) != len(self.observations):
            raise ValueError("semantic observation IDs must be unique")
        if len(conflict_ids) != len(self.conflicts):
            raise ValueError("semantic conflict IDs must be unique")
        if len(provenance_ids) != len(self.provenance_sources):
            raise ValueError("semantic provenance IDs must be unique")
        for provenance in self.provenance_sources:
            if provenance.native_artifact_id is not None and provenance.native_artifact_id not in provider_native_ids:
                raise ValueError(f"provenance {provenance.provenance_id} references an unknown native artifact")

        observation_order = [
            (observation.start_us, observation.end_us, observation.kind.value, observation.observation_id)
            for observation in self.observations
        ]
        if observation_order != sorted(observation_order):
            raise ValueError("semantic observations must use stable timeline ordering")

        for observation in self.observations:
            if observation.end_us > self.duration_us:
                raise ValueError(f"observation {observation.observation_id} exceeds the semantic-map duration")
            if observation.provenance_ref not in provenance_ids:
                raise ValueError(f"observation {observation.observation_id} references unknown provenance")
        for conflict in self.conflicts:
            if conflict.end_us > self.duration_us:
                raise ValueError(f"conflict {conflict.conflict_id} exceeds the semantic-map duration")
            if not set(conflict.observation_ids) <= observation_ids:
                raise ValueError(f"conflict {conflict.conflict_id} references an unknown observation")

        for region in self.regions:
            if region.region_id in region_ids:
                raise ValueError("semantic region IDs must be unique")
            region_ids.add(region.region_id)
            if region.end_us > self.duration_us:
                raise ValueError(f"region {region.region_id} exceeds the semantic-map duration")
            if region.start_us != expected_start:
                raise ValueError("semantic regions must be ordered, contiguous, and cover from zero")
            if not set(region.observation_ids) <= observation_ids:
                raise ValueError(f"region {region.region_id} references an unknown observation")
            if not set(region.conflict_ids) <= conflict_ids:
                raise ValueError(f"region {region.region_id} references an unknown conflict")
            if region.conflict_ids and region.processing_eligibility is not ProcessingEligibility.PROTECT:
                raise ValueError(f"conflicted region {region.region_id} must remain protected")
            expected_start = region.end_us
        if expected_start != self.duration_us:
            raise ValueError("semantic regions must cover the full source duration")
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
