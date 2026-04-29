from agentrail.handoff_schema import ArtifactPaths, HandoffDocument, ProjectInfo


def test_handoff_document_round_trip() -> None:
    document = HandoffDocument(
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:01Z",
        project=ProjectInfo(root="/tmp/repo", name="repo", dirty=True),
        artifacts=ArtifactPaths(
            diff=".handoff/diff.patch",
            staged_diff=".handoff/staged.diff.patch",
            summary=".handoff/summary.md",
            prompts={"gemini": ".handoff/next-prompt.gemini.md"},
        ),
    )
    payload = document.model_dump()
    restored = HandoffDocument.model_validate(payload)
    assert restored.artifacts.prompts["gemini"].endswith("next-prompt.gemini.md")
