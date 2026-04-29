"""Filesystem path helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

PROJECT_HANDOFF_DIRNAME = ".handoff"
LEGACY_USER_CONFIG_DIRNAME = ".handoff"
USER_CONFIG_DIRNAME = ".agentrail"


@dataclass(frozen=True, slots=True)
class ResolvedPaths:
    cwd: Path
    user_home: Path
    user_config_dir: Path
    legacy_user_config_dir: Path


@dataclass(frozen=True, slots=True)
class ProjectPaths:
    repo_root: Path
    handoff_dir: Path
    state_dir: Path


def resolve_paths(cwd: Path | None = None, home: Path | None = None) -> ResolvedPaths:
    current = (cwd or Path.cwd()).resolve()
    user_home = (home or Path.home()).resolve()
    return ResolvedPaths(
        cwd=current,
        user_home=user_home,
        user_config_dir=user_home / USER_CONFIG_DIRNAME,
        legacy_user_config_dir=user_home / LEGACY_USER_CONFIG_DIRNAME,
    )


def project_paths(repo_root: Path) -> ProjectPaths:
    handoff_dir = repo_root / PROJECT_HANDOFF_DIRNAME
    return ProjectPaths(
        repo_root=repo_root, handoff_dir=handoff_dir, state_dir=handoff_dir / "state"
    )
