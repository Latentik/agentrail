from pathlib import Path

from agentrail.agent_registry import AgentRegistry
from agentrail.models import FileSnapshot, GitSnapshot, HandoffContext


def test_claude_adapter_registered():
    registry = AgentRegistry()
    assert "claude" in registry.supported_targets()
    adapter = registry.get_target("claude")
    assert adapter.name == "claude"


def test_opencode_adapter_registered():
    registry = AgentRegistry()
    assert "opencode" in registry.supported_targets()
    adapter = registry.get_target("opencode")
    assert adapter.name == "opencode"


def test_render_claude_prompt():
    registry = AgentRegistry()
    adapter = registry.get_target("claude")

    git = GitSnapshot(
        repo_root=Path("/tmp/repo"),
        branch="main",
        head="abc",
        status_short="",
        diff="",
        staged_diff="",
        untracked_files=[],
        recent_commits=[],
    )
    files = FileSnapshot([], [], 0, 0)
    context = HandoffContext(
        target="claude",
        project_name="test-project",
        git=git,
        files=files,
        summary_markdown="Summary",
        source_discoveries=[],
        selected_source=None,
        transcript_excerpt=None,
        diff_path=Path("/tmp/diff.patch"),
        staged_diff_path=Path("/tmp/staged.diff.patch"),
        handoff_dir=Path("/tmp/.handoff"),
        warnings=[],
    )

    artifact = adapter.render_prompt(context)
    assert artifact.target == "claude"
    assert "claude" in artifact.filename
    assert "You are continuing work" in artifact.content
