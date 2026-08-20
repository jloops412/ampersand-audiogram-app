from __future__ import annotations

import hashlib
import math
import wave
from array import array
from pathlib import Path

import pytest
from ampersand_contracts import FixtureAssetManifest, FixtureCorpusManifest, FixturePartition, read_manifest
from ampersand_test_fixtures import (
    LONG_FORM_FIXTURE_ID,
    fixture_catalog,
    generate_fixture_corpus,
    generate_long_form_control,
)
from pydantic import ValidationError


@pytest.fixture(scope="module")
def generated_corpora(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path, FixtureCorpusManifest]:
    root = tmp_path_factory.mktemp("fixture-corpus")
    first = root / "first"
    second = root / "second"
    first_manifest = generate_fixture_corpus(first)
    second_manifest = generate_fixture_corpus(second)
    assert first_manifest == second_manifest
    return first, second, first_manifest


def test_catalog_represents_required_controls_partitions_and_long_form() -> None:
    catalog = fixture_catalog()
    partitions = {spec.partition for spec in catalog}
    renderers = {spec.renderer for spec in catalog}

    assert partitions == {
        FixturePartition.DEVELOPMENT,
        FixturePartition.VALIDATION,
        FixturePartition.HIDDEN_TEST,
    }
    assert {
        "silence",
        "tone_impulse",
        "stereo_channels",
        "level_steps",
        "multi_speaker",
        "events",
        "protected_music",
        "hvac",
        "hum",
        "reverb",
        "clipping",
        "phone",
        "abrupt_environment",
        "long_form",
    } <= renderers
    long_form = next(spec for spec in catalog if spec.fixture_id == LONG_FORM_FIXTURE_ID)
    assert long_form.duration_seconds == 3_600
    assert long_form.long_form


def test_generated_corpus_is_byte_reproducible(generated_corpora: tuple[Path, Path, FixtureCorpusManifest]) -> None:
    first, second, _manifest = generated_corpora
    first_files = {
        str(path.relative_to(first)): path.read_bytes() for path in sorted(first.rglob("*")) if path.is_file()
    }
    second_files = {
        str(path.relative_to(second)): path.read_bytes() for path in sorted(second.rglob("*")) if path.is_file()
    }

    assert first_files == second_files


def test_manifests_record_hashes_rights_lineage_and_boundaries(
    generated_corpora: tuple[Path, Path, FixtureCorpusManifest],
) -> None:
    root, _second, generated = generated_corpora
    restored = read_manifest(root / "corpus-manifest.json", FixtureCorpusManifest)
    assert restored == generated
    assert restored.partitions_present == (FixturePartition.DEVELOPMENT, FixturePartition.VALIDATION)
    assert LONG_FORM_FIXTURE_ID not in {fixture.fixture_id for fixture in restored.fixtures}
    assert restored.external_api_cost_usd == 0
    assert set(restored.prohibited_sources) == {
        "hosted_processor_service",
        "hosted_processor_output",
        "production_customer_media",
    }

    by_id = {fixture.fixture_id: fixture for fixture in restored.fixtures}
    for fixture in restored.fixtures:
        audio = root / "audio" / fixture.filename
        assert _sha256_file(audio) == fixture.sha256
        assert audio.stat().st_size == fixture.size_bytes
        assert not fixture.contains_personal_data
        assert not fixture.contains_customer_media
        assert not fixture.contains_copyrighted_music
        assert fixture.generation_command[3] == "<output-directory>"
        assert all(region.end_us <= fixture.duration_us for region in fixture.regions)
        individual = read_manifest(
            root / "manifests" / f"{fixture.fixture_id.replace(':', '-')}.manifest.json",
            FixtureAssetManifest,
        )
        assert individual == fixture
        if fixture.parent_fixture_id is not None:
            parent = by_id[fixture.parent_fixture_id]
            assert parent.partition is fixture.partition
            assert fixture.parent_sha256 == parent.sha256
            assert fixture.session_group_id == parent.session_group_id


