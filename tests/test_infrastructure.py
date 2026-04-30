"""Tests for handoff_writer, git_state, and error edge cases."""

from pathlib import Path

from agentrail.errors import NotGitRepositoryError, UnsupportedTargetError
from agentrail.git_state import _maybe_truncate_diff
from agentrail.handoff_schema import HandoffDocument
from agentrail.handoff_writer import _existing_created_at, _simple_list_doc


class TestGitState:
    def test_truncate_diff_under_max(self) -> None:
        text = "short text"
        result = _maybe_truncate_diff(text, max_bytes=1000)
        assert result == text

    def test_truncate_diff_over_max(self) -> None:
        text = "a" * 500
        result = _maybe_truncate_diff(text, max_bytes=100)
        assert "diff truncated due to size" in result
        assert len(result) < len(text)

    def test_not_git_repo(self, tmp_path: Path) -> None:
        try:
            from agentrail.git_state import capture_git_state
            capture_git_state(tmp_path)
            raise AssertionError("expected error")
        except NotGitRepositoryError:
            pass


class TestHandoffWriter:
    def test_simple_list_doc_empty(self) -> None:
        result = _simple_list_doc("Title", [])
        assert "# Title" in result
        assert "- None" in result

    def test_simple_list_doc_with_items(self) -> None:
        result = _simple_list_doc("Title", ["a", "b"])
        assert "- a" in result
        assert "- b" in result

    def test_existing_created_at_no_file(self, tmp_path: Path) -> None:
        assert _existing_created_at(tmp_path / "nonexistent.json") is None

    def test_existing_created_at_invalid_json(self, tmp_path: Path) -> None:
        f = tmp_path / "handoff.json"
        f.write_text("not json", encoding="utf-8")
        assert _existing_created_at(f) is None

    def test_existing_created_at_valid(self, tmp_path: Path) -> None:
        import json
        f = tmp_path / "handoff.json"
        f.write_text(json.dumps({"created_at": "2024-01-01T00:00:00"}), encoding="utf-8")
        assert _existing_created_at(f) == "2024-01-01T00:00:00"


class TestErrors:
    def test_unsupported_target(self) -> None:
        from agentrail.agent_registry import AgentRegistry
        registry = AgentRegistry()
        try:
            registry.get_target("nonexistent")
            raise AssertionError("expected error")
        except UnsupportedTargetError as e:
            assert "nonexistent" in str(e)


class TestHandoffSchema:
    def test_handoff_document_defaults(self) -> None:
        doc = HandoffDocument(
            created_at="now", updated_at="now",
            project={"root": "/tmp", "name": "x", "dirty": False},
            artifacts={"diff": "d", "staged_diff": "s", "summary": "sum"},
        )
        assert doc.schema_version == "0.1"
        assert doc.warnings == []
        assert doc.source_agents == []
