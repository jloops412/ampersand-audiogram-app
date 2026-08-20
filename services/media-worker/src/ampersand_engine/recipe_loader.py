from __future__ import annotations

from importlib.resources import files

from ampersand_contracts import RecipeVersion

from .errors import EngineError

BUILT_IN_RECIPES = {"smart-spoken-word-v0": "smart_spoken_word_v0.json"}


def load_recipe(slug: str) -> RecipeVersion:
    filename = BUILT_IN_RECIPES.get(slug)
    if filename is None:
        supported = ", ".join(sorted(BUILT_IN_RECIPES))
        raise EngineError(f"Unknown recipe '{slug}'. Supported recipes: {supported}.")
    payload = files("ampersand_engine.recipes").joinpath(filename).read_text(encoding="utf-8")
    return RecipeVersion.model_validate_json(payload)
