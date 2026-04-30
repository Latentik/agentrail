"""Tests for generic file-based source discovery and excerpt extraction."""

from pathlib import Path

from agentrail.adapters._file_source import (
    DEFAULT_CONTENT_MARKERS,
    discover_file_sources,
    extract_file_excerpt,
)
from agentrail.adapters.claude import ClaudeAdapter
from agentrail.adapters.gemini import GeminiAdapter
from agentrail.adapters.opencode import OpenCodeAdapter
from agentrail.config import AgentConfig, UserConfig


class TestDiscoverFileSources:
    def test_missing_sessions_dir_returns_warning(self, tmp_path: Path) -> None:
        result = discover_file_sources("test", str(tmp_path / "missing"), tmp_path)
        assert result is not None
        assert result.found is False
        assert result.warnings
        assert "does not exist" in result.warnings[0].message.lower()

    def test_no_files_returns_empty(self, tmp_path: Path) -> None:
        sessions = tmp_path / "sessions"
        sessions.mkdir()
        result = discover_file_sources("test", str(sessions), tmp_path)
        assert result is not None
        assert result.found is False
        assert result.matched_sessions == []

    def test_high_confidence_repo_root_match(self, tmp_path: Path) -> None:
        sessions = tmp_path / "sessions"
        sessions.mkdir()
        session_file = sessions / "session.log"
        session_file.write_text(f"worked in {tmp_path}\n", encoding="utf-8")
        result = discover_file_sources("test", str(sessions), tmp_path)
        assert result is not None
        assert result.found is True
        assert result.matched_sessions[0].confidence == "high"

    def test_low_confidence_marker_match(self, tmp_path: Path) -> None:
        sessions = tmp_path / "sessions"
        sessions.mkdir()
        session_file = sessions / "session.md"
        session_file.write_text("assistant said hello\n", encoding="utf-8")
        result = discover_file_sources(
            "test", str(sessions), tmp_path, content_markers=("assistant",)
        )
        assert result is not None
        assert result.found is True
        assert result.matched_sessions[0].confidence == "low"

    def test_default_markers_per_adapter(self) -> None:
        for name in ("codex", "claude", "gemini", "opencode"):
            assert name in DEFAULT_CONTENT_MARKERS
            assert "assistant" in DEFAULT_CONTENT_MARKERS[name]


class TestExtractFileExcerpt:
    def test_no_selected_session_returns_none(self) -> None:
        from agentrail.models import SourceDiscoveryResult

        discovery = SourceDiscoveryResult(
            adapter_name="test", found=False, source_dir=None, selected_session=None
        )
        assert extract_file_excerpt("test", "test.md", discovery) is None

    def test_reads_and_redacts(self, tmp_path: Path) -> None:
        from agentrail.models import SourceDiscoveryResult, SourceMatch

        session_file = tmp_path / "session.log"
        session_file.write_text("user asked something\ncommand: ls\n", encoding="utf-8")
        discovery = SourceDiscoveryResult(
            adapter_name="test",
            found=True,
            source_dir=tmp_path,
            selected_session=session_file,
            matched_sessions=[
                SourceMatch(
                    adapter_name="test",
                    path=session_file,
                    mtime="2024-01-01T00:00:00",
                    confidence="high",
                    reason="test",
                )
            ],
        )
        excerpt = extract_file_excerpt("test", "test.md", discovery)
        assert excerpt is not None
        assert "user asked something" in excerpt.content
        assert any("command" in cmd for cmd in excerpt.commands)

    def test_oserror_handled(self, tmp_path: Path) -> None:
        from agentrail.models import SourceDiscoveryResult, SourceMatch

        session_file = tmp_path / "session.log"
        session_file.write_text("data", encoding="utf-8")
        discovery = SourceDiscoveryResult(
            adapter_name="test",
            found=True,
            source_dir=tmp_path,
            selected_session=session_file,
            matched_sessions=[
                SourceMatch(
                    adapter_name="test",
                    path=session_file,
                    mtime="2024-01-01T00:00:00",
                    confidence="high",
                    reason="test",
                )
            ],
        )
        session_file.chmod(0o000)
        try:
            excerpt = extract_file_excerpt("test", "test.md", discovery)
            assert excerpt is not None
            assert "Failed to read transcript" in excerpt.content
        finally:
            session_file.chmod(0o644)


class TestAdapterDiscoveryIntegration:
    def test_claude_adapter_discovery(self, tmp_path: Path) -> None:
        sessions = tmp_path / ".claude" / "sessions"
        sessions.mkdir(parents=True)
        (sessions / "session.md").write_text("claude assistant output\n", encoding="utf-8")
        config = UserConfig(
            agents={"claude": AgentConfig(sessions_dir=str(sessions))}
        )
        adapter = ClaudeAdapter()
        result = adapter.discover_sources(tmp_path, config)
        assert result is not None
        assert result.found is True
        assert result.adapter_name == "claude"

    def test_gemini_adapter_discovery(self, tmp_path: Path) -> None:
        sessions = tmp_path / ".gemini" / "sessions"
        sessions.mkdir(parents=True)
        (sessions / "session.log").write_text("gemini user prompt\n", encoding="utf-8")
        config = UserConfig(
            agents={"gemini": AgentConfig(sessions_dir=str(sessions))}
        )
        adapter = GeminiAdapter()
        result = adapter.discover_sources(tmp_path, config)
        assert result is not None
        assert result.found is True
        assert result.adapter_name == "gemini"

    def test_opencode_adapter_discovery(self, tmp_path: Path) -> None:
        sessions = tmp_path / ".opencode" / "sessions"
        sessions.mkdir(parents=True)
        path = sessions / "session.jsonl"
        path.write_text('{"content": "opencode assistant"}\n', encoding="utf-8")
        config = UserConfig(
            agents={"opencode": AgentConfig(sessions_dir=str(sessions))}
        )
        adapter = OpenCodeAdapter()
        result = adapter.discover_sources(tmp_path, config)
        assert result is not None
        assert result.found is True
        assert result.adapter_name == "opencode"

    def test_disabled_agent_returns_none(self, tmp_path: Path) -> None:
        config = UserConfig(
            agents={"claude": AgentConfig(enabled=False, sessions_dir="~/.claude/sessions")}
        )
        adapter = ClaudeAdapter()
        assert adapter.discover_sources(tmp_path, config) is None

    def test_missing_config_returns_none(self, tmp_path: Path) -> None:
        config = UserConfig(agents={})
        adapter = ClaudeAdapter()
        assert adapter.discover_sources(tmp_path, config) is None
