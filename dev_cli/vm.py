"""
dev vm  —  Lima VM lifecycle commands.
Run these on macOS, not inside the VM.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(no_args_is_help=True)
console = Console()

VM_NAME = "dev"
TEMPLATES_REPO = "https://github.com/k4zzz/dev-templates"
LIMA_YAML_PATH = "lima/dev.yaml"  # path inside the templates repo


# ── Helpers ───────────────────────────────────────────────────────────────────


def _run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a subprocess, streaming output to the terminal."""
    return subprocess.run(cmd, check=check)


def _vm_exists() -> bool:
    result = subprocess.run(
        ["limactl", "list", "--format", "{{.Name}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    return VM_NAME in result.stdout.splitlines()


def _require_limactl() -> None:
    if subprocess.run(["which", "limactl"], capture_output=True).returncode != 0:
        console.print("[red]limactl not found.[/red] Run the install script first.")
        raise typer.Exit(1)


def _fetch_lima_yaml(dest: Path) -> None:
    """Clone the templates repo and copy the Lima YAML to dest."""
    with tempfile.TemporaryDirectory() as tmp:
        console.print(f"  Fetching Lima config from [cyan]{TEMPLATES_REPO}[/cyan]...")
        subprocess.run(
            ["git", "clone", "--depth=1", TEMPLATES_REPO, tmp],
            check=True,
            capture_output=True,
        )
        src = Path(tmp) / LIMA_YAML_PATH
        if not src.exists():
            console.print(
                f"[red]Lima YAML not found at '{LIMA_YAML_PATH}' in templates repo.[/red]"
            )
            raise typer.Exit(1)
        import shutil

        shutil.copy(src, dest)


# ── Commands ──────────────────────────────────────────────────────────────────


@app.command()
def create() -> None:
    """Delete any existing VM and provision a fresh one."""
    _require_limactl()

    if _vm_exists():
        console.print(
            f"  VM [yellow]{VM_NAME!r}[/yellow] already exists — deleting it first..."
        )
        _run(["limactl", "stop", "--force", VM_NAME], check=False)
        _run(["limactl", "delete", "--force", VM_NAME])
        console.print("  Deleted.\n")

    with tempfile.TemporaryDirectory() as tmp:
        lima_yaml = Path(tmp) / "dev.yaml"
        _fetch_lima_yaml(lima_yaml)

        console.print(f"  Creating VM [bold]{VM_NAME!r}[/bold]...")
        _run(["limactl", "create", "--name", VM_NAME, str(lima_yaml)])

        console.print(f"  Starting VM (provisioning may take a few minutes)...")
        _run(["limactl", "start", VM_NAME])

    console.print(f"\n  [green]✓ VM '{VM_NAME}' is ready.[/green]")
    console.print("  Shell in with:  [bold]limactl shell dev[/bold]\n")


@app.command()
def start() -> None:
    """Start the VM."""
    _require_limactl()
    console.print(f"  Starting [bold]{VM_NAME!r}[/bold]...")
    _run(["limactl", "start", VM_NAME])
    console.print(f"  [green]✓ VM '{VM_NAME}' started.[/green]\n")


@app.command()
def stop() -> None:
    """Stop the VM."""
    _require_limactl()
    console.print(f"  Stopping [bold]{VM_NAME!r}[/bold]...")
    _run(["limactl", "stop", VM_NAME])
    console.print(f"  [green]✓ VM '{VM_NAME}' stopped.[/green]\n")


@app.command()
def delete() -> None:
    """Stop and permanently delete the VM."""
    _require_limactl()

    if not _vm_exists():
        console.print(f"  VM [yellow]{VM_NAME!r}[/yellow] does not exist.")
        raise typer.Exit(0)

    console.print(f"  Stopping [bold]{VM_NAME!r}[/bold]...")
    _run(["limactl", "stop", "--force", VM_NAME], check=False)
    console.print(f"  Deleting [bold]{VM_NAME!r}[/bold]...")
    _run(["limactl", "delete", "--force", VM_NAME])
    console.print(f"  [green]✓ VM '{VM_NAME}' deleted.[/green]\n")
