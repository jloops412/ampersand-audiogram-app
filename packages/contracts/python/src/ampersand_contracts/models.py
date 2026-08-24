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
ProcessingAction = Literal["bypass", "protect", "deterministic_filter", "denoise", "level", "final_master"]
ProcessingSource = Literal["recipe", "automatic", "user_override"]


class ContractModel(BaseModel):
    """Strict, immutable base for Ampersand-owned serialized contracts."""

    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True, allow_inf_nan=False)
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION


class SemanticContractModel(BaseModel):
    """Versioned base for the richer Semantic Audio Map introduced by issue #22."""

    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True, allow_inf_nan=False)
    schema_version: Literal["1.1.0"] = SEMANTIC_SCHEMA_VERSION


class AssetKind(StrEnum):
    SOURCE = "source"
    BACKGROUND_ARTWORK = "background_artwork"
    CANONICAL_AUDIO = "canonical_audio"
    WAVEFORM = "waveform"
    MASTER_WAV = "master_wav"
    MASTER_MP3 = "master_mp3"
    AUDIOGRAM_MP4 = "audiogram_mp4"
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
    resolved_settings_id: Identifier
    resolved_settings_sha256: Sha256
    engine_build_id: Identifier
    idempotency_key: Sha256
    status: RunStatus
    step_ids: tuple[Identifier, ...]
    cleanup_plan_id: Identifier | None = None
    cleanup_plan_sha256: Sha256 | None = None

    @model_validator(mode="after")
    def cleanup_identity_is_complete(self) -> Self:
        if (self.cleanup_plan_id is None) is not (self.cleanup_plan_sha256 is None):
            raise ValueError("cleanup plan ID and SHA-256 must be present or absent together")
        return self


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


class MasteringSettings(ContractModel):
    """Safe, executable mastering controls exposed by the private beta."""

    target_integrated_lufs: float = Field(ge=-24.0, le=-14.0)
    max_true_peak_dbtp: float = Field(ge=-3.0, le=-1.0)
    target_loudness_range_lu: float = Field(ge=5.0, le=30.0)


class CleanupSettings(ContractModel):
    """Deterministic spoken-word cleanup controls admitted for the V1 beta."""

    mode: Literal["smart", "manual"] = "manual"
    noise_reduction: Literal["off", "light", "balanced", "strong"] = "off"
    rumble_filter: bool = False
    hum_reduction: Literal["off", "50hz", "60hz"] = "off"
    declip: bool = False
    noise_gate: Literal["off", "light", "balanced"] = "off"
    deesser: Literal["off", "light", "balanced", "strong"] = "off"
    voice_enhancement: Literal["off", "natural", "warm", "presence"] = "off"
    compression: Literal["off", "gentle", "balanced", "firm"] = "off"


class CleanupPlannerSettings(ContractModel):
    """Versioned, protect-only admission policy for Smart Cleanup V0.3."""

    settings_id: Identifier = "cleanup-planner-settings:smart-v0.3"
    algorithm_version: Literal["0.3.0"] = "0.3.0"
    activation_mode: Literal["protect"] = "protect"
    maximum_music_probability: Probability = 0.35
    minimum_noise_probability_for_candidate: Probability = 0.65
    minimum_rumble_probability_for_candidate: Probability = 0.75
    minimum_hum_probability_for_candidate: Probability = 0.80
    require_full_coverage_music_evidence: Literal[True] = True
    automatic_declip_enabled: Literal[False] = False


class CleanupEvidenceSummary(ContractModel):
    """Bounded measurements used to explain one Smart Cleanup resolution."""

    semantic_map_sha256: Sha256
    duration_us: Microseconds
    region_count: int = Field(gt=0)
    protected_region_count: int = Field(ge=0)
    conflict_count: int = Field(ge=0)
    music_evidence_available: bool
    stationary_noise_evidence_available: bool
    maximum_music_probability: Probability | None = None
    maximum_noise_probability: Probability | None = None
    maximum_rumble_probability: Probability | None = None
    maximum_hum_probability: Probability | None = None
    maximum_clipping_probability: Probability | None = None
    resolved_hum_fundamental_hz: Literal[50, 60] | None = None


class CleanupStageDecision(ContractModel):
    """One explicit stage disposition in a resolved cleanup plan."""

    stage: Literal[
        "declip",
        "rumble_filter",
        "hum_reduction",
        "noise_reduction",
        "noise_gate",
        "deesser",
        "voice_enhancement",
        "compression",
    ]
    disposition: Literal["candidate", "applied", "skipped", "protected"]
    measured_probability: Probability | None = None
    candidate_threshold: Probability | None = None
    reason_code: Identifier
    reason: str = Field(min_length=1, max_length=512)


