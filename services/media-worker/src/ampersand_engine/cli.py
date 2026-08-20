from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from ampersand_contracts import GainEnvelope, ProductionSettings, canonical_json_bytes, read_manifest
from ampersand_contracts.schema_export import EXPORTED_MODELS, export_json_schemas
from pydantic import ValidationError

from .errors import EngineError
from .ffmpeg import FFmpegTools, probe_media
from .gain_renderer import render_leveler_candidate
from .hashing import sha256_file, stable_id
from .pipeline import process_source
from .recipe_loader import BUILT_IN_RECIPES
from .settings import SettingsSource


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "process":
            settings = read_manifest(args.settings, ProductionSettings) if args.settings is not None else None
            settings_source = cast(
                SettingsSource,
                args.settings_source or ("run_override" if settings is not None else "recipe"),
            )
            result = process_source(
                args.source,
                args.output,
                recipe_slug=args.recipe,
                title=args.title,
                settings=settings,
                intent=args.intent,
                template_version_id=args.template_version_id,
                settings_source=settings_source,
                progress=lambda message: print(f"ampersand: {message}", file=sys.stderr),
            )
            print(
                json.dumps(
                    {
                        "output_directory": str(result.output_directory),
                        "production_id": result.production_id,
                        "run_id": result.run_id,
                        "source_sha256": result.source_sha256,
                        "wav_sha256": result.wav_sha256,
                        "mp3_sha256": result.mp3_sha256,
                    },
                    sort_keys=True,
                )
            )
            return 0
        if args.command == "probe":
            source = args.source.expanduser().resolve(strict=True)
            source_sha = sha256_file(source)
            source_asset_id = stable_id("asset", source_sha)
            probe = probe_media(
                source,
                source_asset_id=source_asset_id,
                probe_id=stable_id("probe", source_sha),
                tools=FFmpegTools.discover(),
            )
            sys.stdout.buffer.write(canonical_json_bytes(probe) + b"\n")
            return 0
        if args.command == "render-leveler-candidate":
            envelope = read_manifest(args.envelope, GainEnvelope)
            render_result = render_leveler_candidate(args.source, envelope, args.output)
            print(
                json.dumps(
                    {
                        "candidate_path": str(render_result.candidate_path),
                        "candidate_sha256": render_result.manifest.candidate_sha256,
                        "gain_render_manifest_id": render_result.manifest.gain_render_manifest_id,
                        "real_time_factor": render_result.runtime.real_time_factor,
                        "status": "evaluation_only",
                    },
                    sort_keys=True,
                )
            )
            return 0
        if args.command == "schemas":
            written = export_json_schemas(args.output)
            print(json.dumps({"count": len(written), "output": str(args.output)}, sort_keys=True))
            return 0
        if args.command == "validate-manifest":
            model_types = {model_type.__name__: model_type for model_type in EXPORTED_MODELS}
            model_type = model_types[args.contract]
            model_type.model_validate_json(args.manifest.read_bytes())
            print(json.dumps({"contract": args.contract, "status": "valid"}, sort_keys=True))
            return 0
        if args.command == "list-recipes":
            print("\n".join(sorted(BUILT_IN_RECIPES)))
            return 0
    except (EngineError, FileNotFoundError, OSError, ValidationError, ValueError) as error:
        print(f"ampersand: error: {error}", file=sys.stderr)
        return 2
    parser.error("a command is required")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ampersand-engine",
        description="Independent, local-only Ampersand V2 media-engine baseline.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    process = subcommands.add_parser("process", help="Run the deterministic baseline graph for one local source.")
    process.add_argument("source", type=Path, help="Local rights-cleared audio source.")
    process.add_argument(
        "--output",
        type=Path,
        required=True,
        help="New directory for derived artifacts and manifests.",
    )
    process.add_argument("--recipe", default="smart-spoken-word-v0", choices=sorted(BUILT_IN_RECIPES))
    process.add_argument("--title", default=None, help="Optional production title (does not affect source identity).")
    process.add_argument(
        "--settings",
        type=Path,
        default=None,
        help="Optional complete ProductionSettings JSON; the resolved snapshot is stored with the run.",
    )
    process.add_argument(
        "--intent",
        choices=("podcast", "natural_voice", "broadcast", "social_voice"),
        default="podcast",
        help="Quick-start intent recorded in the resolved settings snapshot.",
    )
    process.add_argument(
        "--template-version-id",
        default=None,
        help="Immutable template version identity when --settings-source=template.",
    )
    process.add_argument(
        "--settings-source",
        choices=("recipe", "template", "run_override"),
        default=None,
        help="Provenance for the complete settings value (inferred when omitted).",
    )

    probe = subcommands.add_parser("probe", help="Validate and print normalized media metadata as canonical JSON.")
    probe.add_argument("source", type=Path)

    render = subcommands.add_parser(
        "render-leveler-candidate",
        help="Apply a gain envelope to a new evaluation-only WAV; the production master remains unchanged.",
    )
    render.add_argument("source", type=Path, help="Local rights-cleared source used to build the envelope.")
    render.add_argument("envelope", type=Path, help="Validated GainEnvelope JSON manifest.")
    render.add_argument("--output", type=Path, required=True, help="New evaluation output directory.")

    schemas = subcommands.add_parser("schemas", help="Export provider-neutral JSON Schemas for other runtimes.")
    schemas.add_argument("--output", type=Path, required=True)

    validate = subcommands.add_parser("validate-manifest", help="Validate one JSON manifest against a contract.")
    validate.add_argument("contract", choices=sorted(model_type.__name__ for model_type in EXPORTED_MODELS))
    validate.add_argument("manifest", type=Path)

    subcommands.add_parser("list-recipes", help="List immutable built-in recipe slugs.")
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
