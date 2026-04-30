"""Git capture via subprocess."""

from __future__ import annotations

import subprocess
from pathlib import Path

from agentrail.errors import GitCommandError, NotGitRepositoryError
from agentrail.models import FileSnapshot, GitSnapshot

MAX_CAPTURED_DIFF_BYTES = 200_000


def capture_git_state(
    cwd: Path | None = None, *, exclude_dotenv: bool = True
) -> tuple[GitSnapshot, FileSnapshot]:
    current = (cwd or Path.cwd()).resolve()
    repo_root = _run_git(current, ["rev-parse", "--show-toplevel"], allow_empty=False).strip()
    repo_path = Path(repo_root)

    branch = _run_git(repo_path, ["branch", "--show-current"], allow_empty=True).strip() or None
    head = _safe_git(repo_path, ["rev-parse", "HEAD"])
    status_short = _run_git(repo_path, ["status", "--short"], allow_empty=True)
    diff = _maybe_truncate_diff(
        _run_git(
            repo_path,
            _git_diff_args(["diff"], exclude_dotenv=exclude_dotenv),
            allow_empty=True,
        )
    )
    staged_diff = _maybe_truncate_diff(
        _run_git(
            repo_path,
            _git_diff_args(["diff", "--staged"], exclude_dotenv=exclude_dotenv),
            allow_empty=True,
        )
    )
    untracked_output = _run_git(
        repo_path,
        _git_ls_files_args(exclude_dotenv=exclude_dotenv),
        allow_empty=True,
    )
    recent_log = _safe_git(repo_path, ["log", "-n", "5", "--oneline"]) or ""
    untracked_files = [line for line in untracked_output.splitlines() if line.strip()]
    recent_commits = [line for line in recent_log.splitlines() if line.strip()]

    snapshot = GitSnapshot(
        repo_root=repo_path,
        branch=branch,
        head=head.strip() or None if head else None,
        status_short=status_short,
        diff=diff,
        staged_diff=staged_diff,
        untracked_files=untracked_files,
        recent_commits=recent_commits,
    )
    files = FileSnapshot(
        changed_files=snapshot.changed_files,
        untracked_files=untracked_files,
        diff_bytes=len(diff.encode("utf-8")),
        staged_diff_bytes=len(staged_diff.encode("utf-8")),
    )
    return snapshot, files


def diff_summary(diff_text: str, max_lines: int = 40) -> str:
    lines = diff_text.splitlines()
    if len(lines) <= max_lines:
        return diff_text.strip()
    return "\n".join(lines[:max_lines]).strip() + "\n... diff truncated ..."


def _maybe_truncate_diff(diff_text: str, max_bytes: int = MAX_CAPTURED_DIFF_BYTES) -> str:
    encoded = diff_text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return diff_text
    truncated = encoded[:max_bytes]
    last_newline = truncated.rfind(b"\n")
    if last_newline > 0:
        truncated = truncated[:last_newline]
    return truncated.decode("utf-8", errors="replace") + "\n\n... diff truncated due to size ...\n"


DOTENV_EXCLUDES = ["--", ".", ":(exclude).env", ":(exclude)*.env"]


def _git_diff_args(base: list[str], *, exclude_dotenv: bool) -> list[str]:
    if exclude_dotenv:
        return [*base, *DOTENV_EXCLUDES]
    return base


def _git_ls_files_args(*, exclude_dotenv: bool) -> list[str]:
    base = ["ls-files", "--others", "--exclude-standard"]
    if exclude_dotenv:
        return [*base, *DOTENV_EXCLUDES]
    return base


def _run_git(cwd: Path, args: list[str], allow_empty: bool) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if proc.returncode == 0:
        return proc.stdout
    stderr = proc.stderr.strip()
    if args[:2] == ["rev-parse", "--show-toplevel"]:
        raise NotGitRepositoryError("Current directory is not inside a Git repository.")
    if allow_empty:
        return ""
    raise GitCommandError(stderr or f"git {' '.join(args)} failed")


def _safe_git(cwd: Path, args: list[str]) -> str | None:
    proc = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if proc.returncode == 0:
        return proc.stdout
    return None