class CleanupPlan(ContractModel):
    """Resolved, auditable cleanup decision used by the production renderer."""

    cleanup_plan_id: Identifier
    run_id: Identifier
    semantic_map_id: Identifier
    algorithm_version: Literal["0.3.0"] = "0.3.0"
    mode: Literal["smart", "manual"]
    decision: Literal["candidate", "manual", "protect", "no_op"]
    planner_settings_id: Identifier
    planner_settings_sha256: Sha256
    planner_settings: CleanupPlannerSettings
    evidence: CleanupEvidenceSummary
    requested_settings: CleanupSettings
    requested_settings_sha256: Sha256
    resolved_settings: CleanupSettings
    resolved_settings_sha256: Sha256
    applied_stages: tuple[
        Literal[
            "declip",
            "rumble_filter",
            "hum_reduction",
            "noise_reduction",
            "noise_gate",
            "deesser",
            "voice_enhancement",
            "compression",
        ],
        ...,
    ] = ()
    candidate_stages: tuple[
        Literal["rumble_filter", "hum_reduction", "noise_reduction"],
        ...,
    ] = ()
    stage_decisions: tuple[CleanupStageDecision, ...] = Field(min_length=8, max_length=8)
    reason_codes: tuple[Identifier, ...] = Field(min_length=1)
    reasons: tuple[str, ...] = Field(min_length=1)
    warnings: tuple[str, ...] = ()
    production_audio_changed: bool

    @model_validator(mode="after")
    def valid_cleanup_resolution(self) -> Self:
        from .serialization import manifest_sha256

        if self.planner_settings_sha256 != manifest_sha256(self.planner_settings):
            raise ValueError("cleanup planner settings SHA-256 must match the embedded policy snapshot")
        if self.requested_settings_sha256 != manifest_sha256(self.requested_settings):
            raise ValueError("cleanup requested settings SHA-256 must match the embedded request")
        if self.resolved_settings_sha256 != manifest_sha256(self.resolved_settings):
            raise ValueError("cleanup resolved settings SHA-256 must match the embedded resolution")
        expected_stages: list[str] = []
        settings = self.resolved_settings
        if settings.declip:
            expected_stages.append("declip")
        if settings.rumble_filter:
            expected_stages.append("rumble_filter")
        if settings.hum_reduction != "off":
            expected_stages.append("hum_reduction")
        if settings.noise_reduction != "off":
            expected_stages.append("noise_reduction")
        if settings.noise_gate != "off":
            expected_stages.append("noise_gate")
        if settings.deesser != "off":
            expected_stages.append("deesser")
        if settings.voice_enhancement != "off":
            expected_stages.append("voice_enhancement")
        if settings.compression != "off":
            expected_stages.append("compression")
        if tuple(expected_stages) != self.applied_stages:
            raise ValueError("applied_stages must exactly match the resolved cleanup settings")
        if self.production_audio_changed is not bool(self.applied_stages):
            raise ValueError("production_audio_changed must match whether cleanup stages are applied")
        if self.mode != settings.mode:
            raise ValueError("cleanup plan mode must match the resolved settings mode")
        if self.planner_settings_id != self.planner_settings.settings_id:
            raise ValueError("cleanup planner settings ID must match the embedded policy snapshot")
        if self.mode == "manual" and self.decision != "manual":
            raise ValueError("manual cleanup mode requires a manual decision")
        if self.mode == "smart" and self.decision == "manual":
            raise ValueError("Smart Cleanup cannot contain a manual decision")
        if self.mode == "manual" and self.requested_settings != self.resolved_settings:
            raise ValueError("manual cleanup settings must be preserved exactly")
        if self.decision in {"protect", "no_op"} and self.applied_stages:
            raise ValueError("protect and no-op cleanup plans cannot apply processing stages")
        if self.mode == "smart" and self.applied_stages:
            raise ValueError("Smart Cleanup V0.3 is protect-only and cannot change production audio")
        if self.mode == "manual" and self.candidate_stages:
            raise ValueError("manual cleanup plans do not contain automatic candidate stages")
        if self.decision == "candidate" and not self.candidate_stages:
            raise ValueError("candidate cleanup decisions require at least one candidate stage")
        if self.decision != "candidate" and self.candidate_stages:
            raise ValueError("only candidate cleanup decisions may contain candidate stages")
        if len(set(self.candidate_stages)) != len(self.candidate_stages):
            raise ValueError("cleanup candidate stages must be unique")
        decision_stages = tuple(decision.stage for decision in self.stage_decisions)
        required_stages = {
            "declip",
            "rumble_filter",
            "hum_reduction",
            "noise_reduction",
            "noise_gate",
            "deesser",
            "voice_enhancement",
            "compression",
        }
        if set(decision_stages) != required_stages or len(decision_stages) != len(required_stages):
            raise ValueError("stage_decisions must contain each cleanup stage exactly once")
        if (
            tuple(decision.stage for decision in self.stage_decisions if decision.disposition == "applied")
            != self.applied_stages
        ):
            raise ValueError("applied stage decisions must match applied_stages")
        if (
            tuple(decision.stage for decision in self.stage_decisions if decision.disposition == "candidate")
            != self.candidate_stages
        ):
            raise ValueError("candidate stage decisions must match candidate_stages")
        if len(set(self.reason_codes)) != len(self.reason_codes):
            raise ValueError("cleanup reason codes must be unique")
        return self


class OutputMetadataSettings(ContractModel):
    """Portable delivery tags written by FFmpeg without adding a metadata dependency."""

    artist: str = Field(default="", max_length=160)
    album: str = Field(default="", max_length=160)
    genre: str = Field(default="", max_length=80)
    date: str = Field(default="", max_length=40)
    comment: str = Field(default="", max_length=512)
    copyright: str = Field(default="", max_length=256)
    track_number: str = Field(default="", max_length=32)


class AudiogramSettings(ContractModel):
    """Versioned deterministic controls shared by Studio and the server renderer."""

    spec_version: Literal["1.0", "1.1"] = "1.1"
    enabled: bool = False
    aspect_ratio: Literal["square", "feed_portrait", "portrait", "landscape"] = "square"
    waveform_style: Literal[
        "line",
        "mirrored",
        "bars",
        "dots",
        "spectrum",
        "spectrum_dots",
    ] = "mirrored"
    waveform_scale: Literal["linear", "sqrt", "cbrt", "log"] = "sqrt"
    waveform_position: Literal["top", "center", "bottom"] = "center"
    waveform_width_percent: int = Field(default=84, ge=40, le=100)
    waveform_height_percent: int = Field(default=30, ge=10, le=60)
    waveform_opacity: float = Field(default=1.0, ge=0.1, le=1.0)
    waveform_glow: float = Field(default=0.58, ge=0.0, le=1.0)
    waveform_frame: Literal["none", "glass", "outline", "accent"] = "glass"
    background_mode: Literal["color", "gradient", "radial", "artwork", "video"] = "gradient"
    background_fit: Literal["cover", "contain"] = "cover"
    background_dim: float = Field(default=0.08, ge=0.0, le=0.85)
    background_blur: int = Field(default=0, ge=0, le=30)
    background_vignette: float = Field(default=0.45, ge=0.0, le=1.0)
    background_color: str = Field(default="#111718", pattern=r"^#[0-9a-fA-F]{6}$")
    accent_color: str = Field(default="#e1b977", pattern=r"^#[0-9a-fA-F]{6}$")
    waveform_color: str = Field(default="#f3cc8a", pattern=r"^#[0-9a-fA-F]{6}$")
    text_color: str = Field(default="#f8f4ec", pattern=r"^#[0-9a-fA-F]{6}$")
    font_family: Literal["sans", "serif", "mono"] = "sans"
    text_align: Literal["left", "center", "right"] = "center"
    text_position: Literal["top", "center", "bottom"] = "top"
    text_panel: Literal["none", "shadow", "glass", "accent"] = "shadow"
    headline_size_percent: float = Field(default=4.8, ge=2.0, le=10.0)
    subtitle_size_percent: float = Field(default=2.7, ge=1.0, le=6.0)
    headline: str = Field(default="", max_length=160)
    subtitle: str = Field(default="", max_length=160)
    frame_rate: Literal[24, 30, 60] = 30
    render_quality: Literal["draft", "standard", "high"] = "standard"


