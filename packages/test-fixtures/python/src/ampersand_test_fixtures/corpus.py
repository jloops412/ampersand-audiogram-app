from __future__ import annotations

import hashlib
import math
import shutil
import tempfile
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ampersand_contracts import (
    FixtureAssetManifest,
    FixtureConsentStatus,
    FixtureCorpusManifest,
    FixturePartition,
    FixtureRegion,
    FixtureRelationship,
    FixtureRightsStatus,
    FixtureSourceKind,
    FixtureTransform,
    write_manifest,
)

from .audio import (
    deterministic_noise_sample,
    harmonic_music_control,
    synthetic_voice_sample,
    write_pcm16_fixture,
    write_repeating_pcm16_fixture,
)

CORPUS_ID = "fixture-corpus:synthetic-controls-v0"
CORPUS_VERSION = "0.1.0"
GENERATOR_ID = "generator:ampersand-synthetic-corpus"
GENERATOR_VERSION = "0.2.0"
LONG_FORM_FIXTURE_ID = "fixture:continuity-one-hour-development"

RendererKey = Literal[
    "silence",
    "tone_impulse",
    "stereo_channels",
    "clean_voice",
    "level_steps",
    "protected_music",
    "multi_speaker",
    "events",
    "hvac",
    "hum",
    "reverb",
    "clipping",
    "phone",
    "abrupt_environment",
    "long_form",
]


@dataclass(frozen=True)
class TransformSpec:
    transform_id: str
    family: str
    seed: int | None
    parameters: dict[str, str | int | float | bool | None]


@dataclass(frozen=True)
class FixtureSpec:
    fixture_id: str
    filename: str
    partition: FixturePartition
    duration_seconds: float
    sample_rate_hz: int
    channels: int
    renderer: RendererKey
    relationship: FixtureRelationship
    session_group_id: str
    speaker_group_ids: tuple[str, ...]
    regions: tuple[FixtureRegion, ...]
    parent_fixture_id: str | None = None
    transforms: tuple[TransformSpec, ...] = ()
    long_form: bool = False


