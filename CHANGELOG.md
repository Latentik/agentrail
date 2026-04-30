# Changelog

## v0.2.0 (unreleased)

### Features

- **Source discovery parity**: Claude, Gemini, and OpenCode adapters now support source discovery and transcript excerpt extraction, matching Codex.
- **Cross-platform releases**: Linux x86_64, Linux arm64, and Windows x64 binaries are now built and attached to GitHub Releases. PyPI publishing is also included.
- **Security hardening**:
  - `init` and `capture` auto-append `.handoff/` to `.gitignore`.
  - `.env` file contents are excluded from diff capture by default.
  - Expanded secret redaction patterns (AWS keys, GitHub tokens, Slack tokens, OpenAI keys).
  - Diff and staged diff outputs are redacted before writing.
  - Diff size is capped at 200 KB to avoid oversized artifacts.
- **CLI polish**:
  - `status --json` for machine-readable output.
  - `init --dry-run` and `capture --dry-run` for safe previews.
  - `agentrail config` subcommand with `list`, `get`, and `set`.
  - `agentrail clean` to remove handoff artifacts.
- **Prompt improvements**:
  - Token-budget-aware diff truncation per target.
  - `--include-agents-md` and `--include-cursorrules` flags for `continue` commands.
- **Quality**:
  - MyPy type checking integrated into CI.
  - pytest-cov with 80% minimum coverage gate.
  - CI matrix expanded to macOS and Ubuntu.
  - Makefile with standard dev commands.

### Documentation

- Rewrote README with concrete usage examples.
- Added adapter authoring guide (`docs/ADAPTER_GUIDE.md`).
- Added security notes (`docs/SECURITY.md`).

## v0.1.0

- Initial release with core capture pipeline, Codex/Gemini support, and macOS distribution.
