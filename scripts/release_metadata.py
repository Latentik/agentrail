"""Release metadata helpers for GitHub Actions."""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

SEMVER_TAG = re.compile(r"^v(?P<version>\d+\.\d+\.\d+)$")
REPO_ROOT = Path(__file__).resolve().parents[1]



def main(argv: list[str] | None = None) -> int:
    args = argv or sys.argv[1:]
    if not args:
        raise SystemExit("usage: release_metadata.py <version|verify-tag> [args]")

    command = args[0]
    if command == "version":
        print(read_project_version())
        return 0
    if command == "verify-tag":
        if len(args) != 2:
            raise SystemExit("usage: release_metadata.py verify-tag <tag>")
        verify_tag(args[1])
        print(tag_to_version(args[1]))
        return 0
    raise SystemExit(f"unknown command: {command}")



def read_project_version() -> str:
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return str(pyproject["project"]["version"])



def tag_to_version(tag: str) -> str:
    match = SEMVER_TAG.match(tag)
    if not match:
        raise SystemExit(f"tag '{tag}' must match vMAJOR.MINOR.PATCH")
    return str(match.group("version"))



def verify_tag(tag: str) -> None:
    version = tag_to_version(tag)
    project_version = read_project_version()
    if version != project_version:
        raise SystemExit(
            f"tag version {version} does not match pyproject version {project_version}"
        )


if __name__ == "__main__":
    raise SystemExit(main())
