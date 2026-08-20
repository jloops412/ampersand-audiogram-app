from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V2_ROOTS = ("apps", "services", "packages", "lab", "infra")
TEXT_SUFFIXES = {".json", ".md", ".py", ".toml", ".ts", ".tsx", ".yaml", ".yml"}
FORBIDDEN = (
    re.compile(r"auphonic", re.IGNORECASE),
    re.compile(r"backend/server\.js"),
    re.compile(r"src/services/auphonicService\.ts"),
    re.compile(r"src/services/videoService\.ts"),
)


def main() -> int:
    violations: list[str] = []
    for root_name in V2_ROOTS:
        root = ROOT / root_name
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in TEXT_SUFFIXES or "__pycache__" in path.parts:
                continue
            text = path.read_text(encoding="utf-8")
            for pattern in FORBIDDEN:
                if pattern.search(text):
                    violations.append(f"{path.relative_to(ROOT)} matches forbidden V2 boundary {pattern.pattern!r}")
    if violations:
        print("\n".join(violations), file=sys.stderr)
        return 1
    print("V2 boundary check passed: no legacy proxy, renderer, or service references.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