class ExportSettings(ContractModel):
    """Delivery choices that map directly to admitted encoder paths."""

    wav: bool = True
    mp3: bool = True
    mp3_bitrate_kbps: Literal[128, 160, 192, 256, 320] = 192

    @model_validator(mode="after")
    def at_least_one_output(self) -> Self:
        if not self.wav and not self.mp3:
            raise ValueError("at least one output format must be enabled")
        return self


class ProductionSettings(ContractModel):
    """Complete executable settings for one beta production."""

    cleanup: CleanupSettings = Field(default_factory=CleanupSettings)
    mastering: MasteringSettings
    metadata: OutputMetadataSettings = Field(default_factory=OutputMetadataSettings)
    audiogram: AudiogramSettings = Field(default_factory=AudiogramSettings)
    export: ExportSettings


class ProductionSettingsOverride(ContractModel):
    """Sparse run override accepted by future template resolution surfaces."""

    target_integrated_lufs: float | None = Field(default=None, ge=-24.0, le=-14.0)
    max_true_peak_dbtp: float | None = Field(default=None, ge=-3.0, le=-1.0)
    target_loudness_range_lu: float | None = Field(default=None, ge=5.0, le=30.0)
    wav: bool | None = None
    mp3: bool | None = None
    mp3_bitrate_kbps: Literal[128, 160, 192, 256, 320] | None = None


class StudioTemplate(ContractModel):
    """Mutable catalog identity; edits point to a new immutable version."""

    template_id: Identifier
    workspace_id: Identifier
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=512)
    current_version_id: Identifier
    is_default: bool = False
    archived: bool = False


class StudioTemplateVersion(ContractModel):
    """Immutable template version containing a complete settings value."""

    template_version_id: Identifier
    template_id: Identifier
    version: int = Field(ge=1)
    recipe_version_id: Identifier
    settings: ProductionSettings
    settings_sha256: Sha256
    built_in: bool = False
    change_summary: str = Field(min_length=1, max_length=512)


class ResolvedProductionSettings(ContractModel):
    """Fully expanded, immutable settings snapshot attached to a run."""

    resolved_settings_id: Identifier
    recipe_version_id: Identifier
    intent: Literal["podcast", "natural_voice", "broadcast", "social_voice"]
    template_version_id: Identifier | None = None
    settings: ProductionSettings
    settings_sha256: Sha256
    field_provenance: dict[
        Literal[
            "cleanup.mode",
            "cleanup.noise_reduction",
            "cleanup.rumble_filter",
            "cleanup.hum_reduction",
            "cleanup.declip",
            "cleanup.noise_gate",
            "cleanup.deesser",
            "cleanup.voice_enhancement",
            "cleanup.compression",
            "mastering.target_integrated_lufs",
            "mastering.max_true_peak_dbtp",
            "mastering.target_loudness_range_lu",
            "metadata.artist",
            "metadata.album",
            "metadata.genre",
            "metadata.date",
            "metadata.comment",
            "metadata.copyright",
            "metadata.track_number",
            "audiogram.enabled",
            "audiogram.spec_version",
            "audiogram.aspect_ratio",
            "audiogram.waveform_style",
            "audiogram.waveform_scale",
            "audiogram.waveform_position",
            "audiogram.waveform_width_percent",
            "audiogram.waveform_height_percent",
            "audiogram.waveform_opacity",
            "audiogram.waveform_glow",
            "audiogram.waveform_frame",
            "audiogram.background_mode",
            "audiogram.background_fit",
            "audiogram.background_dim",
            "audiogram.background_blur",
            "audiogram.background_vignette",
            "audiogram.background_color",
            "audiogram.accent_color",
            "audiogram.waveform_color",
            "audiogram.text_color",
            "audiogram.font_family",
            "audiogram.text_align",
            "audiogram.text_position",
            "audiogram.text_panel",
            "audiogram.headline_size_percent",
            "audiogram.subtitle_size_percent",
            "audiogram.headline",
            "audiogram.subtitle",
            "audiogram.frame_rate",
            "audiogram.render_quality",
            "export.wav",
            "export.mp3",
            "export.mp3_bitrate_kbps",
        ],
        Literal["recipe", "template", "run_override"],
    ]
    warnings: tuple[str, ...] = ()


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
    clipping_probability: Probability | None = None
    rumble_probability: Probability | None = None
    hum_probability: Probability | None = None
    reverb_probability: Probability | None = None
    bandwidth_limit_probability: Probability | None = None
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
    action: ProcessingAction
    processor_id: Identifier
    confidence: Probability
    reason_code: Identifier = "router:unspecified"
    reason: str = Field(min_length=1, max_length=512)
    parameters: dict[str, JsonScalar] = Field(default_factory=dict)
    fallback_processor_id: Identifier | None = None
    warning_codes: tuple[Identifier, ...] = ()
    transition_us: Microseconds = 0
    source: ProcessingSource = "automatic"
    planning_only: bool = False

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
        if not self.regions:
            raise ValueError("processing plans require at least one full-coverage region")
        expected_start = 0
        region_ids: set[str] = set()
        for region in self.regions:
            if region.processing_region_id in region_ids:
                raise ValueError("processing-region IDs must be unique")
            region_ids.add(region.processing_region_id)
            if region.end_us > self.duration_us:
                raise ValueError(f"region {region.processing_region_id} exceeds the plan duration")
            if region.start_us != expected_start:
                raise ValueError("processing regions must be ordered, contiguous, and cover from zero")
            expected_start = region.end_us
        if expected_start != self.duration_us:
            raise ValueError("processing regions must cover the full plan duration")
        return self


class ProcessingRouteOverride(ContractModel):
    override_id: Identifier
    start_us: Microseconds
    end_us: Microseconds
    action: Literal["protect", "bypass"]
    reason: str = Field(min_length=1, max_length=512)

    @model_validator(mode="after")
    def half_open_interval(self) -> Self:
        if self.end_us <= self.start_us:
            raise ValueError("processing-route overrides use non-empty half-open [start_us, end_us) intervals")
        return self


