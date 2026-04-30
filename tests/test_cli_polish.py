"""Tests for CLI polish features (json, dry-run, config, clean)."""

import json
import subprocess
from pathlib import Path

from agentrail.prompt.common import _choose_diff_presentation
from typer.testing import CliRunner

from agentrail.cli import app

runner = CliRunner()


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def test_status_json(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    home = tmp_path / "home"
    home.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test User")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["status", "--json"], catch_exceptions=False, env={"HOME": str(home)})

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["repo_root"] == str(repo)
    assert "targets" in data
    assert "codex" in data["targets"]


def test_dry_run_init(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    home = tmp_path / "home"
    home.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test User")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.chdir(repo)

    result = runner.invoke(
        app, ["init", "--dry-run", "--skip-gitignore"], catch_exceptions=False, env={"HOME": str(home)}
    )

    assert result.exit_code == 0
    assert "Would initialize" in result.stdout
    assert not (repo / ".handoff").exists()


def test_clean_removes_handoff(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    home = tmp_path / "home"
    home.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test User")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.chdir(repo)

    runner.invoke(app, ["init"], catch_exceptions=False, env={"HOME": str(home)})
    assert (repo / ".handoff").exists()

    result = runner.invoke(app, ["clean"], catch_exceptions=False, env={"HOME": str(home)})
    assert result.exit_code == 0
    assert "Removed" in result.stdout
    assert not (repo / ".handoff").exists()


def test_clean_no_handoff(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    home = tmp_path / "home"
    home.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test User")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["clean"], catch_exceptions=False, env={"HOME": str(home)})
    assert result.exit_code == 0
    assert "No handoff artifacts" in result.stdout


def test_config_list(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    home = tmp_path / "home"
    home.mkdir()
    _git(repo, "init")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["config", "list"], catch_exceptions=False, env={"HOME": str(home)})
    assert result.exit_code == 0
    assert "Config path:" in result.stdout


def test_config_get_and_set(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    home = tmp_path / "home"
    home.mkdir()
    _git(repo, "init")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.chdir(repo)

    get_result = runner.invoke(
        app, ["config", "get", "preferred_project_dir"], catch_exceptions=False, env={"HOME": str(home)}
    )
    assert get_result.exit_code == 0
    assert ".handoff" in get_result.stdout

    set_result = runner.invoke(
        app,
        ["config", "set", "agents.claude.binary", "claude-code"],
        catch_exceptions=False,
        env={"HOME": str(home)},
    )
    assert set_result.exit_code == 0
    assert "Updated" in set_result.stdout

    get_after = runner.invoke(
        app, ["config", "get", "agents.claude.binary"], catch_exceptions=False, env={"HOME": str(home)}
    )
    assert get_after.exit_code == 0
    assert "claude-code" in get_after.stdout


def test_diff_presentation_small_diff_inlined() -> None:
    diff = "diff --git a/file.py b/file.py\n+foo\n"
    result = _choose_diff_presentation(diff, budget=64_000)
    assert "diff --git" in result


def test_diff_presentation_large_diff_file_list() -> None:
    lines = ["diff --git a/file{}.py b/file{}.py\n+foo\n".format(i, i) for i in range(5000)]
    diff = "\n".join(lines)
    result = _choose_diff_presentation(diff, budget=64_000)
    assert "Large diff truncated to file list" in result
    assert "file0.py" in result
