from __future__ import annotations

import random
from itertools import pairwise
from pathlib import Path

from ampersand_contracts import (
    EvidenceProvenance,
    ObservationKind,
    ObservationUnit,
    ProcessingEligibility,
    SemanticMap,
    SemanticObservation,
    canonical_json_bytes,
    migrate_semantic_map_payload,
)
from ampersand_engine.semantic_adapters import (
    normalize_speaker_segments,
    normalize_transcript_segments,
    normalize_vad_frames,
)
from ampersand_engine.semantic_debug import write_semantic_debug_report
from ampersand_engine.semantic_fusion import fuse_semantic_map
from ampersand_engine.semantic_types import SpeakerSegment, TranscriptSegment, VadFrame


def test_vad_probabilities_fuse_into_full_coverage_and_round_trip(tmp_path: Path) -> None:
    provenance = _provenance("provider:vad-one")
    frames = (
        _vad_frame(0, 100_000, speech=0.04, silence=0.94),
        _vad_frame(100_000, 200_000, speech=0.82, silence=0.04),
        _vad_frame(200_000, 300_000, speech=0.75, silence=0.08),
        _vad_frame(300_000, 350_000, speech=0.08, silence=0.90),
    )
    observations = normalize_vad_frames(frames, provenance=provenance, id_seed="round-trip")
    semantic_map = fuse_semantic_map(
        semantic_map_id="semantic-map:round-trip",
        source_asset_id="asset:source",
        duration_us=350_000,
        provenance_sources=(provenance,),
        observations=observations,
        analysis_hop_us=100_000,
    )

    assert [(region.start_us, region.end_us) for region in semantic_map.regions] == [
        (0, 100_000),
        (100_000, 200_000),
        (200_000, 300_000),
        (300_000, 350_000),
    ]
    assert semantic_map.regions[0].processing_eligibility is ProcessingEligibility.NO_OP
    assert semantic_map.regions[1].processing_eligibility is ProcessingEligibility.ELIGIBLE
    assert SemanticMap.model_validate_json(canonical_json_bytes(semantic_map)) == semantic_map

    debug_path = tmp_path / "semantic-debug.html"
    write_semantic_debug_report(debug_path, semantic_map)
    debug = debug_path.read_text(encoding="utf-8")
    assert "Semantic Audio Map V0" in debug
    assert "speech_probability" in debug


def test_conflicting_provider_evidence_is_explicit_and_protected() -> None:
    first_provenance = _provenance("provider:vad-one")
    second_provenance = _provenance("provider:vad-two")
    first = normalize_vad_frames(
        (_vad_frame(0, 100_000, speech=0.95, silence=0.02),),
        provenance=first_provenance,
        id_seed="conflict-a",
    )
    second = normalize_vad_frames(
        (_vad_frame(0, 100_000, speech=0.05, silence=0.93),),
        provenance=second_provenance,
        id_seed="conflict-b",
    )
    semantic_map = fuse_semantic_map(
        semantic_map_id="semantic-map:conflict",
        source_asset_id="asset:source",
        duration_us=100_000,
        provenance_sources=(first_provenance, second_provenance),
        observations=(*first, *second),
    )

    assert semantic_map.conflicts
    assert semantic_map.regions[0].content_label == "mixed"
    assert semantic_map.regions[0].protected is True
    assert semantic_map.regions[0].processing_eligibility is ProcessingEligibility.PROTECT
    all_ids = {observation.observation_id for observation in semantic_map.observations}
    assert all(set(conflict.observation_ids) <= all_ids for conflict in semantic_map.conflicts)
    assert semantic_map.regions[0].observations["speech_probability_min"] == 0.05
    assert semantic_map.regions[0].observations["speech_probability_max"] == 0.95


def test_optional_transcript_and_speaker_adapters_share_timeline_without_becoming_required() -> None:
    transcript_provenance = _provenance("provider:mock-asr")
    speaker_provenance = _provenance("provider:mock-speaker")
    transcript = normalize_transcript_segments(
        (TranscriptSegment(0, 180_000, "Synthetic words", 0.91, "en"),),
        provenance=transcript_provenance,
        id_seed="mock-asr",
    )
    speakers = normalize_speaker_segments(
        (SpeakerSegment(0, 180_000, "speaker-a", 0.88),),
        provenance=speaker_provenance,
        id_seed="mock-speaker",
    )
    with_optional = fuse_semantic_map(
        semantic_map_id="semantic-map:optional",
        source_asset_id="asset:source",
        duration_us=200_000,
        provenance_sources=(transcript_provenance, speaker_provenance),
        observations=(*transcript, *speakers),
        unavailable_adapters=("adapter:music-unavailable",),
    )
    without_optional = fuse_semantic_map(
        semantic_map_id="semantic-map:no-asr",
        source_asset_id="asset:source",
        duration_us=200_000,
        observations=(),
        unavailable_adapters=("adapter:asr-unavailable", "adapter:diarization-unavailable"),
    )

    assert with_optional.regions[0].active_speaker == "speaker-a"
    assert any(observation.kind is ObservationKind.TRANSCRIPT_SEGMENT for observation in with_optional.observations)
    assert without_optional.regions[-1].end_us == without_optional.duration_us
    assert all(region.protected for region in without_optional.regions)


