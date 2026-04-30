"""Tests for security helpers."""

from pathlib import Path

from agentrail.redaction import redact_text
from agentrail.security import append_gitignore, check_gitignore


class TestCheckGitignore:
    def test_missing_gitignore(self, tmp_path: Path) -> None:
        ignored, warnings = check_gitignore(tmp_path)
        assert ignored is False
        assert any("missing_gitignore" in w.code for w in warnings)

    def test_gitignore_with_handoff(self, tmp_path: Path) -> None:
        (tmp_path / ".gitignore").write_text(".handoff/\n", encoding="utf-8")
        ignored, warnings = check_gitignore(tmp_path)
        assert ignored is True
        assert warnings == []

    def test_gitignore_without_handoff(self, tmp_path: Path) -> None:
        (tmp_path / ".gitignore").write_text("*.pyc\n", encoding="utf-8")
        ignored, warnings = check_gitignore(tmp_path)
        assert ignored is False
        assert any("handoff_not_ignored" in w.code for w in warnings)


class TestAppendGitignore:
    def test_creates_gitignore(self, tmp_path: Path) -> None:
        append_gitignore(tmp_path)
        text = (tmp_path / ".gitignore").read_text(encoding="utf-8")
        assert ".handoff/" in text

    def test_appends_to_existing(self, tmp_path: Path) -> None:
        (tmp_path / ".gitignore").write_text("*.pyc\n", encoding="utf-8")
        append_gitignore(tmp_path)
        text = (tmp_path / ".gitignore").read_text(encoding="utf-8")
        assert "*.pyc" in text
        assert ".handoff/" in text


class TestRedaction:
    def test_redacts_aws_key(self) -> None:
        text = "AKIAIOSFODNN7EXAMPLE"
        result = redact_text(text)
        assert "[REDACTED]" in result

    def test_redacts_github_token(self) -> None:
        text = "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        result = redact_text(text)
        assert "[REDACTED]" in result

    def test_redacts_bearer_token(self) -> None:
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        result = redact_text(text)
        assert "[REDACTED]" in result

    def test_leaves_normal_text(self) -> None:
        text = "hello world, this is a normal sentence."
        result = redact_text(text)
        assert result == text
