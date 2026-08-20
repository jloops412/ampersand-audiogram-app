from __future__ import annotations

import json
import re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from ampersand_contracts import ListeningSessionManifest, read_manifest
from pydantic import ValidationError

from .errors import ListeningLabError
from .store import close_session, load_report, session_status, submit_score

MAX_REQUEST_BYTES = 65_536
_RANGE = re.compile(r"^bytes=(\d*)-(\d*)$")


def build_server(workspace: Path, *, host: str = "127.0.0.1", port: int = 8765) -> HTTPServer:
    if host not in {"127.0.0.1", "localhost"}:
        raise ListeningLabError("The listening server may bind only to localhost.")
    if not 0 <= port <= 65_535:
        raise ValueError("port must be within [0, 65535]")
    root = workspace.expanduser().resolve(strict=True)
    session = read_manifest(root / "public/session.json", ListeningSessionManifest)
    allowed_audio = {
        "/" + option.audio_relative_path: root / "public" / option.audio_relative_path
        for trial in session.trials
        for option in trial.options
    }

    class ListeningHandler(BaseHTTPRequestHandler):
        server_version = "AmpersandListeningLab/0.1"

        def do_GET(self) -> None:
            path = unquote(urlsplit(self.path).path)
            if path == "/":
                self._send_file(root / "public/index.html", "text/html; charset=utf-8")
                return
            if path == "/session.json":
                self._send_file(root / "public/session.json", "application/json; charset=utf-8")
                return
            if path in allowed_audio:
                self._send_audio(allowed_audio[path])
                return
            if path == "/api/status":
                self._send_json(HTTPStatus.OK, session_status(root))
                return
            if path == "/api/reveal":
                try:
                    report = load_report(root)
                except ListeningLabError as error:
                    self._send_json(HTTPStatus.CONFLICT, {"error": str(error)})
                    return
                self._send_json(HTTPStatus.OK, report.model_dump(mode="json", exclude_none=True))
                return
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found."})

        def do_POST(self) -> None:
            path = unquote(urlsplit(self.path).path)
            try:
                if path == "/api/scores":
                    payload = self._read_json()
                    score = submit_score(root, payload)
                    self._send_json(
                        HTTPStatus.CREATED,
                        {"score_id": score.score_id, "submission_sequence": score.submission_sequence},
                    )
                    return
                if path == "/api/close":
                    report = close_session(root)
                    self._send_json(HTTPStatus.OK, {"report_id": report.listening_report_id, "state": "closed"})
                    return
            except ListeningLabError as error:
                self._send_json(HTTPStatus.CONFLICT, {"error": str(error)})
                return
            except ValidationError:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Score failed contract validation."})
                return
            except (json.JSONDecodeError, ValueError):
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Request body is not valid."})
                return
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found."})

        def _read_json(self) -> dict[str, Any]:
            raw_length = self.headers.get("Content-Length")
            if raw_length is None:
                raise ValueError("Content-Length is required")
            length = int(raw_length)
            if length < 0 or length > MAX_REQUEST_BYTES:
                raise ValueError("request body is too large")
            payload: Any = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError("request body must be an object")
            return payload

        def _send_json(self, status: HTTPStatus, payload: Any) -> None:
            encoded = json.dumps(payload, allow_nan=False, ensure_ascii=False, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self._security_headers()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def _send_file(self, path: Path, content_type: str) -> None:
            payload = path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self._security_headers()
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def _send_audio(self, path: Path) -> None:
            size = path.stat().st_size
            range_header = self.headers.get("Range")
            if not range_header:
                start, end, status = 0, size - 1, HTTPStatus.OK
            else:
                parsed = _parse_range(range_header, size)
                if parsed is None:
                    self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                    self._security_headers()
                    self.send_header("Content-Range", f"bytes */{size}")
                    self.end_headers()
                    return
                start, end = parsed
                status = HTTPStatus.PARTIAL_CONTENT
            length = end - start + 1
            self.send_response(status)
            self._security_headers()
            self.send_header("Content-Type", "audio/wav")
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(length))
            if status is HTTPStatus.PARTIAL_CONTENT:
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.end_headers()
            with path.open("rb") as source:
                source.seek(start)
                remaining = length
                while remaining:
                    chunk = source.read(min(64 * 1024, remaining))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    remaining -= len(chunk)

        def _security_headers(self) -> None:
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Cross-Origin-Resource-Policy", "same-origin")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; media-src 'self'; connect-src 'self'; "
                "script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
                "img-src 'none'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'",
            )

        def log_message(self, _format: str, *_args: object) -> None:
            return

    return HTTPServer((host, port), ListeningHandler)


def _parse_range(value: str, size: int) -> tuple[int, int] | None:
    match = _RANGE.fullmatch(value.strip())
    if match is None or size <= 0:
        return None
    start_text, end_text = match.groups()
    if not start_text and not end_text:
        return None
    if not start_text:
        suffix = int(end_text)
        if suffix <= 0:
            return None
        start = max(0, size - suffix)
        end = size - 1
    else:
        start = int(start_text)
        end = int(end_text) if end_text else size - 1
    if start < 0 or start >= size or end < start:
        return None
    return start, min(end, size - 1)
