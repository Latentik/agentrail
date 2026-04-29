from pathlib import Path

from agentrail.models import FileSnapshot, GitSnapshot, HandoffContext
from agentrail.prompt.gemini import render_gemini_prompt


def test_gemini_prompt_contains_required_sections(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    git = GitSnapshot(
        repo_root=repo_root,
        branch="main",
        head="abc123",
        status_short=" M src/app.py",
        diff="diff --git a/src/app.py b/src/app.py\n+print('x')\n",
        staged_diff="",
        untracked_files=[],
        recent_commits=["abc123 init"],
    )
    files = FileSnapshot(
        changed_files=["src/app.py"],
        untracked_files=[],
        diff_bytes=20,
        staged_diff_bytes=0,
    )
    context = HandoffContext(
        target="gemini",
        project_name="repo",
        git=git,
        files=files,
        summary_markdown="# Handoff Summary\n",
        source_discoveries=[],
        selected_source=None,
        transcript_excerpt=None,
        diff_path=repo_root / ".handoff" / "diff.patch",
        staged_diff_path=repo_root / ".handoff" / "staged.diff.patch",
        handoff_dir=repo_root / ".handoff",
    )
    prompt = render_gemini_prompt(context)
    assert "Do not restart from scratch" in prompt
    assert "Project root:" in prompt
    assert ".handoff/diff.patch" in prompt