def test_normalized_defect_probabilities_are_available_to_the_router() -> None:
    provenance = _provenance("provider:defect-fixture")
    kinds_and_values = (
        (ObservationKind.CLIPPING_PROBABILITY, 0.11),
        (ObservationKind.RUMBLE_PROBABILITY, 0.72),
        (ObservationKind.HUM_PROBABILITY, 0.83),
        (ObservationKind.REVERB_PROBABILITY, 0.44),
        (ObservationKind.BANDWIDTH_LIMIT_PROBABILITY, 0.35),
    )
    observations = tuple(
        SemanticObservation(
            observation_id=f"observation:defect:{kind.value}",
            kind=kind,
            start_us=0,
            end_us=100_000,
            confidence=0.9,
            value=value,
            unit=ObservationUnit.PROBABILITY,
            provenance_ref=provenance.provenance_id,
        )
        for kind, value in kinds_and_values
    )
    semantic_map = fuse_semantic_map(
        semantic_map_id="semantic-map:defect-routing",
        source_asset_id="asset:defect-routing",
        duration_us=100_000,
        observations=observations,
        provenance_sources=(provenance,),
    )

    region = semantic_map.regions[0]
    assert region.clipping_probability == 0.11
    assert region.rumble_probability == 0.72
    assert region.hum_probability == 0.83
    assert region.reverb_probability == 0.44
    assert region.bandwidth_limit_probability == 0.35


def test_property_style_random_intervals_always_produce_ordered_half_open_full_coverage() -> None:
    generator = random.Random(22)
    provenance = _provenance("provider:property")
    for case in range(200):
        duration_us = generator.randint(1, 50) * 10_000
        hop_us = generator.randint(1, 10) * 10_000
        observations: list[SemanticObservation] = []
        for index in range(generator.randint(0, 20)):
            start_us = generator.randrange(0, duration_us)
            end_us = generator.randint(start_us + 1, duration_us)
            observations.append(
                SemanticObservation(
                    observation_id=f"observation:p{case}:{index}",
                    kind=ObservationKind.SPEECH_PROBABILITY,
                    start_us=start_us,
                    end_us=end_us,
                    confidence=generator.random(),
                    value=generator.random(),
                    unit=ObservationUnit.PROBABILITY,
                    provenance_ref=provenance.provenance_id,
                )
            )
        semantic_map = fuse_semantic_map(
            semantic_map_id=f"semantic-map:property{case}",
            source_asset_id="asset:source",
            duration_us=duration_us,
            provenance_sources=(provenance,),
            observations=reversed(observations),
            analysis_hop_us=hop_us,
        )
        assert semantic_map.regions[0].start_us == 0
        assert semantic_map.regions[-1].end_us == duration_us
        assert all(
            current.end_us == following.start_us and current.start_us < current.end_us
            for current, following in pairwise(semantic_map.regions)
        )


def test_legacy_protected_map_requires_and_supports_explicit_migration() -> None:
    legacy = {
        "schema_version": "1.0.0",
        "semantic_map_id": "semantic-map:legacy",
        "source_asset_id": "asset:source",
        "duration_us": 100_000,
        "regions": [
            {
                "schema_version": "1.0.0",
                "region_id": "semantic-region:legacy",
                "start_us": 0,
                "end_us": 100_000,
                "content_label": "unknown",
                "confidence": 0.0,
                "protected": True,
            }
        ],
    }
    migrated_payload = migrate_semantic_map_payload(legacy)
    migrated = SemanticMap.model_validate(migrated_payload)

    assert migrated.schema_version == "1.1.0"
    assert migrated.analysis_hop_us == migrated.duration_us
    assert migrated.regions[0].processing_eligibility is ProcessingEligibility.PROTECT
    assert "migrated" in " ".join(migrated.warnings).lower()


def _provenance(provider_id: str) -> EvidenceProvenance:
    return EvidenceProvenance(
        provenance_id=f"provenance:{provider_id.removeprefix('provider:')}",
        provider_id=provider_id,
        provider_version="test-1",
        adapter_id="adapter:test-v0",
        adapter_version="test-1",
        deterministic=True,
    )


def _vad_frame(start_us: int, end_us: int, *, speech: float, silence: float) -> VadFrame:
    return VadFrame(
        start_us=start_us,
        end_us=end_us,
        speech_probability=speech,
        silence_probability=silence,
        confidence=0.9,
        sample_peak_dbfs=-12.0,
        rms_dbfs=-24.0,
        attributes={"fixture": True},
    )