def fixture_catalog() -> tuple[FixtureSpec, ...]:
    """Return the immutable synthetic-control catalog, including withheld fixtures."""

    development = FixturePartition.DEVELOPMENT
    validation = FixturePartition.VALIDATION
    hidden = FixturePartition.HIDDEN_TEST
    return (
        FixtureSpec(
            fixture_id="fixture:silence-development",
            filename="silence-development.wav",
            partition=development,
            duration_seconds=2.0,
            sample_rate_hz=48_000,
            channels=1,
            renderer="silence",
            relationship=FixtureRelationship.STANDALONE_CONTROL,
            session_group_id="session:synthetic-silence-development",
            speaker_group_ids=(),
            regions=(_region("silence-development", 0, 0, 2, "silence", True, None, "Digital silence control."),),
        ),
        FixtureSpec(
            fixture_id="fixture:tone-impulse-development",
            filename="tone-impulse-development.wav",
            partition=development,
            duration_seconds=4.0,
            sample_rate_hz=48_000,
            channels=1,
            renderer="tone_impulse",
            relationship=FixtureRelationship.STANDALONE_CONTROL,
            session_group_id="session:synthetic-tone-impulse-development",
            speaker_group_ids=(),
            regions=(
                _region("tone-impulse-development", 0, 0, 1, "silence", True, None, "Leading silence."),
                _region("tone-impulse-development", 1, 1, 3, "unknown", True, None, "440 Hz level control."),
                _region("tone-impulse-development", 2, 3, 4, "transient", True, None, "Known impulses."),
            ),
        ),
        FixtureSpec(
            fixture_id="fixture:stereo-channel-development",
            filename="stereo-channel-development.wav",
            partition=development,
            duration_seconds=4.0,
            sample_rate_hz=48_000,
            channels=2,
            renderer="stereo_channels",
            relationship=FixtureRelationship.STANDALONE_CONTROL,
            session_group_id="session:synthetic-stereo-development",
            speaker_group_ids=(),
            regions=(
                _region(
                    "stereo-channel-development",
                    0,
                    0,
                    4,
                    "unknown",
                    True,
                    None,
                    "Independent 220 Hz left and 330 Hz right channel controls.",
                ),
            ),
        ),
        _voice_spec("clean-voice-development", development, "clean_voice", FixtureRelationship.CLEAN_CONTROL),
        FixtureSpec(
            fixture_id="fixture:level-steps-development",
            filename="level-steps-development.wav",
            partition=development,
            duration_seconds=12.0,
            sample_rate_hz=48_000,
            channels=1,
            renderer="level_steps",
            relationship=FixtureRelationship.STANDALONE_CONTROL,
            session_group_id="session:synthetic-level-steps-development",
            speaker_group_ids=("speaker:synthetic-a-development",),
            regions=(
                _region("level-steps-development", 0, 0, 1, "silence", True, None, "Leading silence."),
                _region("level-steps-development", 1, 1, 4, "speech", False, -8.0, "Quiet voice-shaped control."),
                _region("level-steps-development", 2, 4, 7, "speech", False, 0.0, "Reference voice level."),
                _region("level-steps-development", 3, 7, 10, "speech", False, 8.0, "Loud voice-shaped control."),
                _region("level-steps-development", 4, 10, 12, "silence", True, None, "Trailing silence."),
            ),
        ),
        _protected_music_spec("protected-music-development", development),
        FixtureSpec(
            fixture_id=LONG_FORM_FIXTURE_ID,
            filename="continuity-one-hour-development.wav",
            partition=development,
            duration_seconds=3_600.0,
            sample_rate_hz=16_000,
            channels=1,
            renderer="long_form",
            relationship=FixtureRelationship.STANDALONE_CONTROL,
            session_group_id="session:synthetic-continuity-development",
            speaker_group_ids=("speaker:synthetic-a-development", "speaker:synthetic-b-development"),
            regions=(
                _region(
                    "continuity-one-hour-development",
                    0,
                    0,
                    3_600,
                    "mixed",
                    True,
                    None,
                    "An eight-second two-speaker/silence/music/noise control cycle repeated for one hour.",
                ),
            ),
            long_form=True,
        ),
        _voice_spec("clean-voice-validation", validation, "clean_voice", FixtureRelationship.CLEAN_CONTROL),
        FixtureSpec(
            fixture_id="fixture:multi-speaker-validation",
            filename="multi-speaker-validation.wav",
            partition=validation,
            duration_seconds=12.0,
            sample_rate_hz=48_000,
            channels=1,
            renderer="multi_speaker",
            relationship=FixtureRelationship.STANDALONE_CONTROL,
            session_group_id="session:synthetic-multi-speaker-validation",
            speaker_group_ids=("speaker:synthetic-a-validation", "speaker:synthetic-b-validation"),
            regions=(
                _region("multi-speaker-validation", 0, 0, 3, "speech", False, -4.0, "Quieter speaker A."),
                _region("multi-speaker-validation", 1, 3, 6, "speech", False, 5.0, "Louder speaker B."),
                _region("multi-speaker-validation", 2, 6, 9, "speech", False, -4.0, "Speaker A returns."),
                _region("multi-speaker-validation", 3, 9, 12, "speech", False, 5.0, "Speaker B returns."),
            ),
        ),
        FixtureSpec(
            fixture_id="fixture:events-validation",
            filename="events-validation.wav",
            partition=validation,
            duration_seconds=10.0,
            sample_rate_hz=48_000,
            channels=1,
            renderer="events",
            relationship=FixtureRelationship.STANDALONE_CONTROL,
            session_group_id="session:synthetic-events-validation",
            speaker_group_ids=("speaker:synthetic-a-validation",),
            regions=(
                _region("events-validation", 0, 0, 2, "noise", True, None, "Breath-like noise control."),
                _region("events-validation", 1, 2, 4, "speech", False, -18.0, "Legitimate whisper control."),
                _region("events-validation", 2, 4, 6, "speech", True, None, "Laughter-like harmonic control."),
                _region("events-validation", 3, 6, 8, "transient", True, None, "Applause-like impulses."),
                _region("events-validation", 4, 8, 10, "transient", True, None, "Isolated transient and silence."),
            ),
        ),
        _degraded_spec(
            "hvac-snr12-validation",
            validation,
            "hvac",
            TransformSpec(
                "transform:hvac-snr12-validation",
                "stationary-hvac",
                12_041,
                {"nominal_snr_db": 12.0, "noise_color": "low_frequency_weighted"},
            ),
        ),
        _degraded_spec(
            "hum-60-validation",
            validation,
            "hum",
            TransformSpec(
                "transform:hum-60-validation",
                "mains-hum",
                None,
                {"fundamental_hz": 60.0, "harmonic_hz": 120.0},
            ),
        ),
        _degraded_spec(
            "reverb-validation",
            validation,
            "reverb",
            TransformSpec(
                "transform:reverb-validation",
                "deterministic-echo-train",
                None,
                {"delays_ms": "90,170,310", "gains": "0.35,0.22,0.12"},
            ),
        ),
        _degraded_spec(
            "clipping-validation",
            validation,
            "clipping",
            TransformSpec(
                "transform:clipping-validation",
                "hard-clipping",
                None,
                {"pregain_db": 12.0, "threshold": 0.34},
            ),
        ),
        _degraded_spec(
            "phone-bandwidth-validation",
            validation,
            "phone",
            TransformSpec(
                "transform:phone-bandwidth-validation",
                "narrowband-quantized",
                None,
                {"sample_rate_hz": 16_000, "quantization_steps": 64},
            ),
            sample_rate_hz=16_000,
        ),
        _degraded_spec(
            "abrupt-environment-validation",
            validation,
            "abrupt_environment",
            TransformSpec(
                "transform:abrupt-environment-validation",
                "environment-step",
                41_911,
                {"transition_at_seconds": 4.0, "post_transition_noise_gain": 0.12},
            ),
        ),
        _voice_spec("clean-voice-hidden", hidden, "clean_voice", FixtureRelationship.CLEAN_CONTROL),
        FixtureSpec(
            fixture_id="fixture:level-steps-hidden",
            filename="level-steps-hidden.wav",
            partition=hidden,
            duration_seconds=12.0,
            sample_rate_hz=48_000,
            channels=1,
            renderer="level_steps",
            relationship=FixtureRelationship.STANDALONE_CONTROL,
            session_group_id="session:synthetic-level-steps-hidden",
            speaker_group_ids=("speaker:synthetic-a-hidden",),
            regions=(
                _region("level-steps-hidden", 0, 0, 1, "silence", True, None, "Leading silence."),
                _region("level-steps-hidden", 1, 1, 4, "speech", False, -8.0, "Quiet control."),
                _region("level-steps-hidden", 2, 4, 7, "speech", False, 0.0, "Reference control."),
                _region("level-steps-hidden", 3, 7, 10, "speech", False, 8.0, "Loud control."),
                _region("level-steps-hidden", 4, 10, 12, "silence", True, None, "Trailing silence."),
            ),
        ),
        _protected_music_spec("protected-music-hidden", hidden),
    )


