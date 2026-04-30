# Adapter Authoring Guide

`agentrail` uses an adapter pattern to support different coding agents as both sources (where a session started) and targets (where it continues).

## Adapter interface

Every adapter implements `AgentAdapter` (see `src/agentrail/adapters/base.py`):

```python
class AgentAdapter(Protocol):
    name: str

    def discover_sources(self, repo_root: Path, config: UserConfig) -> SourceDiscoveryResult | None: ...
    def extract_excerpt(self, discovery: SourceDiscoveryResult, repo_root: Path, config: UserConfig) -> TranscriptExcerpt | None: ...
    def render_prompt(self, context: HandoffContext) -> PromptArtifact: ...
    def discover_launch(self, config: UserConfig) -> LaunchSpec | None: ...
    def launch(self, prompt_path: Path, prompt_text: str, spec: LaunchSpec | None) -> LaunchResult: ...
```

## Registering a new adapter

1. Create `src/agentrail/adapters/<name>.py`.
2. Implement the adapter class.
3. Add it to `AgentRegistry` in `src/agentrail/agent_registry.py`.
4. Add a default config entry in `src/agentrail/config.py` if applicable.
5. Add the `continue` subcommand in `src/agentrail/cli.py`.
6. Write tests in `tests/test_new_adapters.py` or a new file.

## Source discovery

If the agent stores local session files, implement `discover_sources` using `discover_file_sources` from `adapters/_file_source.py`.

If the agent is cloud-only or stateless, return `None`.

## Prompt rendering

Each target should have a dedicated prompt module under `src/agentrail/prompt/<name>.py`. Reuse `render_common_sections(context)` for consistent formatting.

## Example

See `src/agentrail/adapters/claude.py` for a minimal target-only adapter, or `src/agentrail/adapters/codex.py` for a full source+target adapter.
