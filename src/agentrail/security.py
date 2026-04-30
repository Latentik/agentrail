"""Security helpers for handoff artifact safety."""

from __future__ import annotations

from pathlib import Path

from agentrail.models import WarningRecord


def check_gitignore(repo_root: Path, handoff_dir: str = ".handoff") -> tuple[bool, list[WarningRecord]]:
    """Return (is_ignored, warnings)."""
    gitignore = repo_root / ".gitignore"
    if not gitignore.exists():
        return False, [
            WarningRecord(
                code="security.missing_gitignore",
                message="No .gitignore found. Handoff artifacts may be committed by accident.",
            )
        ]

    text = gitignore.read_text(encoding="utf-8")
    lines = {line.strip() for line in text.splitlines()}
    candidates = {handoff_dir, f"{handoff_dir}/", f"/{handoff_dir}/", f"/{handoff_dir}"}
    if any(c in lines for c in candidates):
        return True, []

    return False, [
        WarningRecord(
            code="security.handoff_not_ignored",
            message=f"{handoff_dir}/ is not in .gitignore. Risk of committing handoff artifacts.",
        )
    ]


def append_gitignore(repo_root: Path, handoff_dir: str = ".handoff") -> None:
    gitignore = repo_root / ".gitignore"
    entry = f"\n{handoff_dir}/\n"
    if gitignore.exists():
        text = gitignore.read_text(encoding="utf-8")
        if not text.endswith("\n"):
            entry = f"\n{entry}"
        gitignore.write_text(text + entry, encoding="utf-8")
    else:
        gitignore.write_text(f"{handoff_dir}/\n", encoding="utf-8")