class ProcessingRouterSettings(ContractModel):
    settings_id: Identifier
    algorithm_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    planning_mode: Literal["shadow"] = "shadow"
    minimum_region_confidence: Probability = 0.60
    minimum_speech_probability: Probability = 0.62
    maximum_silence_probability: Probability = 0.40
    maximum_music_probability: Probability = 0.35
    maximum_ambience_probability: Probability = 0.55
    maximum_overlap_probability: Probability = 0.35
    maximum_clipping_probability: Probability = 0.20
    maximum_reverb_probability: Probability = 0.70
    maximum_bandwidth_limit_probability: Probability = 0.80
    minimum_noise_probability_for_denoise: Probability = 0.65
    minimum_rumble_probability_for_filter: Probability = 0.75
    minimum_hum_probability_for_filter: Probability = 0.80
    transition_us: int = Field(default=25_000, ge=0, le=5_000_000)
    deterministic_filters_enabled: bool = True
    speech_denoise_enabled: bool = False
    admitted_speech_denoise_processor_id: Identifier | None = None
    admitted_speech_denoise_model_manifest_id: Identifier | None = None
    denoise_strength: float = Field(default=0.25, ge=0.0, le=0.5)
    high_pass_cutoff_hz: int = Field(default=70, ge=40, le=100)
    high_pass_slope_db_per_octave: Literal[12] = 12
    require_music_evidence_for_processing: Literal[True] = True

    @model_validator(mode="after")
    def valid_processor_admission(self) -> Self:
        admission_ids = (
            self.admitted_speech_denoise_processor_id,
            self.admitted_speech_denoise_model_manifest_id,
        )
        if self.speech_denoise_enabled and any(identifier is None for identifier in admission_ids):
            raise ValueError("speech denoise cannot be enabled without admitted processor and model-manifest IDs")
        return self


class ProcessingRouteDecision(ContractModel):
    decision_id: Identifier
    processing_region_id: Identifier
    semantic_region_ids: tuple[Identifier, ...] = Field(min_length=1)
    action: ProcessingAction
    processor_id: Identifier
    fallback_processor_id: Identifier | None = None
    reason_code: Identifier
    reason: str = Field(min_length=1, max_length=512)
    confidence: Probability
    parameters: dict[str, JsonScalar] = Field(default_factory=dict)
    warning_codes: tuple[Identifier, ...] = ()
    planning_only: Literal[True] = True


class ProcessingRouterReport(ContractModel):
    processing_router_report_id: Identifier
    run_id: Identifier
    semantic_map_id: Identifier
    recipe_version_id: Identifier
    settings_id: Identifier
    settings_sha256: Sha256
    algorithm_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    processing_plan_id: Identifier
    processing_plan_sha256: Sha256
    decisions: tuple[ProcessingRouteDecision, ...] = Field(min_length=1)
    override_ids: tuple[Identifier, ...] = ()
    protected_region_count: int = Field(ge=0)
    bypassed_region_count: int = Field(ge=0)
    deterministic_filter_region_count: int = Field(ge=0)
    denoise_region_count: int = Field(ge=0)
    leveler_region_count: int = Field(ge=0)
    warnings: tuple[str, ...] = ()
    planning_only: Literal[True] = True
    production_audio_changed: Literal[False] = False
    external_api_cost_usd: Literal[0] = 0

    @model_validator(mode="after")
    def valid_decision_counts(self) -> Self:
        expected_counts = {
            "protect": self.protected_region_count,
            "bypass": self.bypassed_region_count,
            "deterministic_filter": self.deterministic_filter_region_count,
            "denoise": self.denoise_region_count,
            "level": self.leveler_region_count,
        }
        observed_counts = {
            action: sum(decision.action == action for decision in self.decisions) for action in expected_counts
        }
        if observed_counts != expected_counts or sum(expected_counts.values()) != len(self.decisions):
            raise ValueError("processing-router action counts must cover every decision")
        if len({decision.decision_id for decision in self.decisions}) != len(self.decisions):
            raise ValueError("processing-router decision IDs must be unique")
        if len({decision.processing_region_id for decision in self.decisions}) != len(self.decisions):
            raise ValueError("processing-router decisions must reference unique processing regions")
        if len(set(self.override_ids)) != len(self.override_ids):
            raise ValueError("processing-router override IDs must be unique")
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


class GainRenderManifest(ContractModel):
    gain_render_manifest_id: Identifier
    run_id: Identifier
    source_sha256: Sha256
    gain_envelope_id: Identifier
    gain_envelope_sha256: Sha256
    renderer_build_id: Identifier
    renderer_algorithm_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    ffmpeg_version: str = Field(min_length=1, max_length=256)
    candidate_relative_path: str = Field(min_length=1, max_length=512)
    candidate_sha256: Sha256
    candidate_size_bytes: int = Field(gt=0)
    candidate_pcm_encoding: Literal["pcm_s24le"] = "pcm_s24le"
    sample_rate_hz: Literal[48_000] = 48_000
    channels: int = Field(gt=0, le=8)
    source_duration_us: Microseconds
    candidate_duration_us: Microseconds
    expected_frame_count: int = Field(gt=0)
    rendered_frame_count: int = Field(gt=0)
    frame_count_delta: int = Field(ge=-2, le=2)
    input_sample_peak_dbfs: float = Field(ge=-200.0, le=0.0)
    output_sample_peak_dbfs: float = Field(ge=-200.0, le=0.0)
    clipping_sample_count: Literal[0] = 0
    gain_min_db: float = Field(ge=-60.0, le=24.0)
    gain_max_db: float = Field(ge=-60.0, le=24.0)
    maximum_adjacent_gain_delta_db: float = Field(ge=0.0, le=0.001)
    interpolation: Literal["linear_db"] = "linear_db"
    channel_linked: Literal[True] = True
    sample_accurate: Literal[True] = True
    final_loudness_applied: Literal[False] = False
    listening_loudness_match_required: Literal[True] = True
    archived_source_immutable: Literal[True] = True
    evaluation_only: Literal[True] = True
    production_approved: Literal[False] = False
    external_api_cost_usd: Literal[0] = 0

    @model_validator(mode="after")
    def valid_gain_render(self) -> Self:
        path = PurePosixPath(self.candidate_relative_path)
        if path.is_absolute() or ".." in path.parts or path.suffix.lower() != ".wav":
            raise ValueError("gain-render candidates require a portable relative WAV path")
        if self.source_duration_us <= 0 or self.candidate_duration_us <= 0:
            raise ValueError("gain-render durations must be positive")
        if self.rendered_frame_count - self.expected_frame_count != self.frame_count_delta:
            raise ValueError("gain-render frame_count_delta must match rendered minus expected frames")
        if abs(self.candidate_duration_us - self.source_duration_us) > 50:
            raise ValueError("gain-render candidate duration must remain within 50 microseconds of the source")
        if self.gain_min_db > self.gain_max_db:
            raise ValueError("gain-render gain bounds are reversed")
        return self


