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


class FixturePartition(StrEnum):
    DEVELOPMENT = "development"
    VALIDATION = "validation"
    HIDDEN_TEST = "hidden_test"


class FixtureSourceKind(StrEnum):
    SYNTHETIC_CONTROL = "synthetic_control"
    RIGHTS_CLEARED_REAL_WORLD = "rights_cleared_real_world"
    ENGINEER_REFERENCE = "engineer_reference"


class FixtureRightsStatus(StrEnum):
    MATHEMATICAL_GENERATION = "mathematical_generation"
    DOCUMENTED_COMMERCIAL_RESEARCH = "documented_commercial_research"
    RESTRICTED_INTERNAL_RESEARCH = "restricted_internal_research"


class FixtureConsentStatus(StrEnum):
    NOT_APPLICABLE_SYNTHETIC = "not_applicable_synthetic"
    DOCUMENTED = "documented"
    RESTRICTED = "restricted"


class FixtureRelationship(StrEnum):
    CLEAN_CONTROL = "clean_control"
    DEGRADED_FROM_CLEAN = "degraded_from_clean"
    STANDALONE_CONTROL = "standalone_control"
    REAL_WORLD_SOURCE = "real_world_source"
    ENGINEER_DERIVATIVE = "engineer_derivative"


class FixtureRegion(ContractModel):
    fixture_region_id: Identifier
    start_us: Microseconds
    end_us: Microseconds
    expected_role: Literal["speech", "silence", "noise", "music", "transient", "mixed", "unknown"]
    speaker_label: str | None = Field(default=None, min_length=1, max_length=128)
    protected: bool = False
    target_relative_level_db: float | None = Field(default=None, ge=-60.0, le=24.0)
    notes: str = Field(min_length=1, max_length=512)

    @model_validator(mode="after")
    def nonempty_region(self) -> Self:
        if self.end_us <= self.start_us:
            raise ValueError("fixture regions use non-empty half-open [start_us, end_us) intervals")
        return self


class FixtureTransform(ContractModel):
    transform_id: Identifier
    family: Identifier
    implementation_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    seed: int | None = Field(default=None, ge=0, le=2**63 - 1)
    parameters: dict[str, JsonScalar] = Field(default_factory=dict)


class FixtureAssetManifest(ContractModel):
    fixture_id: Identifier
    corpus_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    partition: FixturePartition
    visibility: Literal["development_visible", "validation_visible", "promotion_withheld"]
    filename: str = Field(min_length=1, max_length=255)
    sha256: Sha256
    size_bytes: int = Field(gt=0)
    mime_type: Literal["audio/wav"] = "audio/wav"
    duration_us: Microseconds
    sample_rate_hz: int = Field(ge=8_000, le=192_000)
    channels: int = Field(ge=1, le=8)
    sample_width_bits: Literal[16, 24, 32]
    source_kind: FixtureSourceKind
    rights_status: FixtureRightsStatus
    consent_status: FixtureConsentStatus
    contains_personal_data: bool
    contains_customer_media: bool
    contains_copyrighted_music: bool
    session_group_id: Identifier
    speaker_group_ids: tuple[Identifier, ...] = ()
    relationship: FixtureRelationship
    parent_fixture_id: Identifier | None = None
    parent_sha256: Sha256 | None = None
    transforms: tuple[FixtureTransform, ...] = ()
    regions: tuple[FixtureRegion, ...]
    generator_id: Identifier
    generator_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    generation_command: tuple[str, ...]
    permitted_environments: tuple[Identifier, ...]
    permitted_processor_classes: tuple[Identifier, ...]
    retention_class: Identifier
    deletion_policy: str = Field(min_length=1, max_length=512)

    @model_validator(mode="after")
    def valid_fixture_lineage_and_timeline(self) -> Self:
        path = PurePosixPath(self.filename)
        if path.is_absolute() or ".." in path.parts or len(path.parts) != 1:
            raise ValueError("fixture filename must be a portable basename")
        if self.duration_us <= 0:
            raise ValueError("fixture duration must be positive")
        if not self.generation_command:
            raise ValueError("generation_command cannot be empty")
        if not self.permitted_environments or not self.permitted_processor_classes:
            raise ValueError("fixture permissions cannot be empty")
        if self.partition is FixturePartition.HIDDEN_TEST and self.visibility != "promotion_withheld":
            raise ValueError("hidden-test fixtures must be promotion_withheld")
        if self.partition is not FixturePartition.HIDDEN_TEST and self.visibility == "promotion_withheld":
            raise ValueError("only hidden-test fixtures may be promotion_withheld")
        if self.source_kind is FixtureSourceKind.SYNTHETIC_CONTROL and (
            self.rights_status is not FixtureRightsStatus.MATHEMATICAL_GENERATION
            or self.consent_status is not FixtureConsentStatus.NOT_APPLICABLE_SYNTHETIC
            or self.contains_personal_data
            or self.contains_customer_media
            or self.contains_copyrighted_music
        ):
            raise ValueError(
                "synthetic controls must be mathematical, non-customer, and free of personal/copyrighted media"
            )
        requires_parent = self.relationship in {
            FixtureRelationship.DEGRADED_FROM_CLEAN,
            FixtureRelationship.ENGINEER_DERIVATIVE,
        }
        if requires_parent != (self.parent_fixture_id is not None and self.parent_sha256 is not None):
            raise ValueError("derived fixtures require both parent_fixture_id and parent_sha256")
        if self.relationship is FixtureRelationship.DEGRADED_FROM_CLEAN and not self.transforms:
            raise ValueError("degraded fixtures require at least one transform")
        previous_end = 0
        for region in self.regions:
            if region.end_us > self.duration_us:
                raise ValueError(f"fixture region {region.fixture_region_id} exceeds the asset duration")
            if region.start_us < previous_end:
                raise ValueError("fixture regions must be ordered and non-overlapping")
            previous_end = region.end_us
        return self


