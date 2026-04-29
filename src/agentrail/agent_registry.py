"""Registry for source and target agent adapters."""

from __future__ import annotations

from agentrail.adapters.base import AgentAdapter
from agentrail.adapters.claude import ClaudeAdapter
from agentrail.adapters.codex import CodexAdapter
from agentrail.adapters.gemini import GeminiAdapter
from agentrail.adapters.opencode import OpenCodeAdapter
from agentrail.errors import UnsupportedTargetError


class AgentRegistry:
    def __init__(self) -> None:
        adapters: list[AgentAdapter] = [
            CodexAdapter(),
            GeminiAdapter(),
            ClaudeAdapter(),
            OpenCodeAdapter(),
        ]
        self._adapters = {adapter.name: adapter for adapter in adapters}

    def all_source_adapters(self) -> list[AgentAdapter]:
        return [
            adapter for adapter in self._adapters.values() if hasattr(adapter, "discover_sources")
        ]

    def get_target(self, name: str) -> AgentAdapter:
        adapter = self._adapters.get(name)
        if not adapter:
            supported = ", ".join(sorted(self._adapters))
            message = f"Unsupported target '{name}'. Supported targets: {supported}"
            raise UnsupportedTargetError(message)
        return adapter

    def supported_targets(self) -> list[str]:
        return sorted(self._adapters)
