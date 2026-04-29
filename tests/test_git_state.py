import subprocess
from pathlib import Path

import pytest

from agentrail.errors import NotGitRepositoryError
from agentrail.git_state import capture_git_state


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def test_capture_git_state_in_repo(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test User")
    (repo / "file.txt").write_text("one\n", encoding="utf-8")
    _git(repo, "add", "file.txt")
    _git(repo, "commit", "-m", "init")
    (repo / "file.txt").write_text("two\n", encoding="utf-8")

    git, files = capture_git_state(repo)
    assert git.repo_root == repo.resolve()
    assert git.head
    assert "file.txt" in files.changed_files


def test_capture_git_state_outside_repo_raises(tmp_path: Path) -> None:
    with pytest.raises(NotGitRepositoryError):
        capture_git_state(tmp_path)