class FixtureCorpusManifest(ContractModel):
    corpus_id: Identifier
    corpus_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    generator_id: Identifier
    generator_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    fixtures: tuple[FixtureAssetManifest, ...]
    partitions_present: tuple[FixturePartition, ...]
    local_package_contains_customer_media: Literal[False] = False
    external_api_cost_usd: Literal[0] = 0
    prohibited_sources: tuple[
        Literal["hosted_processor_service", "hosted_processor_output", "production_customer_media"], ...
    ]
    governance_summary: str = Field(min_length=1, max_length=1024)

    @model_validator(mode="after")
    def valid_corpus(self) -> Self:
        if not self.fixtures:
            raise ValueError("fixture corpus cannot be empty")
        ids = [fixture.fixture_id for fixture in self.fixtures]
        filenames = [fixture.filename for fixture in self.fixtures]
        if len(ids) != len(set(ids)) or len(filenames) != len(set(filenames)):
            raise ValueError("fixture IDs and filenames must be unique")
        if any(fixture.corpus_version != self.corpus_version for fixture in self.fixtures):
            raise ValueError("every fixture must use the corpus version")
        expected_partitions = tuple(sorted({fixture.partition for fixture in self.fixtures}, key=str))
        if self.partitions_present != expected_partitions:
            raise ValueError("partitions_present must exactly match the fixture partitions")
        by_id = {fixture.fixture_id: fixture for fixture in self.fixtures}
        for fixture in self.fixtures:
            if fixture.parent_fixture_id is None:
                continue
            parent = by_id.get(fixture.parent_fixture_id)
            if parent is None:
                raise ValueError(f"fixture {fixture.fixture_id} references a parent outside this corpus")
            if parent.partition is not fixture.partition:
                raise ValueError("synthetic variants and their parent must remain in the same partition")
            if parent.sha256 != fixture.parent_sha256:
                raise ValueError("fixture parent_sha256 must match the parent asset")
        return self


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


