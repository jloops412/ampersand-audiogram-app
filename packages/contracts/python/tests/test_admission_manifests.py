from __future__ import annotations

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
