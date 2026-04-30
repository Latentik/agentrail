# agentrail

Portable coding-agent handoff CLI.

## Install

### Homebrew (macOS & Linux)

Recommended on macOS and Linux:

```bash
brew tap Latentik/agentrail
brew install agentrail
```

The dedicated Homebrew tap lives in `Latentik/homebrew-agentrail`, which Homebrew addresses as `Latentik/agentrail`.

### PyPI

```bash
pip install agentrail
```

## Usage

### Initialize a project

```bash
agentrail init
```

This creates a `.handoff/` directory in the current Git repository, captures the current Git state, and writes a summary. It also appends `.handoff/` to `.gitignore` automatically.

### Check status

```bash
agentrail status
agentrail status --json   # machine-readable output
```

### Refresh handoff artifacts

```bash
agentrail capture
agentrail capture --dry-run   # preview without writing
```

### Continue with another agent

Generate a continuation prompt for your target agent:

```bash
agentrail continue claude
agentrail continue gemini --print --no-launch
agentrail continue codex --from claude
```

Include project conventions:

```bash
agentrail continue claude --include-agents-md --include-cursorrules
```

### Manage configuration

```bash
agentrail config list
agentrail config get agents.claude.binary
agentrail config set agents.claude.binary claude-code
```

### Clean up

```bash
agentrail clean   # removes .handoff/
```

## Licensing and contributions

- Source code is licensed under Apache 2.0.
- The project is maintained by Latentik.
- Contributors agree to the repository contribution terms in [CONTRIBUTING.md](CONTRIBUTING.md) and [CLA.md](CLA.md).
- Project branding and trademarks remain controlled by Latentik.

## Releases

Public releases use semantic version tags such as `v0.1.0`.
See [RELEASE.md](RELEASE.md) for packaging and publishing details.
