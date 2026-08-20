from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from ampersand_contracts import canonical_json_bytes
from ampersand_engine.errors import EngineError
from pydantic import ValidationError

from .errors import ListeningLabError
from .prepare import prepare_experiment
from .server import build_server
from .store import close_session, load_report, session_status, submit_score


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            prepared = prepare_experiment(args.manifest, args.output)
            print(
                json.dumps(
                    {
                        "output": str(args.output),
                        "session_id": prepared.session.session_id,
                        "trial_count": len(prepared.session.trials),
                    },
                    sort_keys=True,
                )
            )
            return 0
        if args.command == "serve":
            server = build_server(args.workspace, host=args.host, port=args.port)
            host, port = server.server_name, server.server_port
            print(f"Ampersand listening lab: http://{host}:{port}", file=sys.stderr)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
            finally:
                server.server_close()
            return 0
        if args.command == "submit":
            payload: Any = json.loads(args.score.read_bytes())
            if not isinstance(payload, dict):
                raise ValueError("score submission must be a JSON object")
            score = submit_score(args.workspace, payload)
            print(json.dumps({"score_id": score.score_id, "sequence": score.submission_sequence}, sort_keys=True))
            return 0
        if args.command == "close":
            report = close_session(args.workspace)
            print(
                json.dumps(
                    {
                        "report_id": report.listening_report_id,
                        "score_count": report.score_count,
                        "status": report.human_approval_status,
                    },
                    sort_keys=True,
                )
            )
            return 0
        if args.command == "status":
            print(json.dumps(session_status(args.workspace), sort_keys=True))
            return 0
        if args.command == "report":
            sys.stdout.buffer.write(canonical_json_bytes(load_report(args.workspace)) + b"\n")
            return 0
    except (
        EngineError,
        ListeningLabError,
        FileNotFoundError,
        OSError,
        ValidationError,
        ValueError,
        json.JSONDecodeError,
    ) as error:
        message = str(error) if isinstance(error, ListeningLabError) else "The listening command failed validation."
        print(f"ampersand-listening: error: {message}", file=sys.stderr)
        return 2
    parser.error("a command is required")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ampersand-listening",
        description="Local-only blinded listening and regression harness for rights-cleared Ampersand experiments.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    prepare = commands.add_parser("prepare", help="Create loudness-matched opaque listening copies.")
    prepare.add_argument("manifest", type=Path)
    prepare.add_argument("--output", type=Path, required=True)

    serve = commands.add_parser("serve", help="Serve one prepared workspace on localhost.")
    serve.add_argument("workspace", type=Path)
    serve.add_argument("--host", default="127.0.0.1", choices=("127.0.0.1", "localhost"))
    serve.add_argument("--port", type=int, default=8765)

    submit = commands.add_parser("submit", help="Submit a validated score JSON without the web UI.")
    submit.add_argument("workspace", type=Path)
    submit.add_argument("score", type=Path)

    close = commands.add_parser("close", help="Close scoring and create the identity-revealed report.")
    close.add_argument("workspace", type=Path)

    status = commands.add_parser("status", help="Print session state without revealing identities.")
    status.add_argument("workspace", type=Path)

    report = commands.add_parser("report", help="Print the report after session close.")
    report.add_argument("workspace", type=Path)
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