def test_audio_controls_have_known_levels_channels_and_silence(
    generated_corpora: tuple[Path, Path, FixtureCorpusManifest],
) -> None:
    root, _second, _manifest = generated_corpora
    silence = _read_pcm16(root / "audio/silence-development.wav")
    assert set(silence[0]) == {0}

    left, right = _read_pcm16(root / "audio/stereo-channel-development.wav")
    assert left != right
    assert math.isclose(_rms(left), _rms(right), rel_tol=0.01)

    mono = _read_pcm16(root / "audio/level-steps-development.wav")[0]
    sample_rate_hz = 48_000
    quiet = _rms(mono[round(1.2 * sample_rate_hz) : round(3.8 * sample_rate_hz)])
    reference = _rms(mono[round(4.2 * sample_rate_hz) : round(6.8 * sample_rate_hz)])
    loud = _rms(mono[round(7.2 * sample_rate_hz) : round(9.8 * sample_rate_hz)])
    assert 7.5 <= 20 * math.log10(reference / quiet) <= 8.5
    assert 7.5 <= 20 * math.log10(loud / reference) <= 8.5
    assert not any(mono[:sample_rate_hz])
    assert not any(mono[10 * sample_rate_hz :])


def test_hidden_partition_and_one_hour_control_require_explicit_generation(tmp_path: Path) -> None:
    hidden = generate_fixture_corpus(
        tmp_path / "hidden",
        fixture_ids=("fixture:clean-voice-hidden",),
    )
    assert hidden.partitions_present == (FixturePartition.HIDDEN_TEST,)
    assert len(hidden.fixtures) == 1
    assert hidden.fixtures[0].visibility == "promotion_withheld"

    long_path = generate_long_form_control(tmp_path / "continuity.wav", duration_seconds=16.0)
    with wave.open(str(long_path), "rb") as source:
        assert source.getframerate() == 16_000
        assert source.getnchannels() == 1
        assert source.getnframes() == 16 * 16_000
        first_cycle = source.readframes(8 * 16_000)
        second_cycle = source.readframes(8 * 16_000)
    assert first_cycle == second_cycle


def test_generator_refuses_to_overwrite_or_select_unknown_fixture(tmp_path: Path) -> None:
    destination = tmp_path / "corpus"
    generate_fixture_corpus(destination, fixture_ids=("fixture:silence-development",))
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        generate_fixture_corpus(destination)
    with pytest.raises(ValueError, match="unknown fixture IDs"):
        generate_fixture_corpus(tmp_path / "unknown", fixture_ids=("fixture:not-real",))


def test_contracts_reject_unsafe_synthetic_flags_and_cross_partition_lineage(
    generated_corpora: tuple[Path, Path, FixtureCorpusManifest],
) -> None:
    _root, _second, corpus = generated_corpora
    clean = next(fixture for fixture in corpus.fixtures if fixture.fixture_id == "fixture:clean-voice-validation")
    degraded = next(fixture for fixture in corpus.fixtures if fixture.fixture_id == "fixture:hvac-snr12-validation")

    unsafe_payload = clean.model_dump(mode="json")
    unsafe_payload["contains_customer_media"] = True
    with pytest.raises(ValidationError, match="synthetic controls"):
        FixtureAssetManifest.model_validate(unsafe_payload)

    hidden_parent_payload = clean.model_dump(mode="json")
    hidden_parent_payload["partition"] = "hidden_test"
    hidden_parent_payload["visibility"] = "promotion_withheld"
    hidden_parent = FixtureAssetManifest.model_validate(hidden_parent_payload)
    corpus_payload = corpus.model_dump(mode="json")
    corpus_payload["fixtures"] = [
        hidden_parent.model_dump(mode="json"),
        degraded.model_dump(mode="json"),
    ]
    corpus_payload["partitions_present"] = ["hidden_test", "validation"]
    with pytest.raises(ValidationError, match="same partition"):
        FixtureCorpusManifest.model_validate(corpus_payload)


def _read_pcm16(path: Path) -> tuple[array[int], ...]:
    with wave.open(str(path), "rb") as source:
        assert source.getsampwidth() == 2
        channels = source.getnchannels()
        interleaved = array("h")
        interleaved.frombytes(source.readframes(source.getnframes()))
    return tuple(array("h", interleaved[channel::channels]) for channel in range(channels))


def _rms(samples: array[int]) -> float:
    return math.sqrt(sum(sample * sample for sample in samples) / len(samples))


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