class GainRenderRuntimeReport(ContractModel):
    gain_render_runtime_report_id: Identifier
    gain_render_manifest_id: Identifier
    wall_seconds: float = Field(gt=0.0)
    audio_seconds: float = Field(gt=0.0)
    real_time_factor: float = Field(ge=0.0)
    working_block_frames: int = Field(gt=0)
    peak_working_buffer_mb: float = Field(ge=0.0)
    device_summary: str = Field(min_length=1, max_length=256)
    external_api_cost_usd: Literal[0] = 0
    diagnostic_only: Literal[True] = True


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


class ListeningMode(StrEnum):
    PAIRWISE_PREFERENCE = "pairwise_preference"
    CLEAN_PRESERVATION = "clean_preservation"


class ListeningCandidateRole(StrEnum):
    ORIGINAL = "original"
    CANDIDATE = "candidate"
    REFERENCE = "reference"
    ANCHOR = "anchor"


class ListeningArtifactFlag(StrEnum):
    MUSICAL_NOISE = "musical_noise"
    CHIRPING_WARBLING = "chirping_warbling"
    WATERY_PHASEY_SPEECH = "watery_phasey_speech"
    ROBOTIC_VOICE_CHANGE = "robotic_voice_change"
    MISSING_PHONEME_OR_WORD = "missing_phoneme_or_word"
    PUMPING_BREATHING = "pumping_breathing"
    GATING_CHOPPING = "gating_chopping"
    TRANSIENT_SMEARING = "transient_smearing"
    SIBILANCE_HARSHNESS = "sibilance_harshness"
    MUFFLING_LOST_AIR = "muffling_lost_air"
    BASS_BOOM_MUD = "bass_boom_mud"
    PLOSIVE_DAMAGE = "plosive_damage"
    REVERB_TAIL_TRUNCATION = "reverb_tail_truncation"
    AMBIENCE_COLLAPSE = "ambience_collapse"
    MUSIC_DAMAGE = "music_damage"
    SPEAKER_LEVEL_INCONSISTENCY = "speaker_level_inconsistency"
    PROCESSING_BOUNDARY_CLICK = "processing_boundary_click"
    CLIPPING_DISTORTION = "clipping_distortion"
    TIMING_DRIFT = "timing_drift"
    IDENTITY_EMOTION_CHANGE = "identity_emotion_change"
    OTHER = "other"


class ListeningRuntimeMetrics(ContractModel):
    wall_seconds: float = Field(ge=0.0)
    peak_memory_mb: float | None = Field(default=None, ge=0.0)
    device_summary: str = Field(min_length=1, max_length=256)
    external_cost_usd: float = Field(default=0.0, ge=0.0)


class ListeningExperimentCandidate(ContractModel):
    candidate_id: Identifier
    relative_path: str = Field(min_length=1, max_length=512)
    archived_sha256: Sha256
    role: ListeningCandidateRole
    source_fixture_id: Identifier
    processor_id: Identifier
    processor_version: str = Field(min_length=1, max_length=128)
    recipe_version_id: Identifier | None = None
    model_manifest_ids: tuple[Identifier, ...] = ()
    engine_build_id: Identifier
    runtime: ListeningRuntimeMetrics
    archived_master_immutable: Literal[True] = True
    notes: str = Field(min_length=1, max_length=512)

    @model_validator(mode="after")
    def portable_audio_path(self) -> Self:
        path = PurePosixPath(self.relative_path)
        if path.is_absolute() or ".." in path.parts or path.suffix.lower() not in {".wav", ".flac", ".mp3"}:
            raise ValueError("listening candidates require a portable relative audio path")
        return self


class ListeningExperimentItem(ContractModel):
    item_id: Identifier
    mode: ListeningMode
    source_fixture_id: Identifier
    source_sha256: Sha256
    source_region_ids: tuple[Identifier, ...] = ()
    candidate_ids: tuple[Identifier, ...]
    segment_start_us: Microseconds = 0
    segment_end_us: Microseconds | None = None
    evaluation_prompt: str = Field(min_length=1, max_length=512)

    @model_validator(mode="after")
    def valid_candidate_set_and_segment(self) -> Self:
        if len(self.candidate_ids) < 2 or len(self.candidate_ids) != len(set(self.candidate_ids)):
            raise ValueError("listening items require at least two unique candidates")
        if len(self.source_region_ids) != len(set(self.source_region_ids)):
            raise ValueError("listening source region IDs must be unique")
        if self.mode is ListeningMode.CLEAN_PRESERVATION and len(self.candidate_ids) != 2:
            raise ValueError("clean-preservation items require exactly two candidates")
        if self.segment_end_us is not None and self.segment_end_us <= self.segment_start_us:
            raise ValueError("listening segments use non-empty half-open intervals")
        return self


