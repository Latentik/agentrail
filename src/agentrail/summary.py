"""Deterministic handoff summary generation."""

from __future__ import annotations

from agentrail.models import (
    FileSnapshot,
    GitSnapshot,
    SourceDiscoveryResult,
    TranscriptExcerpt,
    WarningRecord,
)


def render_summary(
    project_name: str,
    git: GitSnapshot,
    files: FileSnapshot,
    source_discoveries: list[SourceDiscoveryResult],
    transcript_excerpt: TranscriptExcerpt | None,
    warnings: list[WarningRecord],
) -> str:
    lines = [
        "# Handoff Summary",
        "",
        "## Project",
        f"- Name: {project_name}",
        f"- Root: {git.repo_root}",
        f"- Branch: {git.branch or 'DETACHED'}",
        f"- HEAD: {git.head or 'No commits yet'}",
        f"- Dirty: {'yes' if git.dirty else 'no'}",
        "",
        "## Source Agent Evidence",
    ]

    if source_discoveries:
        for discovery in source_discoveries:
            selected = str(discovery.selected_session) if discovery.selected_session else "none"
            lines.append(f"- {discovery.adapter_name}: selected={selected}")
            for match in discovery.matched_sessions[:3]:
                lines.append(f"  - {match.confidence}: {match.path} ({match.reason})")
    else:
        lines.append("- No agent transcript evidence found.")

    lines.extend(
        [
            "",
            "## Current Git State",
            "```text",
            git.status_short.strip() or "clean working tree",
            "```",
            "",
            "## Changed Files",
        ]
    )
    lines.extend(_render_list(files.changed_files))
    lines.extend(["", "## Untracked Files"])
    lines.extend(_render_list(files.untracked_files))
    lines.extend(["", "## Recent Commits"])
    lines.extend(_render_list(git.recent_commits))
    lines.extend(["", "## Transcript Signals"])
    if transcript_excerpt:
        lines.append(f"- Transcript excerpt available: {transcript_excerpt.artifact_name}")
        lines.append(f"- Commands detected: {len(transcript_excerpt.commands)}")
        lines.append(f"- Errors detected: {len(transcript_excerpt.errors)}")
    else:
        lines.append("- No transcript excerpt available. Summary is based on Git state only.")
    lines.extend(["", "## Commands Detected"])
    lines.extend(_render_list(transcript_excerpt.commands if transcript_excerpt else []))
    lines.extend(["", "## Errors / Failures Detected"])
    lines.extend(_render_list(transcript_excerpt.errors if transcript_excerpt else []))
    lines.extend(["", "## Suggested Next Steps"])
    lines.extend(_render_next_steps(git, files, transcript_excerpt))
    lines.extend(["", "## Safety Notes"])
    lines.append("- Redaction is best-effort. Review prompt artifacts before sharing externally.")
    for warning in warnings:
        lines.append(f"- {warning.code}: {warning.message}")
    return "\n".join(lines).rstrip() + "\n"


def _render_list(items: list[str]) -> list[str]:
    if not items:
        return ["- None"]
    return [f"- {item}" for item in items]


def _render_next_steps(
    git: GitSnapshot, files: FileSnapshot, transcript_excerpt: TranscriptExcerpt | None
) -> list[str]:
    steps: list[str] = []
    if files.changed_files:
        steps.append(
            "Review changed files and correlate them with the unstaged/staged diff artifacts."
        )
    if transcript_excerpt and transcript_excerpt.errors:
        steps.append("Investigate the most recent failures before making more changes.")
    if transcript_excerpt and transcript_excerpt.verification:
        steps.append("Re-run the last verification steps before declaring the handoff complete.")
    if git.dirty and not steps:
        steps.append(
            "Inspect the working tree and decide whether to continue, stage, "
            "or revert local changes."
        )
    if not steps:
        steps.append(
            "Inspect the repository and confirm the next feature or bugfix before proceeding."
        )
    return [f"- {step}" for step in steps]
