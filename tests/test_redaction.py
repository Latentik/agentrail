from agentrail.redaction import redact_text


def test_redact_text_removes_obvious_secret_patterns() -> None:
    text = "API_KEY=supersecretvalue\nAuthorization: Bearer abcdefghijklmnopqrstuvwxyz123456\n"
    redacted = redact_text(text)
    assert "supersecretvalue" not in redacted
    assert "abcdefghijklmnopqrstuvwxyz123456" not in redacted
    assert "[REDACTED]" in redacted
