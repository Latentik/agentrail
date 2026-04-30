"""Codex adapter: source discovery, excerpt extraction, and target prompt support."""

from __future__ import annotations

import subprocess
from pathlib import Path

from agentrail.adapters._file_source import discover_file_sources, extract_file_excerpt
from agentrail.adapters.base import PromptArtifact
from agentrail.config import UserConfig
from agentrail.models import (
    HandoffContext,
    LaunchResult,
    LaunchSpec,
    SourceDiscoveryResult,
    TranscriptExcerpt,
)
from agentrail.prompt.codex import render_codex_prompt


class CodexAdapter:
    name = "codex"

    def discover_sources(self, repo_root: Path, config: UserConfig) -> SourceDiscoveryResult | None:
        agent_config = config.agents.get(self.name)
        if not agent_config or not agent_config.enabled or not agent_config.sessions_dir:
            return None
        return discover_file_sources(self.name, agent_config.sessions_dir, repo_root)

    def extract_excerpt(
        self, discovery: SourceDiscoveryResult, repo_root: Path, config: UserConfig
    ) -> TranscriptExcerpt | None:
        del repo_root, config
        return extract_file_excerpt(self.name, "codex-transcript.excerpt.md", discovery)

    def render_prompt(self, context: HandoffContext) -> PromptArtifact:
        return PromptArtifact(
            target=self.name,
            filename="next-prompt.codex.md",
            content=render_codex_prompt(context),
        )

    def discover_launch(self, config: UserConfig) -> LaunchSpec | None:
        agent_config = config.agents.get(self.name)
        if not agent_config or not agent_config.enabled or not agent_config.binary:
            return None
        return LaunchSpec(binary=agent_config.binary, args_template=agent_config.launch_args)

    def launch(self, prompt_path: Path, prompt_text: str, spec: LaunchSpec | None) -> LaunchResult:
        return _launch_command(prompt_path, prompt_text, spec)


def _launch_command(prompt_path: Path, prompt_text: str, spec: LaunchSpec | None) -> LaunchResult:
    if not spec:
        return LaunchResult(
            attempted=False,
            command=[],
            launched=False,
            message=f"No launch configuration available. Use the prompt at {prompt_path}.",
        )
    template = spec.args_template or ["{prompt_path}"]
    command = [
        spec.binary,
        *[
            arg.format(
                prompt_path=str(prompt_path),
                prompt_text=prompt_text,
            )
            for arg in template
        ],
    ]
    try:
        proc = subprocess.run(command, check=False)
    except OSError as exc:
        return LaunchResult(
            attempted=True,
            command=command,
            launched=False,
            message=f"Failed to launch {spec.binary}: {exc}",
        )
    if proc.returncode != 0:
        return LaunchResult(
            attempted=True,
            command=command,
            launched=False,
            message=f"{spec.binary} exited with status {proc.returncode}",
        )
    return LaunchResult(
        attempted=True,
        command=command,
        launched=True,
        message=f"Launched {spec.binary}.",
    )


