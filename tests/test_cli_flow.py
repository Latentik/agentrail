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


def test_continue_gemini_print_without_binary(tmp_path: Path, monkeypatch) -> None:
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

    result = runner.invoke(
        app,
        ["continue", "gemini", "--print", "--no-launch"],
        catch_exceptions=False,
        env={"HOME": str(home)},
    )

    assert result.exit_code == 0
    assert "Do not restart from scratch" in result.stdout
    handoff = json.loads((repo / ".handoff" / "handoff.json").read_text(encoding="utf-8"))
    assert handoff["artifacts"]["prompts"]["gemini"].endswith("next-prompt.gemini.md")
