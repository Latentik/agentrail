"""Claude Code specific prompt rendering."""

from __future__ import annotations

from agentrail.models import HandoffContext
from agentrail.prompt.common import render_common_sections


def render_claude_prompt(context: HandoffContext) -> str:
    return (
        "You are continuing work that started in another coding agent.\n"
        "Do not restart from scratch. First inspect the repository and the diff artifacts.\n"
        "Treat `.handoff/` as helpful context, not as perfect truth.\n"
        "Pay attention to failed attempts and verification gaps.\n"
        "Ask before destructive operations. Run tests before declaring the task done.\n\n"
        + render_common_sections(context)
    )
