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
- Security: none identified
