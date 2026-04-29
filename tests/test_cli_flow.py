import json
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from agentrail.cli import app

runner = CliRunner()


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def test_init_creates_handoff_tree(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    home = tmp_path / "home"
    home.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test User")
    (repo / "app.py").write_text("print('hi')\n", encoding="utf-8")
    _git(repo, "add", "app.py")
    _git(repo, "commit", "-m", "init")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["init"], catch_exceptions=False, env={"HOME": str(home)})

    assert result.exit_code == 0
    assert (repo / ".handoff" / "handoff.json").exists()
    assert (repo / ".handoff" / "summary.md").exists()
    assert (repo / ".handoff" / "commands.md").exists()
    assert (home / ".agentrail" / "config.json").exists()


def test_status_output(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    home = tmp_path / "home"
    home.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test User")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.chdir(repo)

    result = runner.invoke(app, ["status"], catch_exceptions=False, env={"HOME": str(home)})

    assert result.exit_code == 0
    assert "Project Status" in result.stdout
    assert "Branch:" in result.stdout
    assert "claude: not configured" in result.stdout
    assert "opencode: not configured" in result.stdout


def test_continue_claude_print(tmp_path: Path, monkeypatch) -> None:
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
        app,
        ["continue", "claude", "--print", "--no-launch"],
        catch_exceptions=False,
        env={"HOME": str(home)},
    )

    assert result.exit_code == 0
    assert "claude" in result.stdout
    assert "## Current State" in result.stdout
