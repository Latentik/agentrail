"""User-local configuration handling."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from agentrail.paths import resolve_paths


class AgentConfig(BaseModel):
    enabled: bool = True
    binary: str | None = None
    launch_args: list[str] = Field(default_factory=list)
    sessions_dir: str | None = None


class RedactionConfig(BaseModel):
    enabled: bool = True
    allow_dotenv: bool = False


class UserConfig(BaseModel):
    schema_version: str = "0.1"
    preferred_project_dir: str = ".handoff"
    agents: dict[str, AgentConfig] = Field(default_factory=dict)
    redaction: RedactionConfig = Field(default_factory=RedactionConfig)


DEFAULT_CONFIG = UserConfig(
    agents={
        "codex": AgentConfig(
            sessions_dir="~/.codex/sessions",
            binary="codex",
            launch_args=["{prompt_text}"],
        ),
        "gemini": AgentConfig(
            sessions_dir="~/.gemini/sessions",
            binary="gemini",
            launch_args=["{prompt_text}"],
        ),
        "claude": AgentConfig(
            sessions_dir="~/.claude/sessions",
            binary="claude",
            launch_args=["{prompt_text}"],
        ),
        "opencode": AgentConfig(
            sessions_dir="~/.opencode/sessions",
            binary="opencode",
            launch_args=["{prompt_text}"],
        ),
    }
)


def _config_path(base_dir: Path) -> Path:
    return base_dir / "config.json"


def load_or_create_user_config(home: Path | None = None) -> tuple[UserConfig, Path, bool]:
    resolved = resolve_paths(home=home)
    config_dir = resolved.user_config_dir
    legacy_dir = resolved.legacy_user_config_dir
    config_path = _config_path(config_dir)
    created = False

    if not config_path.exists() and _config_path(legacy_dir).exists():
        config_dir = legacy_dir
        config_path = _config_path(config_dir)

    if config_path.exists():
        raw = json.loads(config_path.read_text(encoding="utf-8"))
        config = DEFAULT_CONFIG.model_copy(deep=True)
        merged = config.model_dump()
        _deep_merge(merged, raw)
        return UserConfig.model_validate(merged), config_path, created

    created = True
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "agents").mkdir(exist_ok=True)
    (config_dir / "cache").mkdir(exist_ok=True)
    config = DEFAULT_CONFIG.model_copy(deep=True)
    config_path.write_text(json.dumps(config.model_dump(), indent=2) + "\n", encoding="utf-8")
    return config, config_path, created


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> None:
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
