# Security Notes

## Redaction behavior

`agentrail` performs best-effort redaction on all text that enters handoff artifacts:

- Transcript excerpts
- Diff and staged diff outputs
- Generated prompts

Patterns include API keys, access tokens, Bearer tokens, private keys, AWS keys, GitHub tokens, Slack tokens, and OpenAI-style keys. High-entropy tokens (>24 chars, entropy >= 3.5) are also redacted.

## `.env` handling

By default, `.env` files are excluded from `git diff` capture. You can opt in by setting `redaction.allow_dotenv: true` in config.

## `.gitignore` safety

`agentrail init` and `agentrail capture` automatically append `.handoff/` to `.gitignore` if missing. Use `--skip-gitignore` to disable this.

## Reporting vulnerabilities

If you discover a security issue, please open a private advisory on GitHub or contact the maintainers directly before public disclosure.
