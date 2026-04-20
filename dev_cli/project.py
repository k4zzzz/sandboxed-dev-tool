"""
dev project  —  Podman project lifecycle commands.
Run these inside the Lima VM, not on macOS.
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(no_args_is_help=True)
console = Console()

TEMPLATES_REPO = "https://github.com/k4zzz/dev-templates"
TEMPLATES_DIR_NAME = "templates"  # subdirectory inside the repo


# ── Helpers ───────────────────────────────────────────────────────────────────


def _project_name(project_path: Path) -> str:
    """Derive the compose project name from the directory name."""
    return project_path.name


def _run(
    cmd: list[str], cwd: Path | None = None, check: bool = True
) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)


def _compose_up(project_path: Path) -> None:
    result = subprocess.run(
        ["podman", "compose", "up", "-d", "--build"],
        cwd=project_path,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        console.print(f"[red]podman compose up failed:[/red]\n{result.stderr}")
        raise typer.Exit(1)


def _compose_down(project_path: Path, volumes: bool = False) -> None:
    cmd = ["podman", "compose", "down"]
    if volumes:
        cmd.append("--volumes")
    subprocess.run(cmd, cwd=project_path, check=False, capture_output=True)


def _find_container(project_path: Path) -> str | None:
    """
    Return the first container ID belonging to this compose project.
    Podman compose sets the label com.docker.compose.project=<dir-name>.
    """
    project_name = _project_name(project_path)
    result = subprocess.run(
        [
            "podman",
            "ps",
            "-q",
            "--filter",
            f"label=com.docker.compose.project={project_name}",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    ids = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return ids[0] if ids else None


def _list_templates(tmp_repo: Path) -> list[str]:
    tdir = tmp_repo / TEMPLATES_DIR_NAME
    if not tdir.exists():
        return []
    return [d.name for d in sorted(tdir.iterdir()) if d.is_dir()]


# ── Commands ──────────────────────────────────────────────────────────────────


@app.command()
def new(
    path: str = typer.Argument(..., help="Directory to create the project in"),
    template: str = typer.Option(..., "--template", "-t", help="Template name"),
) -> None:
    """Create a new project from a template and start its containers."""
    project_path = Path(path).resolve()

    if project_path.exists():
        console.print(f"[red]Path already exists:[/red] {project_path}")
        raise typer.Exit(1)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        console.print(f"  Fetching templates from [cyan]{TEMPLATES_REPO}[/cyan]...")
        subprocess.run(
            ["git", "clone", "--depth=1", TEMPLATES_REPO, str(tmp_path)],
            check=True,
            capture_output=True,
        )

        template_path = tmp_path / TEMPLATES_DIR_NAME / template
        if not template_path.exists():
            available = _list_templates(tmp_path)
            console.print(f"[red]Template '{template}' not found.[/red]")
            if available:
                console.print(f"  Available: {', '.join(available)}")
            raise typer.Exit(1)

        project_path.mkdir(parents=True)
        shutil.copytree(str(template_path), str(project_path), dirs_exist_ok=True)

    console.print(f"  Created project at [bold]{project_path}[/bold]")
    console.print("  Starting containers...")
    _compose_up(project_path)
    console.print(f"  [green]✓ '{project_path.name}' is running.[/green]\n")


@app.command()
def shell(
    path: str = typer.Argument(..., help="Project directory path"),
) -> None:
    """Open an interactive shell inside the project's running container."""
    project_path = Path(path).resolve()

    if not project_path.exists():
        console.print(f"[red]Path not found:[/red] {project_path}")
        raise typer.Exit(1)

    container_id = _find_container(project_path)
    if not container_id:
        console.print(
            f"[red]No running container found for '{project_path.name}'.[/red]\n"
            f"  Start it first with:  dev project start {path}"
        )
        raise typer.Exit(1)

    # exec replaces the current process — terminal behaves natively
    os.execvp("podman", ["podman", "exec", "-it", container_id, "/bin/bash"])


@app.command(name="list")
def list_projects() -> None:
    """List all running project containers."""
    result = subprocess.run(
        [
            "podman",
            "ps",
            "--filter",
            "label=com.docker.compose.project",
            "--format",
            "{{.Names}}\t{{.Status}}\t{{.Image}}\t{{.Labels}}",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    lines = [l for l in result.stdout.splitlines() if l.strip()]
    if not lines:
        console.print("  No running project containers.")
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("Container")
    table.add_column("Status")
    table.add_column("Image")

    for line in lines:
        parts = line.split("\t")
        name = parts[0] if len(parts) > 0 else ""
        status = parts[1] if len(parts) > 1 else ""
        image = parts[2] if len(parts) > 2 else ""
        table.add_row(name, status, image)

    console.print(table)


@app.command()
def start(
    path: str = typer.Argument(..., help="Project directory path"),
) -> None:
    """Start a stopped project's containers."""
    project_path = Path(path).resolve()

    if not project_path.exists():
        console.print(f"[red]Path not found:[/red] {project_path}")
        raise typer.Exit(1)

    console.print(f"  Starting [bold]{project_path.name!r}[/bold]...")
    _compose_up(project_path)
    console.print(f"  [green]✓ '{project_path.name}' started.[/green]\n")


@app.command()
def stop(
    path: str = typer.Argument(..., help="Project directory path"),
) -> None:
    """Stop a project's containers (preserves data)."""
    project_path = Path(path).resolve()

    if not project_path.exists():
        console.print(f"[red]Path not found:[/red] {project_path}")
        raise typer.Exit(1)

    console.print(f"  Stopping [bold]{project_path.name!r}[/bold]...")
    _compose_down(project_path)
    console.print(f"  [green]✓ '{project_path.name}' stopped.[/green]\n")


@app.command()
def delete(
    path: str = typer.Argument(..., help="Project directory path"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
) -> None:
    """Stop containers, remove volumes, and delete the project directory."""
    project_path = Path(path).resolve()

    if not project_path.exists():
        console.print(f"[red]Path not found:[/red] {project_path}")
        raise typer.Exit(1)

    if not yes:
        typer.confirm(
            f"  Delete '{project_path.name}' and all its data?",
            abort=True,
        )

    console.print(f"  Stopping and removing containers...")
    _compose_down(project_path, volumes=True)
    console.print(f"  Removing directory...")
    shutil.rmtree(project_path, ignore_errors=True)
    console.print(f"  [green]✓ '{project_path.name}' deleted.[/green]\n")
