import typer

from dev_cli import project, vm

app = typer.Typer(
    help="dev — local VM and project manager",
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
)

app.add_typer(vm.app, name="vm", help="Manage the Lima development VM  [run on macOS]")
app.add_typer(
    project.app, name="project", help="Manage project containers        [run inside VM]"
)

if __name__ == "__main__":
    app()
