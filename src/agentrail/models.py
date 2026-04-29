"""Internal models used during capture and prompt generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class WarningRecord:
    code: str
    message: str


@dataclass(slots=True)
class GitSnapshot:
    repo_root: Path
    branch: str | None
    head: str | None
    status_short: str
    diff: str
    staged_diff: str
    untracked_files: list[str]
    recent_commits: list[str]

    @property
    def dirty(self) -> bool:
        return bool(self.status_short.strip())

    @property
    def changed_files(self) -> list[str]:
        files: list[str] = []
        for line in self.status_short.splitlines():
            if len(line) < 4:
                continue
            path = line[3:].strip()
            if path and path not in files:
                files.append(path)
        return files


@dataclass(slots=True)
class FileSnapshot:
    changed_files: list[str]
    untracked_files: list[str]
    diff_bytes: int
    staged_diff_bytes: int


@dataclass(slots=True)
class SourceMatch:
    adapter_name: str
    path: Path
    mtime: str
    confidence: str
    reason: str


@dataclass(slots=True)
class SourceDiscoveryResult:
    adapter_name: str
    found: bool
    source_dir: Path | None
    matched_sessions: list[SourceMatch] = field(default_factory=list)
    selected_session: Path | None = None
    warnings: list[WarningRecord] = field(default_factory=list)


@dataclass(slots=True)
class TranscriptExcerpt:
    adapter_name: str
    artifact_name: str
    content: str
    commands: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    verification: list[str] = field(default_factory=list)
    warnings: list[WarningRecord] = field(default_factory=list)


@dataclass(slots=True)
class LaunchSpec:
    binary: str
    args_template: list[str] = field(default_factory=list)


@dataclass(slots=True)
class LaunchResult:
    attempted: bool
    command: list[str]
    launched: bool
    message: str


@dataclass(slots=True)
class HandoffContext:
    target: str
    project_name: str
    git: GitSnapshot
    files: FileSnapshot
    summary_markdown: str
    source_discoveries: list[SourceDiscoveryResult]
    selected_source: SourceDiscoveryResult | None
    transcript_excerpt: TranscriptExcerpt | None
    diff_path: Path
    staged_diff_path: Path
    handoff_dir: Path
    warnings: list[WarningRecord] = field(default_factory=list)
