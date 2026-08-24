from __future__ import annotations

import json
from pathlib import Path

from ampersand_contracts import DependencyManifest, RecipeVersion

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]


def test_local_recipe_dependencies_have_machine_readable_admission_records() -> None:
    manifests = {
        manifest.dependency_manifest_id: manifest
        for path in sorted((REPOSITORY_ROOT / "infra/manifests/dependencies").glob("*.json"))
        for manifest in (DependencyManifest.model_validate_json(path.read_bytes()),)
    }
    recipe = RecipeVersion.model_validate_json(
        (REPOSITORY_ROOT / "services/media-worker/src/ampersand_engine/recipes/smart_spoken_word_v0.json").read_bytes()
    )
    assert set(recipe.dependency_manifest_ids) == set(manifests)
    assert all(manifest.admission_state.value == "lab_candidate" for manifest in manifests.values())
    assert not any(manifest.commercial_hosted_use_reviewed for manifest in manifests.values())


def test_wavesurfer_addition_has_a_separate_machine_readable_candidate_record() -> None:
    # This is the issue #11 WaveSurfer addition, not a comprehensive web-runtime allowlist.
    # Existing React/ReactDOM admission and notice coverage remains tracked in issue #12.
    manifests = {
        manifest.dependency_manifest_id: manifest
        for path in sorted((REPOSITORY_ROOT / "infra/manifests/web-dependencies").glob("*.json"))
        for manifest in (DependencyManifest.model_validate_json(path.read_bytes()),)
    }

    assert set(manifests) == {"dependency:wavesurfer-js"}
    wavesurfer = manifests["dependency:wavesurfer-js"]
    assert wavesurfer.dependency_version == "7.12.11"
    assert wavesurfer.code_license == "BSD-3-Clause"
    assert wavesurfer.admission_state.value == "production_candidate"
    assert wavesurfer.scope == "runtime"
    assert wavesurfer.artifact_sha256 == "a337bf2548e41a7211a39b0d16bd70c32eb07cf0ba243e4eb7190f371b2f92a0"
    assert wavesurfer.commercial_hosted_use_reviewed is True

    package = json.loads((REPOSITORY_ROOT / "package.json").read_text(encoding="utf-8"))
    package_lock = json.loads((REPOSITORY_ROOT / "package-lock.json").read_text(encoding="utf-8"))
    locked = package_lock["packages"]["node_modules/wavesurfer.js"]
    assert package["dependencies"]["wavesurfer.js"] == wavesurfer.dependency_version
    assert locked["version"] == wavesurfer.dependency_version
    assert locked["resolved"] == str(wavesurfer.source_url)
    assert locked["license"] == wavesurfer.code_license
    assert locked["integrity"] == (
        "sha512-Sx0yZIz7jRJ9J9p7UL+pl9y0UQBB6UN/XNo+R7Gy4tCR5xZI9jMyA0dnt1R8TMVSQ4LZ10SeB2HJYQ+dV2dPSA=="
    )

    license_text = (REPOSITORY_ROOT / "infra/licenses/wavesurfer.js-7.12.11-LICENSE.txt").read_text(encoding="utf-8")
    notice_text = (REPOSITORY_ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
    assert "BSD 3-Clause License" in license_text
    assert "Copyright (c) 2012-2023, katspaugh and contributors" in license_text
    assert "wavesurfer.js 7.12.11" in notice_text