class ListeningExperimentManifest(ContractModel):
    experiment_id: Identifier
    experiment_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    corpus_id: Identifier
    corpus_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    randomization_seed: int = Field(ge=0, le=2**63 - 1)
    target_integrated_lufs: float = Field(ge=-30.0, le=-12.0)
    max_true_peak_dbtp: float = Field(ge=-6.0, le=0.0)
    candidates: tuple[ListeningExperimentCandidate, ...]
    items: tuple[ListeningExperimentItem, ...]
    identity_reveal_policy: Literal["after_session_close"] = "after_session_close"
    objective_metrics_diagnostic_only: Literal[True] = True
    archived_masters_immutable: Literal[True] = True
    private_local_only: Literal[True] = True
    prohibited_sources: tuple[
        Literal["hosted_processor_service", "hosted_processor_output", "production_customer_media"], ...
    ]
    hypothesis: str = Field(min_length=1, max_length=1024)

    @model_validator(mode="after")
    def valid_experiment_graph(self) -> Self:
        if not self.candidates or not self.items:
            raise ValueError("listening experiments require candidates and items")
        required_prohibitions = {
            "hosted_processor_service",
            "hosted_processor_output",
            "production_customer_media",
        }
        if set(self.prohibited_sources) != required_prohibitions or len(self.prohibited_sources) != len(
            required_prohibitions
        ):
            raise ValueError("listening experiments require the complete unique prohibited-source boundary")
        candidate_ids = [candidate.candidate_id for candidate in self.candidates]
        paths = [candidate.relative_path for candidate in self.candidates]
        item_ids = [item.item_id for item in self.items]
        if len(candidate_ids) != len(set(candidate_ids)) or len(paths) != len(set(paths)):
            raise ValueError("candidate IDs and paths must be unique")
        if len(item_ids) != len(set(item_ids)):
            raise ValueError("listening item IDs must be unique")
        candidates = {candidate.candidate_id: candidate for candidate in self.candidates}
        used: set[str] = set()
        for item in self.items:
            missing = set(item.candidate_ids) - candidates.keys()
            if missing:
                raise ValueError(f"listening item {item.item_id} references unknown candidates")
            if any(
                candidates[candidate_id].source_fixture_id != item.source_fixture_id
                for candidate_id in item.candidate_ids
            ):
                raise ValueError("all item candidates must share its source_fixture_id")
            if item.mode is ListeningMode.CLEAN_PRESERVATION:
                roles = {candidates[candidate_id].role for candidate_id in item.candidate_ids}
                if ListeningCandidateRole.ORIGINAL not in roles or ListeningCandidateRole.CANDIDATE not in roles:
                    raise ValueError("clean-preservation items require original and candidate roles")
            source_controls = [
                candidates[candidate_id]
                for candidate_id in item.candidate_ids
                if candidates[candidate_id].role in {ListeningCandidateRole.ORIGINAL, ListeningCandidateRole.REFERENCE}
            ]
            if source_controls and all(
                candidate.archived_sha256 != item.source_sha256 for candidate in source_controls
            ):
                raise ValueError("item source_sha256 must match an original or reference candidate")
            used.update(item.candidate_ids)
        if used != set(candidate_ids):
            raise ValueError("every experiment candidate must be used by at least one item")
        return self


class ListeningOption(ContractModel):
    option_id: Identifier
    audio_relative_path: str = Field(min_length=1, max_length=512)
    listening_sha256: Sha256
    loudness: LoudnessMeasurement
    duration_us: Microseconds
    sample_rate_hz: int = Field(gt=0, le=192_000)
    channels: int = Field(gt=0, le=8)

    @model_validator(mode="after")
    def portable_listening_path(self) -> Self:
        path = PurePosixPath(self.audio_relative_path)
        if path.is_absolute() or ".." in path.parts or path.suffix.lower() != ".wav":
            raise ValueError("listening option path must be a portable WAV path")
        if self.duration_us <= 0:
            raise ValueError("listening option duration must be positive")
        return self


class ListeningTrial(ContractModel):
    trial_id: Identifier
    source_token: Identifier
    mode: ListeningMode
    evaluation_prompt: str = Field(min_length=1, max_length=512)
    options: tuple[ListeningOption, ...]

    @model_validator(mode="after")
    def valid_options(self) -> Self:
        option_ids = [option.option_id for option in self.options]
        if len(option_ids) < 2 or len(option_ids) != len(set(option_ids)):
            raise ValueError("listening trials require at least two unique options")
        if self.mode is ListeningMode.CLEAN_PRESERVATION and len(option_ids) != 2:
            raise ValueError("clean-preservation trials require exactly two options")
        return self


class ListeningSessionManifest(ContractModel):
    session_id: Identifier
    experiment_commitment_sha256: Sha256
    randomization_algorithm: Literal["sha256-seed-item-candidate-v1"]
    target_integrated_lufs: float
    max_true_peak_dbtp: float
    trials: tuple[ListeningTrial, ...]
    artifact_flags: tuple[ListeningArtifactFlag, ...]
    state: Literal["open"] = "open"
    identity_hidden: Literal[True] = True
    instructions: tuple[str, ...]

    @model_validator(mode="after")
    def valid_public_session(self) -> Self:
        trial_ids = [trial.trial_id for trial in self.trials]
        if not trial_ids or len(trial_ids) != len(set(trial_ids)):
            raise ValueError("public session trial IDs must be non-empty and unique")
        if set(self.artifact_flags) != set(ListeningArtifactFlag):
            raise ValueError("public sessions require the complete unique artifact taxonomy")
        if not self.instructions:
            raise ValueError("public session requires artifact flags and instructions")
        return self


class ListeningOptionRating(ContractModel):
    option_id: Identifier
    speech_quality: int = Field(ge=1, le=5)
    background_quality: int = Field(ge=1, le=5)
    overall_quality: int = Field(ge=1, le=5)
    artifact_flags: tuple[ListeningArtifactFlag, ...] = ()


