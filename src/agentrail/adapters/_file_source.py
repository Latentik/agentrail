"""Generic file-based source discovery and excerpt helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from agentrail.models import (
    SourceDiscoveryResult,
    SourceMatch,
    TranscriptExcerpt,
    WarningRecord,
)
from agentrail.redaction import redact_text
from agentrail.transcript_excerpt import excerpt_recent_text, maybe_extract_structured_sections

DEFAULT_CONTENT_MARKERS: dict[str, tuple[str, ...]] = {
    "codex": ("codex", "assistant", "user"),
    "claude": ("claude", "assistant", "user"),
    "gemini": ("gemini", "assistant", "user"),
    "opencode": ("opencode", "assistant", "user"),
}


def discover_file_sources(
    adapter_name: str,
    sessions_dir: str | None,
    repo_root: Path,
    content_markers: tuple[str, ...] | None = None,
) -> SourceDiscoveryResult | None:
    """Discover session files in a directory, scoring by repo root and markers."""
    if not sessions_dir:
        return None
    path = Path(sessions_dir).expanduser()
    if not path.exists():
        return SourceDiscoveryResult(
            adapter_name=adapter_name,
            found=False,
            source_dir=path,
            warnings=[
                WarningRecord(
                    code=f"{adapter_name}.sessions_missing",
                    message=f"Configured {adapter_name} sessions directory does not exist.",
                )
            ],
        )

    markers = content_markers or DEFAULT_CONTENT_MARKERS.get(adapter_name, ())
    repo_root_text = str(repo_root)
    candidates = sorted(
        (p for p in path.rglob("*") if p.is_file()),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    matched: list[SourceMatch] = []
    for candidate in candidates[:200]:
        try:
            text = candidate.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        confidence, reason = _score_session(candidate, text, repo_root_text, markers)
        if confidence:
            matched.append(
                SourceMatch(
                    adapter_name=adapter_name,
                    path=candidate,
                    mtime=datetime.fromtimestamp(candidate.stat().st_mtime, UTC).isoformat(),
                    confidence=confidence,
                    reason=reason,
                )
            )
    matched.sort(key=_rank_match)
    selected = matched[0].path if matched else None
    return SourceDiscoveryResult(
        adapter_name=adapter_name,
        found=bool(matched),
        source_dir=path,
        matched_sessions=matched[:10],
        selected_session=selected,
    )


def extract_file_excerpt(
    adapter_name: str,
    artifact_name: str,
    discovery: SourceDiscoveryResult,
) -> TranscriptExcerpt | None:
    """Extract a redacted transcript excerpt from a discovered session file."""
    if not discovery.selected_session:
        return None
    path = discovery.selected_session
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return TranscriptExcerpt(
            adapter_name=adapter_name,
            artifact_name=artifact_name,
            content=f"## Errors / Failures\n\n- Failed to read transcript: {exc}\n",
            errors=[str(exc)],
        )

    structured = maybe_extract_structured_sections(text)
    raw_excerpt, commands, errors, verification = excerpt_recent_text(path)
    sections = [f"# {adapter_name.title()} Transcript Excerpt", ""]
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
        adapter_name=adapter_name,
        artifact_name=artifact_name,
        content=content,
        commands=commands[:20],
        errors=errors[:20],
        verification=verification[:20],
    )


def _score_session(
    path: Path, text: str, repo_root_text: str, markers: tuple[str, ...]
) -> tuple[Literal["high", "medium", "low"] | None, str]:
    lower = text.lower()
    if repo_root_text in text:
        return "high", "contains repo root path"
    if path.suffix in {".jsonl", ".log", ".md"} and markers and any(
        marker in lower for marker in markers
    ):
        return "low", "recent session-like file"
    return None, ""


def _confidence_rank(confidence: Literal["high", "medium", "low"]) -> int:
    order: dict[str, int] = {"high": 0, "medium": 1, "low": 2}
    return order.get(confidence, 3)


def _rank_match(item: SourceMatch) -> tuple[int, float]:
    return (_confidence_rank(item.confidence), -item.path.stat().st_mtime)
