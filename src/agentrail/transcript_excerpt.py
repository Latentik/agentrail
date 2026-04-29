"""Helpers for extracting plain-text transcript signals."""

from __future__ import annotations

from collections import deque
from pathlib import Path

from agentrail.redaction import redact_text

COMMAND_MARKERS = ("$ ", "> ", "command", "cmd")
ERROR_MARKERS = ("error", "exception", "traceback", "failed", "failure")
VERIFY_MARKERS = ("pytest", "tests passed", "ruff", "build succeeded", "validated")
USER_MARKERS = ("user", "prompt")
ASSISTANT_MARKERS = ("assistant", "summary")


def excerpt_recent_text(
    path: Path, max_lines: int = 120
) -> tuple[str, list[str], list[str], list[str]]:
    recent: deque[str] = deque(maxlen=max_lines)
    commands: list[str] = []
    errors: list[str] = []
    verification: list[str] = []

    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            line = raw_line.rstrip("\n")
            recent.append(line)
            normalized = line.lower()
            if any(marker in normalized for marker in COMMAND_MARKERS) and len(commands) < 20:
                commands.append(line.strip())
            if any(marker in normalized for marker in ERROR_MARKERS) and len(errors) < 20:
                errors.append(line.strip())
            if any(marker in normalized for marker in VERIFY_MARKERS) and len(verification) < 20:
                verification.append(line.strip())

    excerpt_lines: list[str] = [
        "## Raw Recent Excerpt",
        "",
        "```text",
        *list(recent),
        "```",
    ]
    return redact_text("\n".join(excerpt_lines) + "\n"), commands, errors, verification


def maybe_extract_structured_sections(text: str) -> dict[str, list[str]]:
    sections = {
        "user": [],
        "assistant": [],
        "commands": [],
        "errors": [],
        "verification": [],
    }
    for raw_line in text.splitlines():
        line = raw_line.strip()
        lower = line.lower()
        if not line:
            continue
        if any(marker in lower for marker in USER_MARKERS):
            sections["user"].append(line)
        if any(marker in lower for marker in ASSISTANT_MARKERS):
            sections["assistant"].append(line)
        if any(marker in lower for marker in COMMAND_MARKERS):
            sections["commands"].append(line)
        if any(marker in lower for marker in ERROR_MARKERS):
            sections["errors"].append(line)
        if any(marker in lower for marker in VERIFY_MARKERS):
            sections["verification"].append(line)
    return sections
