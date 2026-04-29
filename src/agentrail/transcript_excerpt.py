"""Helpers for extracting plain-text transcript signals."""

from __future__ import annotations

import json
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

    is_jsonl = path.suffix == ".jsonl"

    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            line = raw_line.rstrip("\n")
            if not line:
                continue

            content_to_match = line
            if is_jsonl:
                try:
                    data = json.loads(line)
                    # Try to extract text content from common JSONL formats
                    if isinstance(data, dict):
                        # Some formats use 'text', 'content', 'message', etc.
                        content_to_match = str(data.get("content") or data.get("text") or line)
                except json.JSONDecodeError:
                    pass

            recent.append(line)
            normalized = content_to_match.lower()
            if any(marker in normalized for marker in COMMAND_MARKERS) and len(commands) < 20:
                commands.append(content_to_match.strip())
            if any(marker in normalized for marker in ERROR_MARKERS) and len(errors) < 20:
                errors.append(content_to_match.strip())
            if any(marker in normalized for marker in VERIFY_MARKERS) and len(verification) < 20:
                verification.append(content_to_match.strip())

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
        if not line:
            continue
            
        content = line
        # Try JSONL parsing if it looks like a JSON object
        if line.startswith("{") and line.endswith("}"):
            try:
                data = json.loads(line)
                if isinstance(data, dict):
                    # Try to extract the most descriptive content
                    content = str(data.get("content") or data.get("text") or data.get("message") or line)
            except json.JSONDecodeError:
                pass

        lower = content.lower()
        if any(marker in lower for marker in USER_MARKERS):
            sections["user"].append(content)
        if any(marker in lower for marker in ASSISTANT_MARKERS):
            sections["assistant"].append(content)
        if any(marker in lower for marker in COMMAND_MARKERS):
            sections["commands"].append(content)
        if any(marker in lower for marker in ERROR_MARKERS):
            sections["errors"].append(content)
        if any(marker in lower for marker in VERIFY_MARKERS):
            sections["verification"].append(content)
    return sections
