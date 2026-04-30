"""Tests for prompt/common.py rendering."""

from pathlib import Path

from agentrail.models import FileSnapshot, GitSnapshot, HandoffContext, TranscriptExcerpt
from agentrail.prompt.common import (
    _choose_diff_presentation,
    _diff_file_summary,
    _read_project_file,
    render_common_sections,
)


def test_read_project_file_exists(tmp_path: Path) -> None:
    (tmp_path / "test.txt").write_text("hello", encoding="utf-8")
    result = _read_project_file(tmp_path, "test.txt")
    assert result == "hello"


def test_read_project_file_missing(tmp_path: Path) -> None:
    result = _read_project_file(tmp_path, "nonexistent.txt")
    assert result is None


def test_diff_file_summary_parses_filenames() -> None:
    diff = "diff --git a/file1.py b/file1.py\ndiff --git a/file2.py b/file2.py\n"
    result = _diff_file_summary(diff)
    assert "file1.py" in result
    assert "file2.py" in result
    assert "Large diff truncated to file list" in result


def test_diff_file_summary_empty() -> None:
    result = _diff_file_summary("")
    assert "Diff too large to inline" in result


def test_diff_presentation_small_returns_inline() -> None:
    diff = "diff --git a/a.py b/a.py\n+small change\n"
    result = _choose_diff_presentation(diff, budget=128_000)
    assert "diff --git" in result


def test_diff_presentation_large_returns_file_list() -> None:
    # A diff that exceeds 30% of budget (~1200 bytes per file * 200 = many tokens)
    lines = [f"diff --git a/file{i}.py b/file{i}.py\n+{'x' * 100}" for i in range(200)]
    big_diff = "\n".join(lines)
    result = _choose_diff_presentation(big_diff, budget=4_000)  # tiny budget so 30% is tiny
    assert "Large diff truncated to file list" in result


def test_render_common_sections_with_agents_md(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "AGENTS.md").write_text("# My custom instructions", encoding="utf-8")
    git = GitSnapshot(
        repo_root=repo, branch="main", head="abc", status_short="", diff="",
        staged_diff="", untracked_files=[], recent_commits=["abc123 initial"],
    )
    files = FileSnapshot([], [], 0, 0)
    context = HandoffContext(
        target="claude", project_name="test", git=git, files=files,
        summary_markdown="Summary", source_discoveries=[], selected_source=None,
        transcript_excerpt=None, diff_path=Path("/dev/null"), staged_diff_path=Path("/dev/null"),
        handoff_dir=repo / ".handoff", warnings=[], include_agents_md=True,
    )
    result = render_common_sections(context)
    assert "My custom instructions" in result


def test_render_common_sections_with_cursorrules(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".cursorrules").write_text("cursor rules content", encoding="utf-8")
    git = GitSnapshot(
        repo_root=repo, branch="main", head="abc", status_short="", diff="",
        staged_diff="", untracked_files=[], recent_commits=[],
    )
    files = FileSnapshot([], [], 0, 0)
    context = HandoffContext(
        target="claude", project_name="test", git=git, files=files,
        summary_markdown="Summary", source_discoveries=[], selected_source=None,
        transcript_excerpt=None, diff_path=Path("/dev/null"), staged_diff_path=Path("/dev/null"),
        handoff_dir=repo / ".handoff", warnings=[], include_cursorrules=True,
    )
    result = render_common_sections(context)
    assert "cursor rules content" in result


def test_render_common_sections_with_transcript_path(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    handoff = repo / ".handoff"
    handoff.mkdir()
    (handoff / "test-transcript.excerpt.md").write_text("transcript body", encoding="utf-8")
    git = GitSnapshot(
        repo_root=repo, branch="main", head="abc", status_short="", diff="",
        staged_diff="", untracked_files=[], recent_commits=[],
    )
    files = FileSnapshot([], [], 0, 0)
    excerpt = TranscriptExcerpt(
        adapter_name="test", artifact_name="test-transcript.excerpt.md",
        content="", commands=["cmd1"], errors=[], verification=[],
    )
    context = HandoffContext(
        target="claude", project_name="test", git=git, files=files,
        summary_markdown="Summary", source_discoveries=[], selected_source=None,
        transcript_excerpt=excerpt, diff_path=Path("/dev/null"), staged_diff_path=Path("/dev/null"),
        handoff_dir=handoff, warnings=[],
    )
    result = render_common_sections(context)
    assert "test-transcript.excerpt.md" in result
    assert "cmd1" in result