def generate_fixture_corpus(
    destination: Path,
    *,
    partitions: tuple[FixturePartition, ...] = (
        FixturePartition.DEVELOPMENT,
        FixturePartition.VALIDATION,
    ),
    include_long_form: bool = False,
    fixture_ids: tuple[str, ...] = (),
) -> FixtureCorpusManifest:
    """Generate an immutable corpus directory and its validated lineage manifests."""

    if destination.exists():
        raise FileExistsError(f"refusing to overwrite existing corpus: {destination}")
    catalog = fixture_catalog()
    by_id = {spec.fixture_id: spec for spec in catalog}
    requested_ids = set(fixture_ids)
    unknown = requested_ids - by_id.keys()
    if unknown:
        raise ValueError(f"unknown fixture IDs: {', '.join(sorted(unknown))}")
    if requested_ids:
        selected_ids = requested_ids.copy()
    else:
        selected_ids = {
            spec.fixture_id
            for spec in catalog
            if spec.partition in partitions and (include_long_form or not spec.long_form)
        }
    for fixture_id in tuple(selected_ids):
        parent_id = by_id[fixture_id].parent_fixture_id
        if parent_id is not None:
            selected_ids.add(parent_id)
    selected = tuple(spec for spec in catalog if spec.fixture_id in selected_ids)
    if not selected:
        raise ValueError("fixture selection cannot be empty")

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{destination.name}-", dir=destination.parent))
    try:
        audio_directory = temporary / "audio"
        manifests_directory = temporary / "manifests"
        audio_directory.mkdir()
        manifests_directory.mkdir()
        manifests: dict[str, FixtureAssetManifest] = {}
        for spec in selected:
            output = audio_directory / spec.filename
            _render(spec, output)
            parent = manifests.get(spec.parent_fixture_id) if spec.parent_fixture_id is not None else None
            if spec.parent_fixture_id is not None and parent is None:
                raise ValueError(f"fixture catalog parent order is invalid for {spec.fixture_id}")
            manifest = _build_manifest(spec, output, parent)
            manifests[spec.fixture_id] = manifest
            manifest_name = spec.fixture_id.replace(":", "-") + ".manifest.json"
            write_manifest(manifests_directory / manifest_name, manifest)

        ordered_manifests = tuple(manifests[spec.fixture_id] for spec in selected)
        partitions_present = tuple(sorted({manifest.partition for manifest in ordered_manifests}, key=str))
        selection_identity = hashlib.sha256(
            "|".join(f"{manifest.fixture_id}:{manifest.sha256}" for manifest in ordered_manifests).encode("utf-8")
        ).hexdigest()[:16]
        corpus = FixtureCorpusManifest(
            corpus_id=f"{CORPUS_ID}:{selection_identity}",
            corpus_version=CORPUS_VERSION,
            generator_id=GENERATOR_ID,
            generator_version=GENERATOR_VERSION,
            fixtures=ordered_manifests,
            partitions_present=partitions_present,
            prohibited_sources=(
                "hosted_processor_service",
                "hosted_processor_output",
                "production_customer_media",
            ),
            governance_summary=(
                "Mathematical PCM controls only: no recorded speech, customer media, copied composition, model output, "
                "or external hosted-processor output. Hidden-test labels are governance markers; "
                "promotion evidence requires separately access-controlled rights-cleared material."
            ),
        )
        write_manifest(temporary / "corpus-manifest.json", corpus)
        if destination.exists():
            raise FileExistsError(f"refusing to overwrite corpus created during generation: {destination}")
        temporary.replace(destination)
        return corpus
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def generate_long_form_control(path: Path, *, duration_seconds: float = 3_600.0) -> Path:
    """Generate the bounded-memory repeating long-form durability control."""

    if duration_seconds < 8.0:
        raise ValueError("long-form control must contain at least one eight-second cycle")
    sample_rate_hz = 16_000

    def sample_at(frame_index: int, _channel: int) -> float:
        local_time = frame_index / sample_rate_hz
        if local_time < 2.0:
            return 0.12 * synthetic_voice_sample(frame_index, sample_rate_hz, speaker_index=0)
        if local_time < 4.0:
            return 0.30 * synthetic_voice_sample(frame_index, sample_rate_hz, speaker_index=1)
        if local_time < 5.0:
            return 0.0
        if local_time < 7.0:
            return 0.16 * synthetic_voice_sample(
                frame_index, sample_rate_hz, speaker_index=0
            ) + 0.08 * harmonic_music_control(frame_index, sample_rate_hz)
        return 0.04 * deterministic_noise_sample(frame_index, seed=73_031)

    return write_repeating_pcm16_fixture(
        path,
        duration_seconds=duration_seconds,
        sample_rate_hz=sample_rate_hz,
        channels=1,
        block_duration_seconds=8.0,
        sample_at=sample_at,
    )


