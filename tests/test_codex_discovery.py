from pathlib import Path

from agentrail.adapters.codex import CodexAdapter
from agentrail.config import DEFAULT_CONFIG


def test_codex_discovery_prefers_repo_path_matches(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    match = sessions_dir / "recent.jsonl"
    match.write_text(f"user prompt for repo {repo_root}\nassistant summary\n", encoding="utf-8")
    other = sessions_dir / "older.log"
    other.write_text("assistant summary only\n", encoding="utf-8")

    config = DEFAULT_CONFIG.model_copy(deep=True)
    config.agents["codex"].sessions_dir = str(sessions_dir)
    adapter = CodexAdapter()

    discovery = adapter.discover_sources(repo_root, config)
    assert discovery is not None
    assert discovery.selected_session == match
    assert discovery.matched_sessions[0].confidence == "high"
