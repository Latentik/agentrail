"""Shared prompt rendering helpers."""

from __future__ import annotations

from pathlib import Path

from agentrail.git_state import diff_summary
from agentrail.models import HandoffContext

MAX_INLINE_DIFF_BYTES = 12_000


def render_common_sections(context: HandoffContext) -> str:
    git = context.git
    files = context.files
    transcript_path = None
    if context.transcript_excerpt:
        transcript_path = context.handoff_dir / context.transcript_excerpt.artifact_name
    diff_text = git.diff
    inline_diff = (
        diff_summary(diff_text)
        if len(diff_text.encode("utf-8")) <= MAX_INLINE_DIFF_BYTES
        else "Diff too large to inline. Read `.handoff/diff.patch`."
    )
    source_name = "none detected"
    if context.selected_source:
        source_name = context.selected_source.adapter_name

    lines = [
        f"Project root: {git.repo_root}",
        f"Branch: {git.branch or 'DETACHED'}",
        f"HEAD: {git.head or 'No commits yet'}",
        "",
        "## Current State",
        "Git status:",
        "```text",
        git.status_short.strip() or "clean working tree",
        "```",
        "",
        "### Changes since last commit:",
        "```diff",
        inline_diff,
        "```",
        "",
        "### Recently modified files:",
        *_bullet_list(files.changed_files),
        "",
        "### Untracked files:",
        *_bullet_list(files.untracked_files),
        "",
        "### Recent commit history:",
        *_bullet_list(git.recent_commits),
        "",
        f"## Source Agent Context (Source: {source_name})",
    ]
    if context.transcript_excerpt:
        lines.append("The following signals were extracted from the previous agent's session:")
        if context.transcript_excerpt.commands:
            lines.append("\n**Last executed commands:**")
            lines.extend(_bullet_list(context.transcript_excerpt.commands[:5]))
        if context.transcript_excerpt.errors:
            lines.append("\n**Recent errors/failures:**")
            lines.extend(_bullet_list(context.transcript_excerpt.errors[:5]))
        if context.transcript_excerpt.verification:
            lines.append("\n**Verification signals:**")
            lines.extend(_bullet_list(context.transcript_excerpt.verification[:5]))
    else:
        lines.append(
            "No previous transcript evidence detected. Relying on current repository state."
        )

    lines.extend(
        [
            "",
            "## Handoff Artifacts",
            "- Summary: `.handoff/summary.md`",
            "- Diff: `.handoff/diff.patch`",
            "- Staged diff: `.handoff/staged.diff.patch`",
        ]
    )
    if transcript_path:
        relative_path = _relative_artifact_path(git.repo_root, transcript_path)
        lines.append(f"- Transcript excerpt: `{relative_path}`")
    lines.extend(
        [
            "",
            "Suggested next action:",
            "- Inspect the repo and handoff artifacts before making new changes.",
        ]
    )
    return "\n".join(lines)


def _bullet_list(items: list[str]) -> list[str]:
    if not items:
        return ["- None"]
    return [f"- {item}" for item in items]


def _relative_artifact_path(repo_root: Path, artifact_path: Path) -> str:
    return str(artifact_path.relative_to(repo_root))
