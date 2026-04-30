# Epics

## Epic 1: Project Scaffold
- [x] Convert repository to `src/agentrail` package layout
- [x] Add CLI entrypoint and dependency configuration
- [x] Add implementation tracking and validation tooling
- Security: none identified

## Epic 2: Core Capture Pipeline
- [x] Implement config and path resolution
- [x] Implement git state capture and artifact writing
- [x] Implement persisted handoff schema and deterministic summary generation
- Security: none identified

## Epic 3: Cross-Agent Adapters
- [x] Implement adapter registry and base interfaces
- [x] Implement Codex source discovery and transcript excerpting
- [x] Implement Gemini and Codex target prompt generation and launch fallback behavior
- Security: none identified

## Epic 4: Validation and Release Hygiene
- [x] Add pytest coverage for core flows and edge cases
- [x] Run lint and tests
- [x] Create focused commits and milestone tags
- Security: none identified

## Epic 5: Public Packaging and Distribution
- [x] Add Apache 2.0 licensing, contributor terms, and release documentation
- [x] Add standalone binary build support for macOS distribution
- [x] Add GitHub Actions for CI, tagged releases, and Homebrew tap updates
- [x] Validate packaging artifacts and document release operations
- [x] Add automated release-note configuration and commit naming guidance
- Security: none identified

## Epic 6: Ongoing Improvements and New Adapters
- [x] Implement Claude Code (claude) adapter and prompt renderer
- [x] Implement OpenCode (opencode) adapter and prompt renderer
- [x] Improve transcript extraction and handoff fidelity
- [x] Polish CLI UX with colored output and better status formatting
- [x] Increase test coverage for CLI flows and new adapters
- [x] Fix Ruff formatting/import regressions in follow-up edits
- Security: none identified

---

# v0.2.0 Roadmap

## Epic 7: Source Discovery Expansion
Bring parity to source discovery so handoffs work regardless of which agent started the session.

- [x] Add default `sessions_dir` configs for `claude`, `gemini`, and `opencode` in `config.py`
- [x] Implement `discover_sources` for `ClaudeAdapter` using configured sessions directory
- [x] Implement `discover_sources` for `GeminiAdapter` using configured sessions directory
- [x] Implement `discover_sources` for `OpenCodeAdapter` using configured sessions directory
- [x] Implement `extract_excerpt` for `ClaudeAdapter`
- [x] Implement `extract_excerpt` for `GeminiAdapter`
- [x] Implement `extract_excerpt` for `OpenCodeAdapter`
- [x] Add unit tests for each new source discovery path
- [x] Add integration tests for the full discovery-to-prompt flow with non-Codex sources
- Security: CWE-200 (information exposure via transcript paths), CWE-532 (insecure logs if transcripts leak)

## Epic 8: Cross-Platform Distribution
Ship to Linux and Windows users; add PyPI as an alternative install channel.

- [x] Add Linux x86_64 PyInstaller build job to `release.yml`
- [x] Add Linux arm64 PyInstaller build job to `release.yml`
- [x] Add Windows x64 PyInstaller build job to `release.yml`
- [x] Add PyPI publish job to `release.yml` using `python -m build` and `twine`
- [x] Update `ci.yml` to run tests on `macos-latest` and `ubuntu-latest`
- [x] Update `render_homebrew_formula.py` to include Linux bottle URLs/SHAs
- [x] Update `build_release_bundle.py` to accept platform/arch arguments
- [x] Add smoke tests for Linux and Windows artifacts in CI
- [x] Update `pyproject.toml` classifiers and README install instructions
- Security: CWE-494 (downloading untrusted code in release scripts), CWE-1104 (exposure of sensitive build artifacts)

## Epic 9: Security Hardening
Prevent accidental secret leakage through handoff artifacts.

- [x] Add `.gitignore` validation to `init` and `capture` commands
- [x] Auto-append `.handoff/` to `.gitignore` with a `--skip-gitignore` opt-out flag
- [x] Skip `.env` file contents in diff capture unless `redaction.allow_dotenv` is true
- [x] Expand redaction patterns to cover AWS keys, GitHub tokens, and generic base64 secrets
- [x] Add entropy-based secret redaction to diff and staged diff outputs
- [x] Warn when handoff artifacts exceed a size threshold that may include binaries
- [x] Add security-focused test cases for redaction
- Security: CWE-798 (hardcoded credentials in artifacts), CWE-312 (cleartext storage of sensitive info), CAPEC-37

## Epic 10: CLI Polish
Make the CLI scriptable, configurable, and easier to clean up.

- [x] Add `--json` flag to `status` for machine-readable output
- [x] Add `--dry-run` flag to `init` and `capture` that prints what would change without writing
- [x] Add `agentrail config` subcommand with `get`, `set`, and `list` actions
- [x] Add `agentrail clean` command to delete `.handoff/` artifacts
- [ ] Add `--verbose` / `--quiet` global flags to control output level
- [ ] Refactor `_continue_to_target` to reduce duplication across target commands
- [x] Add CLI tests for `--json`, `--dry-run`, `config`, and `clean`
- Security: none identified

## Epic 11: Quality & Observability
Raise the bar for code quality and release confidence.

- [x] Add `mypy` (or `pyright`) to dev dependencies and CI
- [x] Add `pytest-cov` to dev dependencies with a minimum coverage threshold (e.g., 80%)
- [x] Fix or annotate all type errors surfaced by the type checker
- [x] Add binary smoke tests that exercise `--version` and `status` on built artifacts
- [x] Expand CI matrix to test Python 3.11 and 3.12 on both Ubuntu and macOS
- [x] Add a `Makefile` or `justfile` with standard dev commands (`test`, `lint`, `typecheck`, `build`)
- Security: none identified

## Epic 12: Prompt & Context Improvements
Smarter prompt generation that respects context limits and includes relevant project conventions.

- [x] Add per-target approximate token-budget awareness (e.g., 64k for Gemini, 128k for Claude)
- [x] Truncate inline diff intelligently when near budget instead of blunt cutoff
- [x] Add `--include-agents-md` flag to append `AGENTS.md` content to generated prompts
- [x] Add `--include-cursorrules` flag to append `.cursorrules` content to generated prompts
- [x] Summarize large diffs by file when inline would exceed budget
- [ ] Add tests for context-budget truncation logic
- Security: CWE-200 (AGENTS.md may contain internal URLs or names)

## Epic 13: Documentation
Close the gap between README promises and actual usage.

- [x] Rewrite README with concrete `init`, `status`, `capture`, and `continue` examples
- [x] Add `docs/ADAPTER_GUIDE.md` explaining how to register a new adapter
- [x] Add `CHANGELOG.md` with entries for v0.1.0 through v0.2.0
- [x] Update `homebrew-agentrail` README with Linux bottle instructions
- [x] Add `docs/SECURITY.md` summarizing redaction behavior and secret-leak prevention
- Security: none identified