class ListeningScore(ContractModel):
    score_id: Identifier
    session_id: Identifier
    trial_id: Identifier
    listener_id: Identifier
    mode: ListeningMode
    preferred_option_id: Identifier | None = None
    no_meaningful_preference: bool
    option_ratings: tuple[ListeningOptionRating, ...]
    confidence: int = Field(ge=1, le=5)
    trial_artifact_flags: tuple[ListeningArtifactFlag, ...] = ()
    audible_degradation: bool | None = None
    voice_identity_changed: bool | None = None
    speech_less_natural: bool | None = None
    ambience_or_music_changed: bool | None = None
    processing_preferred: bool | None = None
    notes: str | None = Field(default=None, max_length=1024)
    submission_sequence: int = Field(ge=1)

    @model_validator(mode="after")
    def valid_score(self) -> Self:
        if (self.preferred_option_id is None) == (not self.no_meaningful_preference):
            raise ValueError("select one preferred option or no meaningful preference")
        rating_ids = [rating.option_id for rating in self.option_ratings]
        if len(rating_ids) < 2 or len(rating_ids) != len(set(rating_ids)):
            raise ValueError("scores require unique ratings for every presented option")
        if self.preferred_option_id is not None and self.preferred_option_id not in rating_ids:
            raise ValueError("preferred_option_id must reference a rated option")
        clean_answers = (
            self.audible_degradation,
            self.voice_identity_changed,
            self.speech_less_natural,
            self.ambience_or_music_changed,
            self.processing_preferred,
        )
        if self.mode is ListeningMode.CLEAN_PRESERVATION and any(answer is None for answer in clean_answers):
            raise ValueError("clean-preservation scores require all preservation answers")
        if self.mode is ListeningMode.PAIRWISE_PREFERENCE and any(answer is not None for answer in clean_answers):
            raise ValueError("pairwise scores cannot include clean-preservation answers")
        if len(self.trial_artifact_flags) != len(set(self.trial_artifact_flags)) or any(
            len(rating.artifact_flags) != len(set(rating.artifact_flags)) for rating in self.option_ratings
        ):
            raise ValueError("artifact flags must be unique within their score scope")
        return self


class ListeningSessionState(ContractModel):
    session_id: Identifier
    state: Literal["open", "closed"]
    next_submission_sequence: int = Field(ge=1)
    score_ids: tuple[Identifier, ...] = ()
    report_sha256: Sha256 | None = None

    @model_validator(mode="after")
    def valid_state(self) -> Self:
        if len(self.score_ids) != len(set(self.score_ids)):
            raise ValueError("session state score IDs must be unique")
        if self.state == "open" and self.report_sha256 is not None:
            raise ValueError("open listening sessions cannot reference a report")
        if self.state == "closed" and self.report_sha256 is None:
            raise ValueError("closed listening sessions require a report hash")
        return self


class ListeningObjectiveMetrics(ContractModel):
    item_id: Identifier
    candidate_id: Identifier
    archived_sha256: Sha256
    listening_sha256: Sha256
    loudness_before: LoudnessMeasurement
    loudness_after: LoudnessMeasurement
    duration_us: Microseconds
    sample_rate_hz: int = Field(gt=0, le=192_000)
    channels: int = Field(gt=0, le=8)
    loudness_hop_us: Microseconds
    loudness_frame_count: int = Field(gt=0)
    momentary_lufs_min: float
    momentary_lufs_max: float
    short_term_lufs_min: float
    short_term_lufs_max: float
    sample_peak_dbfs: float = Field(ge=-200.0, le=0.0)
    clipping_sample_count: int = Field(ge=0)
    snr_db: float | None = None
    si_sdr_db: float | None = None
    runtime: ListeningRuntimeMetrics
    diagnostic_only: Literal[True] = True

    @model_validator(mode="after")
    def valid_loudness_timeline_summary(self) -> Self:
        if self.loudness_hop_us <= 0:
            raise ValueError("loudness diagnostic hop must be positive")
        if self.momentary_lufs_min > self.momentary_lufs_max:
            raise ValueError("momentary loudness bounds are reversed")
        if self.short_term_lufs_min > self.short_term_lufs_max:
            raise ValueError("short-term loudness bounds are reversed")
        return self


class ListeningIdentityReveal(ContractModel):
    trial_id: Identifier
    option_id: Identifier
    candidate_id: Identifier
    role: ListeningCandidateRole
    processor_id: Identifier
    processor_version: str
    recipe_version_id: Identifier | None = None
    model_manifest_ids: tuple[Identifier, ...] = ()
    engine_build_id: Identifier


class ListeningItemReveal(ContractModel):
    trial_id: Identifier
    item_id: Identifier
    source_fixture_id: Identifier
    source_sha256: Sha256
    source_region_ids: tuple[Identifier, ...] = ()
    segment_start_us: Microseconds
    segment_end_us: Microseconds | None = None
    evaluation_prompt: str = Field(min_length=1, max_length=512)

    @model_validator(mode="after")
    def valid_revealed_segment(self) -> Self:
        if len(self.source_region_ids) != len(set(self.source_region_ids)):
            raise ValueError("revealed source region IDs must be unique")
        if self.segment_end_us is not None and self.segment_end_us <= self.segment_start_us:
            raise ValueError("revealed listening segments use non-empty half-open intervals")
        return self


class PreparedListeningExperiment(ContractModel):
    prepared_experiment_id: Identifier
    experiment_commitment_sha256: Sha256
    experiment: ListeningExperimentManifest
    session: ListeningSessionManifest
    identity_reveals: tuple[ListeningIdentityReveal, ...]
    item_reveals: tuple[ListeningItemReveal, ...]
    objective_metrics: tuple[ListeningObjectiveMetrics, ...]

    @model_validator(mode="after")
    def valid_prepared_experiment(self) -> Self:
        from .serialization import manifest_sha256

        if manifest_sha256(self.experiment) != self.experiment_commitment_sha256:
            raise ValueError("experiment commitment must match the private experiment manifest")
        if self.session.experiment_commitment_sha256 != self.experiment_commitment_sha256:
            raise ValueError("session commitment must match the private experiment manifest")
        reveal_keys = [(reveal.trial_id, reveal.option_id) for reveal in self.identity_reveals]
        presented_keys = [
            (trial.trial_id, option.option_id) for trial in self.session.trials for option in trial.options
        ]
        if sorted(reveal_keys) != sorted(presented_keys):
            raise ValueError("private identity reveals must exactly cover public options")
        candidate_ids = {candidate.candidate_id for candidate in self.experiment.candidates}
        if any(reveal.candidate_id not in candidate_ids for reveal in self.identity_reveals):
            raise ValueError("private identity reveals must reference experiment candidates")
        item_reveals = {reveal.item_id: reveal for reveal in self.item_reveals}
        experiment_items = {item.item_id: item for item in self.experiment.items}
        if len(item_reveals) != len(self.item_reveals) or set(item_reveals) != set(experiment_items):
            raise ValueError("private item reveals must uniquely cover experiment items")
        if {reveal.trial_id for reveal in self.item_reveals} != {trial.trial_id for trial in self.session.trials}:
            raise ValueError("private item reveals must uniquely cover public trials")
        for item_id, reveal in item_reveals.items():
            item = experiment_items[item_id]
            if (
                reveal.source_fixture_id != item.source_fixture_id
                or reveal.source_sha256 != item.source_sha256
                or reveal.source_region_ids != item.source_region_ids
                or reveal.segment_start_us != item.segment_start_us
                or reveal.segment_end_us != item.segment_end_us
                or reveal.evaluation_prompt != item.evaluation_prompt
            ):
                raise ValueError("private item reveal metadata must match the experiment item")
        metric_keys = [(metric.item_id, metric.candidate_id) for metric in self.objective_metrics]
        expected_metric_keys = {
            (item.item_id, candidate_id) for item in self.experiment.items for candidate_id in item.candidate_ids
        }
        if set(metric_keys) != expected_metric_keys or len(metric_keys) != len(set(metric_keys)):
            raise ValueError("prepared objective metrics must exactly cover every item/candidate")
        return self


