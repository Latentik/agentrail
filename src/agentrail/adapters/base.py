"""Base interfaces for agent adapters."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from agentrail.config import UserConfig
from agentrail.models import (
    HandoffContext,
    LaunchResult,
    LaunchSpec,
    SourceDiscoveryResult,
    TranscriptExcerpt,
)


@dataclass(frozen=True, slots=True)
class PromptArtifact:
    target: str
    filename: str
    content: str


class AgentAdapter(Protocol):
    name: str

    def discover_sources(
        self, repo_root: Path, config: UserConfig
    ) -> SourceDiscoveryResult | None: ...

    def extract_excerpt(
        self, discovery: SourceDiscoveryResult, repo_root: Path, config: UserConfig
    ) -> TranscriptExcerpt | None: ...

    def render_prompt(self, context: HandoffContext) -> PromptArtifact: ...

    def discover_launch(self, config: UserConfig) -> LaunchSpec | None: ...

    def launch(
        self, prompt_path: Path, prompt_text: str, spec: LaunchSpec | None
    ) -> LaunchResult: ...
