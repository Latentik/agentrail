"""OpenCode adapter."""

from __future__ import annotations

from pathlib import Path

from agentrail.adapters.base import PromptArtifact
from agentrail.adapters.codex import _launch_command
from agentrail.config import UserConfig
from agentrail.models import (
    HandoffContext,
    LaunchResult,
    LaunchSpec,
    SourceDiscoveryResult,
    TranscriptExcerpt,
)
from agentrail.prompt.opencode import render_opencode_prompt


class OpenCodeAdapter:
    name = "opencode"

    def discover_sources(self, repo_root: Path, config: UserConfig) -> SourceDiscoveryResult | None:
        del repo_root, config
        return None

    def extract_excerpt(
        self, discovery: SourceDiscoveryResult, repo_root: Path, config: UserConfig
    ) -> TranscriptExcerpt | None:
        del discovery, repo_root, config
        return None

    def render_prompt(self, context: HandoffContext) -> PromptArtifact:
        return PromptArtifact(
            target=self.name,
            filename="next-prompt.opencode.md",
            content=render_opencode_prompt(context),
        )

    def discover_launch(self, config: UserConfig) -> LaunchSpec | None:
        agent_config = config.agents.get(self.name)
        if not agent_config or not agent_config.enabled or not agent_config.binary:
            return None
        return LaunchSpec(binary=agent_config.binary, args_template=agent_config.launch_args)

    def launch(self, prompt_path: Path, prompt_text: str, spec: LaunchSpec | None) -> LaunchResult:
        return _launch_command(prompt_path, prompt_text, spec)