class CandidateListeningSummary(ContractModel):
    candidate_id: Identifier
    exposures: int = Field(ge=0)
    preference_wins: int = Field(ge=0)
    mean_speech_quality: float | None = Field(default=None, ge=1.0, le=5.0)
    mean_background_quality: float | None = Field(default=None, ge=1.0, le=5.0)
    mean_overall_quality: float | None = Field(default=None, ge=1.0, le=5.0)
    artifact_flag_counts: dict[ListeningArtifactFlag, int] = Field(default_factory=dict)
    clean_audible_degradation_count: int = Field(default=0, ge=0)
    clean_processing_preferred_count: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def valid_summary_counts(self) -> Self:
        bounded_counts = (
            self.preference_wins,
            self.clean_audible_degradation_count,
            self.clean_processing_preferred_count,
            *self.artifact_flag_counts.values(),
        )
        if any(count < 0 or count > self.exposures for count in bounded_counts):
            raise ValueError("candidate summary event counts cannot exceed exposures")
        return self


class ListeningReport(ContractModel):
    listening_report_id: Identifier
    experiment_id: Identifier
    experiment_version: str
    corpus_id: Identifier
    corpus_version: str
    session_id: Identifier
    experiment_commitment_sha256: Sha256
    closed: Literal[True] = True
    scores: tuple[ListeningScore, ...]
    identity_reveals: tuple[ListeningIdentityReveal, ...]
    item_reveals: tuple[ListeningItemReveal, ...]
    objective_metrics: tuple[ListeningObjectiveMetrics, ...]
    candidate_summaries: tuple[CandidateListeningSummary, ...]
    trial_count: int = Field(ge=1)
    score_count: int = Field(ge=0)
    no_preference_count: int = Field(ge=0)
    decision: Literal["descriptive_pilot_only"] = "descriptive_pilot_only"
    uncertainty_summary: str = Field(min_length=1, max_length=1024)
    human_approval_status: Literal["not_evaluated", "pilot_only", "approved", "rejected"]
    objective_metrics_diagnostic_only: Literal[True] = True
    external_api_cost_usd: float = Field(ge=0.0)
    warnings: tuple[str, ...]

    @model_validator(mode="after")
    def valid_report(self) -> Self:
        if self.score_count != len(self.scores):
            raise ValueError("score_count must match the serialized scores")
        if self.no_preference_count != sum(score.no_meaningful_preference for score in self.scores):
            raise ValueError("no_preference_count must match serialized scores")
        reveal_keys = [(reveal.trial_id, reveal.option_id) for reveal in self.identity_reveals]
        if not reveal_keys or len(reveal_keys) != len(set(reveal_keys)):
            raise ValueError("identity reveal trial/option pairs must be unique")
        revealed_trials = {trial_id for trial_id, _option_id in reveal_keys}
        if self.trial_count != len(revealed_trials):
            raise ValueError("trial_count must match identity-revealed trials")
        item_trial_ids = [reveal.trial_id for reveal in self.item_reveals]
        item_ids = [reveal.item_id for reveal in self.item_reveals]
        if (
            set(item_trial_ids) != revealed_trials
            or len(item_trial_ids) != len(set(item_trial_ids))
            or len(item_ids) != len(set(item_ids))
        ):
            raise ValueError("item reveals must uniquely cover identity-revealed trials and items")
        revealed_options = set(reveal_keys)
        score_ids = [score.score_id for score in self.scores]
        if len(score_ids) != len(set(score_ids)) or any(score.session_id != self.session_id for score in self.scores):
            raise ValueError("report scores must have unique IDs and reference its session")
        for score in self.scores:
            rated = {(score.trial_id, rating.option_id) for rating in score.option_ratings}
            presented = {key for key in revealed_options if key[0] == score.trial_id}
            if rated != presented:
                raise ValueError("report scores must exactly rate identity-revealed trial options")
        candidate_ids = [summary.candidate_id for summary in self.candidate_summaries]
        revealed_candidates = {reveal.candidate_id for reveal in self.identity_reveals}
        if set(candidate_ids) != revealed_candidates or len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError("candidate summaries must uniquely cover identity-revealed candidates")
        if any(metric.candidate_id not in revealed_candidates for metric in self.objective_metrics):
            raise ValueError("objective metrics must reference identity-revealed candidates")
        return self


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
    resolved_settings_id: Identifier
    resolved_settings_sha256: Sha256
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
    resolved_settings_id: Identifier
    resolved_settings_sha256: Sha256
    engine_build_id: Identifier
    status: RunStatus
    loudness_before: LoudnessMeasurement
    loudness_after: LoudnessMeasurement
    gain_envelope_id: Identifier | None = None
    leveler_statistics_id: Identifier | None = None
    cleanup_plan_id: Identifier
    cleanup_plan_sha256: Sha256
    step_ids: tuple[Identifier, ...]
    decisions: tuple[str, ...]
    artifact_sha256: dict[str, Sha256]
    warnings: tuple[str, ...] = ()
    external_api_cost_usd: float = Field(default=0.0, ge=0.0)
    privacy_summary: str = Field(min_length=1, max_length=512)
    reproducibility_summary: str = Field(min_length=1, max_length=512)

    @model_validator(mode="after")
    def cleanup_plan_reference_matches_artifact_hash(self) -> Self:
        if self.artifact_sha256.get("cleanup_plan") != self.cleanup_plan_sha256:
            raise ValueError("processing report cleanup-plan hash must match the artifact ledger")
        return self


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
