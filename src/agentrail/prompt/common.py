"""Shared prompt rendering helpers."""

from __future__ import annotations

from pathlib import Path

from agentrail.git_state import diff_summary
from agentrail.models import HandoffContext

MAX_INLINE_DIFF_BYTES = 12_000
TARGET_TOKEN_BUDGETS: dict[str, int] = {
    "gemini": 64_000,
    "claude": 128_000,
    "codex": 128_000,
    "opencode": 128_000,
}


def render_common_sections(context: HandoffContext) -> str:
    git = context.git
    files = context.files
    transcript_path = None
    if context.transcript_excerpt:
        transcript_path = context.handoff_dir / context.transcript_excerpt.artifact_name
    diff_text = git.diff
    budget = TARGET_TOKEN_BUDGETS.get(context.target, 64_000)
    inline_diff = _choose_diff_presentation(diff_text, budget)
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

    if context.include_agents_md:
        agents_md = _read_project_file(git.repo_root, "AGENTS.md")
        if agents_md:
            lines.extend(["", "## AGENTS.md", agents_md])

    if context.include_cursorrules:
        cursorrules = _read_project_file(git.repo_root, ".cursorrules")
        if cursorrules:
            lines.extend(["", "## .cursorrules", cursorrules])

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


def _choose_diff_presentation(diff_text: str, budget: int) -> str:
    diff_bytes = len(diff_text.encode("utf-8"))
    estimated_tokens = diff_bytes // 4
    if diff_bytes <= MAX_INLINE_DIFF_BYTES and estimated_tokens <= budget * 0.1:
        return diff_summary(diff_text)
    if estimated_tokens > budget * 0.3:
        return _diff_file_summary(diff_text)
    return "Diff too large to inline. Read `.handoff/diff.patch`."


def _diff_file_summary(diff_text: str) -> str:
    files: list[str] = []
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                files.append(parts[-2][2:])  # strip a/ prefix
    if not files:
        return "Diff too large to inline. Read `.handoff/diff.patch`."
    return "Large diff truncated to file list:\n" + "\n".join(f"- {f}" for f in files[:50])


def _read_project_file(repo_root: Path, filename: str) -> str | None:
    path = repo_root / filename
    if path.exists():
        try:
            return path.read_text(encoding="utf-8")
        except OSError:
            pass
    return None


def _bullet_list(items: list[str]) -> list[str]:
    if not items:
        return ["- None"]
    return [f"- {item}" for item in items]


def _relative_artifact_path(repo_root: Path, artifact_path: Path) -> str:
    return str(artifact_path.relative_to(repo_root))