class AdaptiveLevelerSettings(ContractModel):
    settings_id: Identifier
    algorithm_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    activation_mode: Literal["shadow", "active"] = "shadow"
    comfort_band_lu: float = Field(default=4.0, gt=0.0, le=12.0)
    target_speech_min_lufs: float = Field(default=-30.0, ge=-45.0, le=-12.0)
    target_speech_max_lufs: float = Field(default=-18.0, ge=-45.0, le=-12.0)
    max_boost_db: float = Field(default=6.0, ge=0.0, le=12.0)
    max_cut_db: float = Field(default=9.0, ge=0.0, le=18.0)
    max_speaker_offset_db: float = Field(default=6.0, ge=0.0, le=12.0)
    max_gain_slope_db_per_second: float = Field(default=3.0, gt=0.0, le=24.0)
    max_gain_acceleration_db_per_second2: float = Field(default=12.0, gt=0.0, le=96.0)
    smoothing_time_ms: int = Field(default=500, ge=50, le=5_000)
    boundary_taper_ms: int = Field(default=300, ge=0, le=5_000)
    short_term_loudness_weight: float = Field(default=0.35, ge=0.0, le=0.75)
    min_speech_probability: Probability = 0.62
    max_silence_probability: Probability = 0.40
    min_region_confidence: Probability = 0.60
    max_overlap_probability: Probability = 0.35
    max_clipping_probability: Probability = 0.20
    pre_master_peak_ceiling_dbfs: float = Field(default=-2.0, ge=-18.0, le=0.0)
    significant_correction_db: float = Field(default=2.0, gt=0.0, le=12.0)
    minimum_speaker_duration_us: Microseconds = 1_000_000

    @model_validator(mode="after")
    def ordered_target_range(self) -> Self:
        if self.target_speech_min_lufs > self.target_speech_max_lufs:
            raise ValueError("target_speech_min_lufs cannot exceed target_speech_max_lufs")
        return self


class SpeakerLevelStatistics(ContractModel):
    speaker_label: str = Field(min_length=1, max_length=128)
    observation_count: int = Field(gt=0)
    eligible_duration_us: Microseconds
    robust_speech_level_lufs: float
    relative_offset_db: float
    used_global_fallback: bool


class SignificantGainCorrection(ContractModel):
    correction_id: Identifier
    start_us: Microseconds
    end_us: Microseconds
    peak_gain_db: float = Field(ge=-60.0, le=24.0)
    reason: str = Field(min_length=1, max_length=512)

    @model_validator(mode="after")
    def half_open_interval(self) -> Self:
        if self.end_us <= self.start_us:
            raise ValueError("gain corrections use non-empty half-open [start_us, end_us) intervals")
        return self


class LevelerStatistics(ContractModel):
    leveler_statistics_id: Identifier
    run_id: Identifier
    semantic_map_id: Identifier
    settings_id: Identifier
    settings_sha256: Sha256
    algorithm_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    activation_mode: Literal["shadow", "active"]
    target_speech_level_lufs: float | None
    comfort_band_low_lufs: float | None
    comfort_band_high_lufs: float | None
    total_duration_us: Microseconds
    eligible_duration_us: Microseconds
    changed_duration_us: Microseconds
    eligible_region_count: int = Field(ge=0)
    protected_region_count: int = Field(ge=0)
    changed_region_count: int = Field(ge=0)
    gain_min_db: float = Field(ge=-60.0, le=24.0)
    gain_mean_db: float = Field(ge=-60.0, le=24.0)
    gain_max_db: float = Field(ge=-60.0, le=24.0)
    maximum_gain_slope_db_per_second: float = Field(ge=0.0)
    maximum_gain_acceleration_db_per_second2: float = Field(ge=0.0)
    peak_limited_region_count: int = Field(ge=0)
    speaker_statistics: tuple[SpeakerLevelStatistics, ...] = ()
    significant_corrections: tuple[SignificantGainCorrection, ...] = ()
    reasoning: tuple[str, ...]
    warnings: tuple[str, ...] = ()

    @model_validator(mode="after")
    def valid_statistics(self) -> Self:
        if self.total_duration_us <= 0:
            raise ValueError("total_duration_us must be positive")
        if self.eligible_duration_us > self.total_duration_us:
            raise ValueError("eligible duration cannot exceed total duration")
        if self.changed_duration_us > self.eligible_duration_us:
            raise ValueError("changed duration cannot exceed eligible duration")
        if not self.gain_min_db <= self.gain_mean_db <= self.gain_max_db:
            raise ValueError("gain statistics must satisfy min <= mean <= max")
        comfort_values = (
            self.target_speech_level_lufs,
            self.comfort_band_low_lufs,
            self.comfort_band_high_lufs,
        )
        if any(value is None for value in comfort_values) and not all(value is None for value in comfort_values):
            raise ValueError("target and comfort-band values must be present or absent together")
        if (
            self.target_speech_level_lufs is not None
            and self.comfort_band_low_lufs is not None
            and self.comfort_band_high_lufs is not None
            and not self.comfort_band_low_lufs <= self.target_speech_level_lufs <= self.comfort_band_high_lufs
        ):
            raise ValueError("target speech level must sit inside the comfort band")
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
    gain_envelope_id: Identifier | None = None
    leveler_statistics_id: Identifier | None = None
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