def _render(spec: FixtureSpec, output: Path) -> None:
    if spec.renderer == "long_form":
        generate_long_form_control(output, duration_seconds=spec.duration_seconds)
        return

    def sample_at(frame_index: int, channel: int) -> float:
        return _sample(spec.renderer, frame_index, channel, spec.sample_rate_hz, spec.duration_seconds)

    write_pcm16_fixture(
        output,
        duration_seconds=spec.duration_seconds,
        sample_rate_hz=spec.sample_rate_hz,
        channels=spec.channels,
        sample_at=sample_at,
    )


def _sample(
    renderer: RendererKey,
    frame_index: int,
    channel: int,
    sample_rate_hz: int,
    duration_seconds: float,
) -> float:
    time_seconds = frame_index / sample_rate_hz
    clean = 0.20 * _gated_voice(frame_index, sample_rate_hz, duration_seconds, speaker_index=0)
    if renderer == "silence":
        return 0.0
    if renderer == "tone_impulse":
        if 1.0 <= time_seconds < 3.0:
            return 0.20 * math.sin(2.0 * math.pi * 440.0 * time_seconds)
        if frame_index in {3 * sample_rate_hz, round(3.5 * sample_rate_hz)}:
            return 0.90
        return 0.0
    if renderer == "stereo_channels":
        frequency = 220.0 if channel == 0 else 330.0
        return 0.20 * math.sin(2.0 * math.pi * frequency * time_seconds)
    if renderer == "clean_voice":
        return clean
    if renderer == "level_steps":
        if 1.0 <= time_seconds < 4.0:
            amplitude = 0.08
        elif 4.0 <= time_seconds < 7.0:
            amplitude = 0.20
        elif 7.0 <= time_seconds < 10.0:
            amplitude = 0.50
        else:
            return 0.0
        return amplitude * synthetic_voice_sample(frame_index, sample_rate_hz, speaker_index=0)
    if renderer == "protected_music":
        music = harmonic_music_control(frame_index, sample_rate_hz)
        if time_seconds < 2.0:
            return 0.18 * music
        if time_seconds < 8.0:
            return 0.18 * synthetic_voice_sample(frame_index, sample_rate_hz, speaker_index=0) + 0.10 * music
        if time_seconds < 10.0:
            return 0.0
        return 0.20 * synthetic_voice_sample(frame_index, sample_rate_hz, speaker_index=0)
    if renderer == "multi_speaker":
        segment = min(3, int(time_seconds // 3.0))
        speaker_index = segment % 2
        amplitude = 0.12 if speaker_index == 0 else 0.34
        return amplitude * synthetic_voice_sample(frame_index, sample_rate_hz, speaker_index=speaker_index)
    if renderer == "events":
        if time_seconds < 2.0:
            return 0.035 * deterministic_noise_sample(frame_index, seed=83_021)
        if time_seconds < 4.0:
            return 0.025 * synthetic_voice_sample(
                frame_index, sample_rate_hz, speaker_index=0
            ) + 0.015 * deterministic_noise_sample(frame_index, seed=83_021)
        if time_seconds < 6.0:
            laugh = abs(math.sin(2.0 * math.pi * 2.4 * time_seconds))
            return 0.30 * laugh * synthetic_voice_sample(frame_index, sample_rate_hz, speaker_index=1)
        if time_seconds < 8.0:
            impulse = 0.65 if frame_index % max(1, sample_rate_hz // 9) < 8 else 0.0
            return impulse + 0.06 * deterministic_noise_sample(frame_index, seed=91_111)
        return 0.80 if frame_index == 9 * sample_rate_hz else 0.0
    if renderer == "hvac":
        white = deterministic_noise_sample(frame_index, seed=12_041)
        slow = math.sin(2.0 * math.pi * 47.0 * time_seconds) + 0.5 * math.sin(2.0 * math.pi * 93.0 * time_seconds)
        return clean + 0.035 * white + 0.025 * slow
    if renderer == "hum":
        hum = 0.045 * math.sin(2.0 * math.pi * 60.0 * time_seconds) + 0.018 * math.sin(
            2.0 * math.pi * 120.0 * time_seconds + 0.3
        )
        return clean + hum
    if renderer == "reverb":
        value = clean
        for delay_ms, gain in ((90, 0.35), (170, 0.22), (310, 0.12)):
            delayed = frame_index - round(delay_ms * sample_rate_hz / 1_000)
            if delayed >= 0:
                value += gain * 0.20 * _gated_voice(delayed, sample_rate_hz, duration_seconds, speaker_index=0)
        return value
    if renderer == "clipping":
        return max(-0.34, min(0.34, clean * 4.0))
    if renderer == "phone":
        narrow = 0.24 * _gated_voice(frame_index, sample_rate_hz, duration_seconds, speaker_index=0)
        return round(narrow * 32.0) / 32.0
    if renderer == "abrupt_environment":
        if time_seconds < 4.0:
            return clean
        return clean + 0.12 * deterministic_noise_sample(frame_index, seed=41_911)
    raise ValueError(f"unsupported fixture renderer: {renderer}")


def _build_manifest(
    spec: FixtureSpec,
    audio_path: Path,
    parent: FixtureAssetManifest | None,
) -> FixtureAssetManifest:
    with wave.open(str(audio_path), "rb") as source:
        frame_count = source.getnframes()
        sample_rate_hz = source.getframerate()
        channels = source.getnchannels()
        if source.getsampwidth() != 2:
            raise ValueError("synthetic corpus generator must emit PCM16 WAV")
    transforms = tuple(
        FixtureTransform(
            transform_id=transform.transform_id,
            family=transform.family,
            implementation_version=GENERATOR_VERSION,
            seed=transform.seed,
            parameters=transform.parameters,
        )
        for transform in spec.transforms
    )
    visibility: Literal["development_visible", "validation_visible", "promotion_withheld"]
    if spec.partition is FixturePartition.DEVELOPMENT:
        visibility = "development_visible"
    elif spec.partition is FixturePartition.VALIDATION:
        visibility = "validation_visible"
    else:
        visibility = "promotion_withheld"
    return FixtureAssetManifest(
        fixture_id=spec.fixture_id,
        corpus_version=CORPUS_VERSION,
        partition=spec.partition,
        visibility=visibility,
        filename=spec.filename,
        sha256=_sha256_file(audio_path),
        size_bytes=audio_path.stat().st_size,
        duration_us=round(frame_count * 1_000_000 / sample_rate_hz),
        sample_rate_hz=sample_rate_hz,
        channels=channels,
        sample_width_bits=16,
        source_kind=FixtureSourceKind.SYNTHETIC_CONTROL,
        rights_status=FixtureRightsStatus.MATHEMATICAL_GENERATION,
        consent_status=FixtureConsentStatus.NOT_APPLICABLE_SYNTHETIC,
        contains_personal_data=False,
        contains_customer_media=False,
        contains_copyrighted_music=False,
        session_group_id=spec.session_group_id,
        speaker_group_ids=spec.speaker_group_ids,
        relationship=spec.relationship,
        parent_fixture_id=parent.fixture_id if parent is not None else None,
        parent_sha256=parent.sha256 if parent is not None else None,
        transforms=transforms,
        regions=spec.regions,
        generator_id=GENERATOR_ID,
        generator_version=GENERATOR_VERSION,
        generation_command=(
            "uv",
            "run",
            "ampersand-generate-corpus",
            "<output-directory>",
            "--fixture",
            spec.fixture_id,
        ),
        permitted_environments=("environment:local-development", "environment:isolated-audio-lab"),
        permitted_processor_classes=(
            "processor-class:deterministic-engine",
            "processor-class:approved-lab-candidate",
        ),
        retention_class="retention:regenerable-synthetic",
        deletion_policy="May be deleted at any time and reproduced byte-for-byte from the versioned generator.",
    )


def _voice_spec(
    slug: str,
    partition: FixturePartition,
    renderer: RendererKey,
    relationship: FixtureRelationship,
) -> FixtureSpec:
    partition_label = _partition_label(partition)
    return FixtureSpec(
        fixture_id=f"fixture:{slug}",
        filename=f"{slug}.wav",
        partition=partition,
        duration_seconds=8.0,
        sample_rate_hz=48_000,
        channels=1,
        renderer=renderer,
        relationship=relationship,
        session_group_id=f"session:synthetic-voice-{partition_label}",
        speaker_group_ids=(f"speaker:synthetic-a-{partition_label}",),
        regions=(
            _region(slug, 0, 0, 0.5, "silence", True, None, "Leading silence."),
            _region(slug, 1, 0.5, 7.5, "speech", False, 0.0, "Clean voice-shaped mathematical control."),
            _region(slug, 2, 7.5, 8, "silence", True, None, "Trailing silence."),
        ),
    )


def _protected_music_spec(slug: str, partition: FixturePartition) -> FixtureSpec:
    partition_label = _partition_label(partition)
    return FixtureSpec(
        fixture_id=f"fixture:{slug}",
        filename=f"{slug}.wav",
        partition=partition,
        duration_seconds=12.0,
        sample_rate_hz=48_000,
        channels=1,
        renderer="protected_music",
        relationship=FixtureRelationship.STANDALONE_CONTROL,
        session_group_id=f"session:synthetic-protected-music-{partition_label}",
        speaker_group_ids=(f"speaker:synthetic-a-{partition_label}",),
        regions=(
            _region(slug, 0, 0, 2, "music", True, None, "Original mathematical chord control; protect."),
            _region(slug, 1, 2, 8, "mixed", True, None, "Voice-shaped signal over protected chord control."),
            _region(slug, 2, 8, 10, "silence", True, None, "Protected pause."),
            _region(slug, 3, 10, 12, "speech", False, 0.0, "Unaccompanied voice-shaped control."),
        ),
    )


def _degraded_spec(
    slug: str,
    partition: FixturePartition,
    renderer: RendererKey,
    transform: TransformSpec,
    *,
    sample_rate_hz: int = 48_000,
) -> FixtureSpec:
    partition_label = _partition_label(partition)
    boundary_role: Literal["silence", "noise", "unknown"]
    if renderer in {"hvac", "hum", "abrupt_environment"}:
        boundary_role = "noise"
    elif renderer == "reverb":
        boundary_role = "unknown"
    else:
        boundary_role = "silence"
    return FixtureSpec(
        fixture_id=f"fixture:{slug}",
        filename=f"{slug}.wav",
        partition=partition,
        duration_seconds=8.0,
        sample_rate_hz=sample_rate_hz,
        channels=1,
        renderer=renderer,
        relationship=FixtureRelationship.DEGRADED_FROM_CLEAN,
        parent_fixture_id=f"fixture:clean-voice-{partition_label}",
        transforms=(transform,),
        session_group_id=f"session:synthetic-voice-{partition_label}",
        speaker_group_ids=(f"speaker:synthetic-a-{partition_label}",),
        regions=(
            _region(slug, 0, 0, 0.5, boundary_role, True, None, "Leading background/control interval."),
            _region(slug, 1, 0.5, 7.5, "speech", False, 0.0, "Deterministically degraded voice control."),
            _region(slug, 2, 7.5, 8, boundary_role, True, None, "Trailing background/control interval."),
        ),
    )


def _region(
    slug: str,
    index: int,
    start_seconds: float,
    end_seconds: float,
    expected_role: Literal["speech", "silence", "noise", "music", "transient", "mixed", "unknown"],
    protected: bool,
    target_relative_level_db: float | None,
    notes: str,
) -> FixtureRegion:
    speaker = None
    if expected_role in {"speech", "mixed"}:
        speaker = "speaker:synthetic-control"
    return FixtureRegion(
        fixture_region_id=f"fixture-region:{slug}:{index}",
        start_us=round(start_seconds * 1_000_000),
        end_us=round(end_seconds * 1_000_000),
        expected_role=expected_role,
        speaker_label=speaker,
        protected=protected,
        target_relative_level_db=target_relative_level_db,
        notes=notes,
    )


def _partition_label(partition: FixturePartition) -> str:
    if partition is FixturePartition.HIDDEN_TEST:
        return "hidden"
    return partition.value


def _gated_voice(
    frame_index: int,
    sample_rate_hz: int,
    duration_seconds: float,
    *,
    speaker_index: int,
) -> float:
    time_seconds = frame_index / sample_rate_hz
    if time_seconds < 0.5 or time_seconds >= duration_seconds - 0.5:
        return 0.0
    fade = min(1.0, (time_seconds - 0.5) / 0.1, (duration_seconds - 0.5 - time_seconds) / 0.1)
    return max(0.0, fade) * synthetic_voice_sample(frame_index, sample_rate_hz, speaker_index=speaker_index)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
