"""CLI entrypoint for agentrail."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import typer

from agentrail import __version__

if TYPE_CHECKING:
    from agentrail.agent_registry import AgentRegistry
    from agentrail.config import UserConfig
    from agentrail.models import SourceDiscoveryResult

app = typer.Typer(
    add_completion=False,
    help="Portable coding-agent handoff CLI.",
)
continue_app = typer.Typer(help="Generate target-specific continuation context.")
app.add_typer(continue_app, name="continue")


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
def init() -> None:
    """Create local handoff state and capture current project context."""
    result = _capture_pipeline(Path.cwd(), include_transcript=True)
    typer.secho(f"Initialized handoff state in {result['handoff_dir']}", fg=typer.colors.GREEN)
    for warning in result["warnings"]:
        typer.secho(f"warning: {warning.message}", fg=typer.colors.YELLOW)


@app.command()
def capture() -> None:
    """Refresh handoff artifacts for the current repository."""
    result = _capture_pipeline(Path.cwd(), include_transcript=True)
    typer.secho(f"Refreshed handoff state in {result['handoff_dir']}", fg=typer.colors.GREEN)
    for warning in result["warnings"]:
        typer.secho(f"warning: {warning.message}", fg=typer.colors.YELLOW)


@app.command()
def status() -> None:
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
    
    typer.secho("Project Status", fg=typer.colors.CYAN, bold=True)
    typer.echo(f"  Repo root: {typer.style(str(git.repo_root), fg=typer.colors.BRIGHT_WHITE)}")
    typer.echo(f"  Branch:    {typer.style(git.branch or 'DETACHED', fg=typer.colors.MAGENTA)}")
    typer.echo(f"  HEAD:      {typer.style(git.head or 'No commits yet', fg=typer.colors.YELLOW)}")
    
    dirty_color = typer.colors.RED if git.dirty else typer.colors.GREEN
    typer.echo(f"  Dirty:     {typer.style('yes' if git.dirty else 'no', fg=dirty_color)}")
    
    typer.echo(f"  Changes:   {len(files.changed_files)} changed, {len(files.untracked_files)} untracked")
    
    handoff_state = "present" if paths.handoff_dir.exists() else "missing"
    handoff_color = typer.colors.GREEN if paths.handoff_dir.exists() else typer.colors.RED
    typer.echo(f"  Handoff:   {typer.style(handoff_state, fg=handoff_color)} ({paths.handoff_dir})")
    
    typer.echo(f"  Config:    {config_path}")
    
    typer.secho("\nDetected source agents:", bold=True)
    if discoveries:
        for discovery in discoveries:
            selected = str(discovery.selected_session) if discovery.selected_session else "none"
            typer.echo(f"  - {typer.style(discovery.adapter_name, fg=typer.colors.CYAN)}: {selected}")
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
) -> None:
    _continue_to_target("gemini", print_prompt, no_launch, include_transcript, source)


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
) -> None:
    _continue_to_target("codex", print_prompt, no_launch, include_transcript, source)


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
) -> None:
    _continue_to_target("claude", print_prompt, no_launch, include_transcript, source)


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
) -> None:
    _continue_to_target("opencode", print_prompt, no_launch, include_transcript, source)



def _continue_to_target(
    target: str,
    print_prompt: bool,
    no_launch: bool,
    include_transcript: bool,
    source: str | None,
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
        adapter = result["registry"].get_target(target)
        context = HandoffContext(
            target=target,
            project_name=result["git"].repo_root.name,
            git=result["git"],
            files=result["files"],
            summary_markdown=result["summary_markdown"],
            source_discoveries=result["discoveries"],
            selected_source=result["selected_discovery"],
            transcript_excerpt=result["transcript_excerpt"],
            diff_path=result["handoff_dir"] / "diff.patch",
            staged_diff_path=result["handoff_dir"] / "staged.diff.patch",
            handoff_dir=result["handoff_dir"],
            warnings=result["warnings"],
        )
        prompt = adapter.render_prompt(context)
        prompt_path = result["handoff_dir"] / prompt.filename
        prompt_path.write_text(prompt.content, encoding="utf-8")
        write_capture_artifacts(
            result["project_paths"],
            result["git"],
            result["files"],
            result["summary_markdown"],
            result["discoveries"],
            result["transcript_excerpt"],
            result["warnings"],
            prompt_paths={target: str(prompt_path.relative_to(result["git"].repo_root))},
        )
    except AgentrailError as exc:
        raise typer.Exit(code=_exit_with_error(str(exc))) from exc

    if print_prompt:
        typer.echo(prompt.content)
    typer.echo(f"Generated prompt: {prompt_path}")
    if no_launch:
        return
    launch = adapter.discover_launch(result["config"])
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
) -> dict[str, object]:
    from agentrail.agent_registry import AgentRegistry
    from agentrail.config import load_or_create_user_config
    from agentrail.git_state import capture_git_state
    from agentrail.handoff_writer import ensure_handoff_dirs, write_capture_artifacts
    from agentrail.models import WarningRecord
    from agentrail.paths import project_paths
    from agentrail.summary import render_summary

    config, _, _ = load_or_create_user_config()
    git, files = capture_git_state(cwd)
    registry = AgentRegistry()
    project = project_paths(git.repo_root)
    ensure_handoff_dirs(project)
    discoveries = []
    if source_override != "none":
        discoveries = _discover_sources(registry, git.repo_root, config)
    selected = _select_discovery(discoveries, source_override)
    transcript_excerpt = None
    warnings: list[WarningRecord] = []
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
    write_capture_artifacts(
        project,
        git,
        files,
        summary_markdown,
        discoveries,
        transcript_excerpt,
        warnings,
    )
    return {
        "config": config,
        "registry": registry,
        "git": git,
        "files": files,
        "project_paths": project,
        "handoff_dir": project.handoff_dir,
        "discoveries": discoveries,
        "selected_discovery": selected,
        "transcript_excerpt": transcript_excerpt,
        "summary_markdown": summary_markdown,
        "warnings": warnings,
    }



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
