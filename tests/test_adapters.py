"""Tests for adapters: render, launch, discover."""

from pathlib import Path

from agentrail.adapters.claude import ClaudeAdapter
from agentrail.adapters.codex import CodexAdapter
from agentrail.adapters.gemini import GeminiAdapter
from agentrail.adapters.opencode import OpenCodeAdapter
from agentrail.config import AgentConfig, UserConfig
from agentrail.models import FileSnapshot, GitSnapshot, HandoffContext


def _make_context(target: str, handoff_dir: Path | None = None) -> HandoffContext:
    git = GitSnapshot(
        repo_root=Path("/tmp/repo"), branch="main", head="abc",
        status_short="", diff="", staged_diff="", untracked_files=[], recent_commits=[],
    )
    files = FileSnapshot([], [], 0, 0)
    return HandoffContext(
        target=target, project_name="test", git=git, files=files,
        summary_markdown="Summary", source_discoveries=[], selected_source=None,
        transcript_excerpt=None,
        diff_path=Path("/tmp/diff.patch"), staged_diff_path=Path("/tmp/staged.diff.patch"),
        handoff_dir=handoff_dir or Path("/tmp/.handoff"), warnings=[],
    )


class TestAdapterRenderAndLaunch:
    def test_codex_render_and_discover_launch(self) -> None:
        a = CodexAdapter()
        ctx = _make_context("codex")
        p = a.render_prompt(ctx)
        assert p.target == "codex"
        assert "codex" in p.filename
        config = UserConfig(agents={"codex": AgentConfig(binary="codex")})
        spec = a.discover_launch(config)
        assert spec is not None
        assert spec.binary == "codex"

    def test_codex_discover_launch_disabled(self) -> None:
        a = CodexAdapter()
        config = UserConfig(agents={"codex": AgentConfig(enabled=False)})
        assert a.discover_launch(config) is None

    def test_claude_render_and_discover_launch(self) -> None:
        a = ClaudeAdapter()
        ctx = _make_context("claude")
        p = a.render_prompt(ctx)
        assert p.target == "claude"
        assert "claude" in p.filename
        config = UserConfig(agents={"claude": AgentConfig(binary="claude")})
        spec = a.discover_launch(config)
        assert spec is not None

    def test_claude_launch_no_spec(self) -> None:
        a = ClaudeAdapter()
        result = a.launch(Path("/dev/null"), "prompt", None)
        assert result.attempted is False
        assert "No launch configuration" in result.message

    def test_gemini_render_and_discover_launch(self) -> None:
        a = GeminiAdapter()
        ctx = _make_context("gemini")
        p = a.render_prompt(ctx)
        assert p.target == "gemini"
        assert "gemini" in p.filename
        config = UserConfig(agents={"gemini": AgentConfig(binary="gemini")})
        spec = a.discover_launch(config)
        assert spec is not None

    def test_opencode_render_and_discover_launch(self) -> None:
        a = OpenCodeAdapter()
        ctx = _make_context("opencode")
        p = a.render_prompt(ctx)
        assert p.target == "opencode"
        assert "opencode" in p.filename
        config = UserConfig(agents={"opencode": AgentConfig(binary="opencode")})
        spec = a.discover_launch(config)
        assert spec is not None


class TestAdapterSourceDiscovery:
    def test_codex_source_missing_dir(self, tmp_path: Path) -> None:
        a = CodexAdapter()
        config = UserConfig(agents={"codex": AgentConfig(sessions_dir=str(tmp_path / "missing"))})
        result = a.discover_sources(tmp_path, config)
        assert result is not None
        assert result.found is False
        assert result.warnings

    def test_claude_source_no_config(self, tmp_path: Path) -> None:
        a = ClaudeAdapter()
        config = UserConfig(agents={})
        assert a.discover_sources(tmp_path, config) is None

    def test_gemini_source_no_config(self, tmp_path: Path) -> None:
        a = GeminiAdapter()
        config = UserConfig(agents={})
        assert a.discover_sources(tmp_path, config) is None

    def test_opencode_source_no_config(self, tmp_path: Path) -> None:
        a = OpenCodeAdapter()
        config = UserConfig(agents={})
        assert a.discover_sources(tmp_path, config) is None
