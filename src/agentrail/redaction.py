"""Best-effort redaction helpers."""

from __future__ import annotations

import math
import re

TOKEN_PATTERNS = [
    re.compile(r"(?im)\b(api[_-]?key|access[_-]?token|secret|password)\b\s*[:=]\s*([^\s]+)"),
    re.compile(r"(?i)bearer\s+[a-z0-9._\-]+"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S),
]

LONG_TOKEN_PATTERN = re.compile(r"\b[A-Za-z0-9_\-]{24,}\b")


def redact_text(text: str) -> str:
    redacted = text
    for pattern in TOKEN_PATTERNS:
        redacted = pattern.sub(_replace_secret, redacted)

    def replace_entropy(match: re.Match[str]) -> str:
        token = match.group(0)
        if _looks_high_entropy(token):
            return "[REDACTED]"
        return token

    return LONG_TOKEN_PATTERN.sub(replace_entropy, redacted)


def should_skip_file_contents(path: str, allow_dotenv: bool = False) -> bool:
    lower = path.lower()
    if allow_dotenv:
        return False
    return lower.endswith(".env") or "/.env" in lower or lower.startswith(".env")


def _replace_secret(match: re.Match[str]) -> str:
    groups = match.groups()
    if len(groups) >= 2:
        return f"{groups[0]}=[REDACTED]"
    return "[REDACTED]"


def _looks_high_entropy(token: str) -> bool:
    unique = len(set(token))
    if unique < 10:
        return False
    entropy = 0.0
    for char in set(token):
        probability = token.count(char) / len(token)
        entropy -= probability * math.log2(probability)
    return entropy >= 3.5
