"""Persisted handoff schema."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ProjectInfo(BaseModel):
    root: str
    name: str
    branch: str | None = None
    head: str | None = None
    dirty: bool


class SourceAgentInfo(BaseModel):
    name: str
    session_path: str | None = None
    confidence: Literal["high", "medium", "low"] | None = None
    reason: str | None = None


class SummaryInfo(BaseModel):
    goal: str | None = None
    current_state: str | None = None
    decisions: list[str] = Field(default_factory=list)
    failed_attempts: list[str] = Field(default_factory=list)
    verification: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)


class ArtifactPaths(BaseModel):
    diff: str
    staged_diff: str
    summary: str
    transcript_excerpt: str | None = None
    prompts: dict[str, str] = Field(default_factory=dict)


class WarningInfo(BaseModel):
    code: str
    message: str


class HandoffDocument(BaseModel):
    schema_version: str = "0.1"
    created_at: str
    updated_at: str
    project: ProjectInfo
    source_agents: list[SourceAgentInfo] = Field(default_factory=list)
    selected_source_agent: str | None = None
    changed_files: list[str] = Field(default_factory=list)
    untracked_files: list[str] = Field(default_factory=list)
    summary: SummaryInfo = Field(default_factory=SummaryInfo)
    artifacts: ArtifactPaths
    warnings: list[WarningInfo] = Field(default_factory=list)
