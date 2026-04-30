"""CLI entrypoint for agentrail."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import typer

from agentrail import __version__

if TYPE_CHECKING:
    from agentrail.agent_registry import AgentRegistry
    from agentrail.config import UserConfig
    from agentrail.models import (
        FileSnapshot,
        GitSnapshot,
        SourceDiscoveryResult,
        TranscriptExcerpt,
        WarningRecord,
    )
    from agentrail.paths import ProjectPaths


@dataclass(slots=True)
class _CaptureResult:
    config: UserConfig
    registry: AgentRegistry
    git: GitSnapshot
    files: FileSnapshot
    project_paths: ProjectPaths
    handoff_dir: Path
    discoveries: list[SourceDiscoveryResult]
    selected_discovery: SourceDiscoveryResult | None
    transcript_excerpt: TranscriptExcerpt | None
    summary_markdown: str
    warnings: list[WarningRecord]

app = typer.Typer(
    add_completion=False,
    help="Portable coding-agent handoff CLI.",
)
continue_app = typer.Typer(help="Generate target-specific continuation context.")
app.add_typer(continue_app, name="continue")
config_app = typer.Typer(help="Manage agentrail configuration.")
app.add_typer(config_app, name="config")


@app.callback(invoke_without_command=True)
def main(
    version: bool = typer.Option(
        False,
        "--version",
        help="Print the agentrail version and exit.",
        is_eager=True,
    )
) -> None:
    """Agentrail CLI."""
    if version:
        typer.echo(__version__)
        raise typer.Exit()


@app.command()
def init(
    skip_gitignore: bool = typer.Option(
        False,
        "--skip-gitignore",
        help="Do not auto-append .handoff/ to .gitignore.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Print what would be written without creating artifacts.",
    ),
) -> None:
    """Create local handoff state and capture current project context."""
    result = _capture_pipeline(
        Path.cwd(), include_transcript=True, skip_gitignore=skip_gitignore, dry_run=dry_run
    )
    action = "Would initialize" if dry_run else "Initialized"
    typer.secho(f"{action} handoff state in {result.handoff_dir}", fg=typer.colors.GREEN)
    for warning in result.warnings:
        typer.secho(f"warning: {warning.message}", fg=typer.colors.YELLOW)


@app.command()
def capture(
    skip_gitignore: bool = typer.Option(
        False,
        "--skip-gitignore",
        help="Do not auto-append .handoff/ to .gitignore.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Print what would be written without creating artifacts.",
    ),
) -> None:
    """Refresh handoff artifacts for the current repository."""
    result = _capture_pipeline(
        Path.cwd(), include_transcript=True, skip_gitignore=skip_gitignore, dry_run=dry_run
    )
    action = "Would refresh" if dry_run else "Refreshed"
    typer.secho(f"{action} handoff state in {result.handoff_dir}", fg=typer.colors.GREEN)
    for warning in result.warnings:
        typer.secho(f"warning: {warning.message}", fg=typer.colors.YELLOW)


@app.command()
def clean() -> None:
    """Remove local handoff artifacts (.handoff/)."""
    from agentrail.errors import AgentrailError
    from agentrail.git_state import capture_git_state
    from agentrail.paths import project_paths

    try:
        git, _ = capture_git_state(Path.cwd())
    except AgentrailError as exc:
        raise typer.Exit(code=_exit_with_error(str(exc))) from exc

    paths = project_paths(git.repo_root)
    if paths.handoff_dir.exists():
        import shutil

        shutil.rmtree(paths.handoff_dir)
        typer.secho(f"Removed {paths.handoff_dir}", fg=typer.colors.GREEN)
    else:
        typer.secho("No handoff artifacts to remove.", fg=typer.colors.YELLOW)


@config_app.command("list")
def config_list() -> None:
    """Print the current user configuration."""
    from agentrail.config import load_or_create_user_config

    config, config_path, _ = load_or_create_user_config()
    typer.echo(f"Config path: {config_path}")
    typer.echo(config.model_dump_json(indent=2))


@config_app.command("get")
def config_get(key: str) -> None:
    """Get a configuration value by dot-notation key (e.g., agents.claude.binary)."""
    from agentrail.config import load_or_create_user_config

    config, _, _ = load_or_create_user_config()
    data = config.model_dump()
    parts = key.split(".")
    for part in parts:
        if isinstance(data, dict) and part in data:
            data = data[part]
        else:
            raise typer.Exit(code=_exit_with_error(f"Key not found: {key}"))
    typer.echo(json.dumps(data, indent=2) if isinstance(data, (dict, list)) else data)


@config_app.command("set")
def config_set(key: str, value: str) -> None:
    """Set a configuration value by dot-notation key."""
    import json

    from agentrail.config import load_or_create_user_config

    config, config_path, _ = load_or_create_user_config()
    data = config.model_dump()
    parts = key.split(".")
    target = data
    for part in parts[:-1]:
        if part not in target:
            target[part] = {}
        target = target[part]
    try:
        target[parts[-1]] = json.loads(value)
    except json.JSONDecodeError:
        target[parts[-1]] = value
    from agentrail.config import UserConfig

    updated = UserConfig.model_validate(data)
    config_path.write_text(updated.model_dump_json(indent=2) + "\n", encoding="utf-8")
    typer.secho(f"Updated {key}", fg=typer.colors.GREEN)


@app.command()
def status(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output status as JSON.",
    ),
) -> None:
    """Print current repository and handoff status."""
    from agentrail.agent_registry import AgentRegistry
    from agentrail.config import load_or_create_user_config
    from agentrail.errors import AgentrailError
    from agentrail.git_state import capture_git_state
    from agentrail.paths import project_paths

    try:
        config, config_path, _ = load_or_create_user_config()
        git, files = capture_git_state(Path.cwd())
    except AgentrailError as exc:
        raise typer.Exit(code=_exit_with_error(str(exc))) from exc

    registry = AgentRegistry()
    discoveries = _discover_sources(registry, git.repo_root, config)
    paths = project_paths(git.repo_root)

    if json_output:
        import json

        payload = {
            "repo_root": str(git.repo_root),
            "branch": git.branch,
            "head": git.head,
            "dirty": git.dirty,
            "changed_files": files.changed_files,
            "untracked_files": files.untracked_files,
            "handoff_present": paths.handoff_dir.exists(),
            "handoff_dir": str(paths.handoff_dir),
            "config_path": str(config_path),
            "source_agents": [
                {
                    "name": d.adapter_name,
                    "selected": str(d.selected_session) if d.selected_session else None,
                }
                for d in discoveries
            ],
            "targets": {
                target: (
                    "configured" if registry.get_target(target).discover_launch(config)
                    else "not configured"
                )
                for target in registry.supported_targets()
            },
        }
        typer.echo(json.dumps(payload, indent=2))
        return

    typer.secho("Project Status", fg=typer.colors.CYAN, bold=True)
    typer.echo(f"  Repo root: {typer.style(str(git.repo_root), fg=typer.colors.BRIGHT_WHITE)}")
    typer.echo(f"  Branch:    {typer.style(git.branch or 'DETACHED', fg=typer.colors.MAGENTA)}")
    typer.echo(f"  HEAD:      {typer.style(git.head or 'No commits yet', fg=typer.colors.YELLOW)}")

    dirty_color = typer.colors.RED if git.dirty else typer.colors.GREEN
    typer.echo(f"  Dirty:     {typer.style('yes' if git.dirty else 'no', fg=dirty_color)}")

    typer.echo(
        f"  Changes:   {len(files.changed_files)} changed, "
        f"{len(files.untracked_files)} untracked"
    )

    handoff_state = "present" if paths.handoff_dir.exists() else "missing"
    handoff_color = typer.colors.GREEN if paths.handoff_dir.exists() else typer.colors.RED
    typer.echo(f"  Handoff:   {typer.style(handoff_state, fg=handoff_color)} ({paths.handoff_dir})")

    typer.echo(f"  Config:    {config_path}")

    typer.secho("\nDetected source agents:", bold=True)
    if discoveries:
        for discovery in discoveries:
            selected = str(discovery.selected_session) if discovery.selected_session else "none"
            adapter_styled = typer.style(discovery.adapter_name, fg=typer.colors.CYAN)
            typer.echo(f"  - {adapter_styled}: {selected}")
    else:
        typer.echo("  - none")

    typer.secho("\nAvailable targets:", bold=True)
    for target in registry.supported_targets():
        adapter = registry.get_target(target)
        launch = adapter.discover_launch(config)
        available = typer.style("configured", fg=typer.colors.GREEN) if launch else "not configured"
        typer.echo(f"  - {typer.style(target, fg=typer.colors.CYAN)}: {available}")


@continue_app.command("gemini")
def continue_gemini(
    print_prompt: bool = typer.Option(
        False,
        "--print",
        help="Print the generated prompt to stdout.",
    ),
    no_launch: bool = typer.Option(
        False,
        "--no-launch",
        help="Only generate the prompt.",
    ),
    include_transcript: bool = typer.Option(
        True,
        "--include-transcript/--no-transcript",
        help="Include transcript recovery when available.",
    ),
    source: str | None = typer.Option(
        None,
        "--from",
        help="Explicitly choose a source agent or 'none'.",
    ),
    include_agents_md: bool = typer.Option(
        False,
        "--include-agents-md",
        help="Include AGENTS.md content in the prompt.",
    ),
    include_cursorrules: bool = typer.Option(
        False,
        "--include-cursorrules",
        help="Include .cursorrules content in the prompt.",
    ),
) -> None:
    _continue_to_target(
        "gemini", print_prompt, no_launch, include_transcript, source,
        include_agents_md, include_cursorrules,
    )


@continue_app.command("codex")
def continue_codex(
    print_prompt: bool = typer.Option(
        False,
        "--print",
        help="Print the generated prompt to stdout.",
    ),
    no_launch: bool = typer.Option(
        False,
        "--no-launch",
        help="Only generate the prompt.",
    ),
    include_transcript: bool = typer.Option(
        True,
        "--include-transcript/--no-transcript",
        help="Include transcript recovery when available.",
    ),
    source: str | None = typer.Option(
        None,
        "--from",
        help="Explicitly choose a source agent or 'none'.",
    ),
    include_agents_md: bool = typer.Option(
        False,
        "--include-agents-md",
        help="Include AGENTS.md content in the prompt.",
    ),
    include_cursorrules: bool = typer.Option(
        False,
        "--include-cursorrules",
        help="Include .cursorrules content in the prompt.",
    ),
) -> None:
    _continue_to_target(
        "codex", print_prompt, no_launch, include_transcript, source,
        include_agents_md, include_cursorrules,
    )


@continue_app.command("claude")
def continue_claude(
    print_prompt: bool = typer.Option(
        False,
        "--print",
        help="Print the generated prompt to stdout.",
    ),
    no_launch: bool = typer.Option(
        False,
        "--no-launch",
        help="Only generate the prompt.",
    ),
    include_transcript: bool = typer.Option(
        True,
        "--include-transcript/--no-transcript",
        help="Include transcript recovery when available.",
    ),
    source: str | None = typer.Option(
        None,
        "--from",
        help="Explicitly choose a source agent or 'none'.",
    ),
    include_agents_md: bool = typer.Option(
        False,
        "--include-agents-md",
        help="Include AGENTS.md content in the prompt.",
    ),
    include_cursorrules: bool = typer.Option(
        False,
        "--include-cursorrules",
        help="Include .cursorrules content in the prompt.",
    ),
) -> None:
    _continue_to_target(
        "claude", print_prompt, no_launch, include_transcript, source,
        include_agents_md, include_cursorrules,
    )


@continue_app.command("opencode")
def continue_opencode(
    print_prompt: bool = typer.Option(
        False,
        "--print",
        help="Print the generated prompt to stdout.",
    ),
    no_launch: bool = typer.Option(
        False,
        "--no-launch",
        help="Only generate the prompt.",
    ),
    include_transcript: bool = typer.Option(
        True,
        "--include-transcript/--no-transcript",
        help="Include transcript recovery when available.",
    ),
    source: str | None = typer.Option(
        None,
        "--from",
        help="Explicitly choose a source agent or 'none'.",
    ),
    include_agents_md: bool = typer.Option(
        False,
        "--include-agents-md",
        help="Include AGENTS.md content in the prompt.",
    ),
    include_cursorrules: bool = typer.Option(
        False,
        "--include-cursorrules",
        help="Include .cursorrules content in the prompt.",
    ),
) -> None:
    _continue_to_target(
        "opencode", print_prompt, no_launch, include_transcript, source,
        include_agents_md, include_cursorrules,
    )



def _continue_to_target(
    target: str,
    print_prompt: bool,
    no_launch: bool,
    include_transcript: bool,
    source: str | None,
    include_agents_md: bool = False,
    include_cursorrules: bool = False,
) -> None:
    from agentrail.errors import AgentrailError
    from agentrail.handoff_writer import write_capture_artifacts
    from agentrail.models import HandoffContext

    try:
        result = _capture_pipeline(
            Path.cwd(),
            include_transcript=include_transcript,
            source_override=source,
        )
        adapter = result.registry.get_target(target)
        context = HandoffContext(
            target=target,
            project_name=result.git.repo_root.name,
            git=result.git,
            files=result.files,
            summary_markdown=result.summary_markdown,
            source_discoveries=result.discoveries,
            selected_source=result.selected_discovery,
            transcript_excerpt=result.transcript_excerpt,
            diff_path=result.handoff_dir / "diff.patch",
            staged_diff_path=result.handoff_dir / "staged.diff.patch",
            handoff_dir=result.handoff_dir,
            warnings=result.warnings,
            include_agents_md=include_agents_md,
            include_cursorrules=include_cursorrules,
        )
        prompt = adapter.render_prompt(context)
        prompt_path = result.handoff_dir / prompt.filename
        prompt_path.write_text(prompt.content, encoding="utf-8")
        write_capture_artifacts(
            result.project_paths,
            result.git,
            result.files,
            result.summary_markdown,
            result.discoveries,
            result.transcript_excerpt,
            result.warnings,
            prompt_paths={target: str(prompt_path.relative_to(result.git.repo_root))},
        )
    except AgentrailError as exc:
        raise typer.Exit(code=_exit_with_error(str(exc))) from exc

    if print_prompt:
        typer.echo(prompt.content)
    typer.echo(f"Generated prompt: {prompt_path}")
    if no_launch:
        return
    launch = adapter.discover_launch(result.config)
    launch_result = adapter.launch(prompt_path, prompt.content, launch)
    if launch_result.command:
        typer.echo(f"Command: {' '.join(json.dumps(part) for part in launch_result.command)}")
    typer.echo(launch_result.message)
    if launch_result.attempted and not launch_result.launched:
        raise typer.Exit(code=1)



def _capture_pipeline(
    cwd: Path,
    include_transcript: bool,
    source_override: str | None = None,
    skip_gitignore: bool = False,
    dry_run: bool = False,
) -> _CaptureResult:
    from agentrail.agent_registry import AgentRegistry
    from agentrail.config import load_or_create_user_config
    from agentrail.git_state import capture_git_state
    from agentrail.handoff_writer import ensure_handoff_dirs, write_capture_artifacts
    from agentrail.models import WarningRecord
    from agentrail.paths import project_paths
    from agentrail.security import append_gitignore, check_gitignore
    from agentrail.summary import render_summary

    config, _, _ = load_or_create_user_config()
    exclude_dotenv = not config.redaction.allow_dotenv
    git, files = capture_git_state(cwd, exclude_dotenv=exclude_dotenv)
    registry = AgentRegistry()
    project = project_paths(git.repo_root)
    if not dry_run:
        ensure_handoff_dirs(project)
    warnings: list[WarningRecord] = []

    if not skip_gitignore and not dry_run:
        ignored, gitignore_warnings = check_gitignore(git.repo_root)
        warnings.extend(gitignore_warnings)
        if not ignored:
            append_gitignore(git.repo_root)
            warnings.append(
                WarningRecord(
                    code="security.auto_gitignore",
                    message="Added .handoff/ to .gitignore to prevent accidental commits.",
                )
            )

    discoveries = []
    if source_override != "none":
        discoveries = _discover_sources(registry, git.repo_root, config)
    selected = _select_discovery(discoveries, source_override)
    transcript_excerpt = None
    for discovery in discoveries:
        warnings.extend(discovery.warnings)
    if include_transcript and selected:
        adapter = registry.get_target(selected.adapter_name)
        transcript_excerpt = adapter.extract_excerpt(selected, git.repo_root, config)
        if transcript_excerpt:
            warnings.extend(transcript_excerpt.warnings)
    summary_markdown = render_summary(
        git.repo_root.name,
        git,
        files,
        discoveries,
        transcript_excerpt,
        warnings,
    )
    if not dry_run:
        write_capture_artifacts(
            project,
            git,
            files,
            summary_markdown,
            discoveries,
            transcript_excerpt,
            warnings,
            redact=config.redaction.enabled,
        )
    return _CaptureResult(
        config=config,
        registry=registry,
        git=git,
        files=files,
        project_paths=project,
        handoff_dir=project.handoff_dir,
        discoveries=discoveries,
        selected_discovery=selected,
        transcript_excerpt=transcript_excerpt,
        summary_markdown=summary_markdown,
        warnings=warnings,
    )



def _discover_sources(
    registry: AgentRegistry,
    repo_root: Path,
    config: UserConfig,
) -> list[SourceDiscoveryResult]:
    discoveries: list[SourceDiscoveryResult] = []
    for adapter in registry.all_source_adapters():
        discovery = adapter.discover_sources(repo_root, config)
        if discovery:
            discoveries.append(discovery)
    return discoveries



def _select_discovery(
    discoveries: list[SourceDiscoveryResult],
    source_override: str | None,
) -> SourceDiscoveryResult | None:
    if source_override:
        for discovery in discoveries:
            if discovery.adapter_name == source_override:
                return discovery
        return None
    ranked = sorted(
        [item for item in discoveries if item.selected_session],
        key=lambda item: _confidence_rank(
            item.matched_sessions[0].confidence if item.matched_sessions else "low"
        ),
    )
    return ranked[0] if ranked else None



def _confidence_rank(confidence: str) -> int:
    order = {"high": 0, "medium": 1, "low": 2}
    return order.get(confidence, 3)



def _exit_with_error(message: str) -> int:
    typer.secho(f"error: {message}", fg=typer.colors.RED, err=True)
    return 1


if __name__ == "__main__":
    app()
