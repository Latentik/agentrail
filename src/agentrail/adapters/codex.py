"""Codex adapter: source discovery, excerpt extraction, and target prompt support."""

from __future__ import annotations

import subprocess
from datetime import UTC, datetime
from pathlib import Path

from agentrail.adapters.base import PromptArtifact
from agentrail.config import UserConfig
from agentrail.models import (
    HandoffContext,
    LaunchResult,
    LaunchSpec,
    SourceDiscoveryResult,
    SourceMatch,
    TranscriptExcerpt,
    WarningRecord,
)
from agentrail.prompt.codex import render_codex_prompt
from agentrail.redaction import redact_text
from agentrail.transcript_excerpt import excerpt_recent_text, maybe_extract_structured_sections


class CodexAdapter:
    name = "codex"

    def discover_sources(self, repo_root: Path, config: UserConfig) -> SourceDiscoveryResult | None:
        agent_config = config.agents.get(self.name)
        if not agent_config or not agent_config.enabled or not agent_config.sessions_dir:
            return None
        sessions_dir = Path(agent_config.sessions_dir).expanduser()
        if not sessions_dir.exists():
            return SourceDiscoveryResult(
                adapter_name=self.name,
                found=False,
                source_dir=sessions_dir,
                warnings=[
                    WarningRecord(
                        code="codex.sessions_missing",
                        message="Configured Codex sessions directory does not exist.",
                    )
                ],
            )

        matched: list[SourceMatch] = []
        repo_root_text = str(repo_root)
        candidates = sorted(
            (path for path in sessions_dir.rglob("*") if path.is_file()),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        for path in candidates[:200]:
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            confidence, reason = _score_session(path, text, repo_root_text)
            if confidence:
                matched.append(
                    SourceMatch(
                        adapter_name=self.name,
                        path=path,
                        mtime=datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat(),
                        confidence=confidence,
                        reason=reason,
                    )
                )
        matched.sort(key=_rank_match)
        selected = matched[0].path if matched else None
        return SourceDiscoveryResult(
            adapter_name=self.name,
            found=bool(matched),
            source_dir=sessions_dir,
            matched_sessions=matched[:10],
            selected_session=selected,
        )

    def extract_excerpt(
        self, discovery: SourceDiscoveryResult, repo_root: Path, config: UserConfig
    ) -> TranscriptExcerpt | None:
        del repo_root, config
        if not discovery.selected_session:
            return None
        path = discovery.selected_session
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            return TranscriptExcerpt(
                adapter_name=self.name,
                artifact_name="codex-transcript.excerpt.md",
                content=f"## Errors / Failures\n\n- Failed to read transcript: {exc}\n",
                errors=[str(exc)],
            )

        structured = maybe_extract_structured_sections(text)
        raw_excerpt, commands, errors, verification = excerpt_recent_text(path)
        sections = ["# Codex Transcript Excerpt", ""]
        if structured["user"]:
            sections.extend(["## User Prompts", ""])
            sections.extend(f"- {item}" for item in structured["user"][:20])
            sections.append("")
        if structured["assistant"]:
            sections.extend(["## Assistant Signals", ""])
            sections.extend(f"- {item}" for item in structured["assistant"][:20])
            sections.append("")
        if commands:
            sections.extend(["## Commands Detected", ""])
            sections.extend(f"- {item}" for item in commands[:20])
            sections.append("")
        if verification:
            sections.extend(["## Verification Signals", ""])
            sections.extend(f"- {item}" for item in verification[:20])
            sections.append("")
        if errors:
            sections.extend(["## Errors / Failures", ""])
            sections.extend(f"- {item}" for item in errors[:20])
            sections.append("")
        sections.append(raw_excerpt.strip())
        content = redact_text("\n".join(sections).rstrip() + "\n")
        return TranscriptExcerpt(
            adapter_name=self.name,
            artifact_name="codex-transcript.excerpt.md",
            content=content,
            commands=commands[:20],
            errors=errors[:20],
            verification=verification[:20],
        )

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


def _score_session(path: Path, text: str, repo_root_text: str) -> tuple[str | None, str]:
    lower = text.lower()
    if repo_root_text in text:
        return "high", "contains repo root path"
    if path.suffix in {".jsonl", ".log", ".md"} and any(
        marker in lower for marker in ("codex", "assistant", "user")
    ):
        return "low", "recent session-like file"
    return None, ""


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


def _confidence_rank(confidence: str) -> int:
    order = {"high": 0, "medium": 1, "low": 2}
    return order.get(confidence, 3)


def _rank_match(item: SourceMatch) -> tuple[int, float]:
    return (_confidence_rank(item.confidence), -item.path.stat().st_mtime)
