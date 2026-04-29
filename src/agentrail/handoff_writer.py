"""Artifact writing for project-local handoff state."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from agentrail.handoff_schema import (
    ArtifactPaths,
    HandoffDocument,
    ProjectInfo,
    SourceAgentInfo,
    SummaryInfo,
    WarningInfo,
)
from agentrail.models import (
    FileSnapshot,
    GitSnapshot,
    SourceDiscoveryResult,
    TranscriptExcerpt,
    WarningRecord,
)
from agentrail.paths import ProjectPaths


def ensure_handoff_dirs(paths: ProjectPaths) -> None:
    paths.handoff_dir.mkdir(exist_ok=True)
    paths.state_dir.mkdir(exist_ok=True)


def write_capture_artifacts(
    paths: ProjectPaths,
    git: GitSnapshot,
    files: FileSnapshot,
    summary_markdown: str,
    source_discoveries: list[SourceDiscoveryResult],
    transcript_excerpt: TranscriptExcerpt | None,
    warnings: list[WarningRecord],
    prompt_paths: dict[str, str] | None = None,
) -> HandoffDocument:
    ensure_handoff_dirs(paths)
    created_at = _existing_created_at(paths.handoff_dir / "handoff.json")
    now = datetime.now(UTC).isoformat()

    diff_path = paths.handoff_dir / "diff.patch"
    staged_diff_path = paths.handoff_dir / "staged.diff.patch"
    summary_path = paths.handoff_dir / "summary.md"
    commands_path = paths.handoff_dir / "commands.md"
    decisions_path = paths.handoff_dir / "decisions.md"
    failures_path = paths.handoff_dir / "failures.md"
    git_json_path = paths.state_dir / "git.json"
    files_json_path = paths.state_dir / "files.json"
    sources_json_path = paths.state_dir / "agent-sources.json"

    diff_path.write_text(git.diff, encoding="utf-8")
    staged_diff_path.write_text(git.staged_diff, encoding="utf-8")
    summary_path.write_text(summary_markdown, encoding="utf-8")
    commands_path.write_text(
        _simple_list_doc(
            "Commands Detected",
            transcript_excerpt.commands if transcript_excerpt else [],
        ),
        encoding="utf-8",
    )
    decisions_path.write_text(_simple_list_doc("Decisions", []), encoding="utf-8")
    failures_path.write_text(
        _simple_list_doc(
            "Failures",
            transcript_excerpt.errors if transcript_excerpt else [],
        ),
        encoding="utf-8",
    )

    transcript_path: Path | None = None
    if transcript_excerpt:
        transcript_path = paths.handoff_dir / transcript_excerpt.artifact_name
        transcript_path.write_text(transcript_excerpt.content, encoding="utf-8")

    git_json_path.write_text(
        json.dumps(
            {
                "repo_root": str(git.repo_root),
                "branch": git.branch,
                "head": git.head,
                "dirty": git.dirty,
                "status_short": git.status_short.splitlines(),
                "recent_commits": git.recent_commits,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    files_json_path.write_text(
        json.dumps(
            {
                "changed_files": files.changed_files,
                "untracked_files": files.untracked_files,
                "diff_bytes": files.diff_bytes,
                "staged_diff_bytes": files.staged_diff_bytes,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    sources_json_path.write_text(
        json.dumps(_source_discoveries_payload(source_discoveries), indent=2) + "\n",
        encoding="utf-8",
    )

    selected = next((item for item in source_discoveries if item.selected_session), None)
    document = HandoffDocument(
        created_at=created_at or now,
        updated_at=now,
        project=ProjectInfo(
            root=str(git.repo_root),
            name=git.repo_root.name,
            branch=git.branch,
            head=git.head,
            dirty=git.dirty,
        ),
        source_agents=[
            SourceAgentInfo(
                name=item.adapter_name,
                session_path=str(item.selected_session) if item.selected_session else None,
                confidence=item.matched_sessions[0].confidence if item.matched_sessions else None,
                reason=item.matched_sessions[0].reason if item.matched_sessions else None,
            )
            for item in source_discoveries
        ],
        selected_source_agent=selected.adapter_name if selected else None,
        changed_files=files.changed_files,
        untracked_files=files.untracked_files,
        summary=SummaryInfo(
            current_state="Dirty working tree" if git.dirty else "Clean working tree",
            failed_attempts=transcript_excerpt.errors if transcript_excerpt else [],
            verification=transcript_excerpt.verification if transcript_excerpt else [],
            next_steps=[],
        ),
        artifacts=ArtifactPaths(
            diff=str(diff_path.relative_to(git.repo_root)),
            staged_diff=str(staged_diff_path.relative_to(git.repo_root)),
            summary=str(summary_path.relative_to(git.repo_root)),
            transcript_excerpt=str(transcript_path.relative_to(git.repo_root))
            if transcript_path
            else None,
            prompts=prompt_paths or {},
        ),
        warnings=[WarningInfo(code=item.code, message=item.message) for item in warnings],
    )
    (paths.handoff_dir / "handoff.json").write_text(
        json.dumps(document.model_dump(), indent=2) + "\n", encoding="utf-8"
    )
    return document


def _source_discoveries_payload(
    source_discoveries: list[SourceDiscoveryResult],
) -> dict[str, object]:
    payload: dict[str, object] = {}
    for item in source_discoveries:
        payload[item.adapter_name] = {
            "found": item.found,
            "sessions_dir": str(item.source_dir) if item.source_dir else None,
            "matched_sessions": [
                {
                    "path": str(match.path),
                    "mtime": match.mtime,
                    "confidence": match.confidence,
                    "reason": match.reason,
                }
                for match in item.matched_sessions
            ],
            "selected_session": str(item.selected_session) if item.selected_session else None,
        }
    return payload


def _existing_created_at(handoff_json_path: Path) -> str | None:
    if not handoff_json_path.exists():
        return None
    try:
        data = json.loads(handoff_json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    value = data.get("created_at")
    return value if isinstance(value, str) else None


def _simple_list_doc(title: str, items: list[str]) -> str:
    lines = [f"# {title}", ""]
    if not items:
        lines.append("- None")
    else:
        lines.extend(f"- {item}" for item in items)
    return "\n".join(lines) + "\n"
