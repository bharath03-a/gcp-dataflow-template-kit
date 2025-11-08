"""CLI tool for creating new Dataflow projects from the template."""

import shutil
from pathlib import Path

import click


@click.group()
def cli():
    """Dataflow Template CLI - Create and manage Dataflow projects."""
    pass


@cli.command()
@click.argument("target_dir", type=click.Path())
@click.option("--name", help="Project name")
def create(target_dir, name):
    """Create a new Dataflow project from the template.

    TARGET_DIR: Directory where the project will be created
    """
    template_dir = Path(__file__).parent.parent / "template_files"
    target_path = Path(target_dir).resolve()

    if not template_dir.exists():
        click.echo(f"❌ Template directory not found at {template_dir}", err=True)
        return

    if target_path.exists() and any(target_path.iterdir()):
        click.echo(f"❌ Target directory {target_path} is not empty", err=True)
        return

    click.echo(f"Creating Dataflow project at: {target_path}")

    # Copy template files
    shutil.copytree(template_dir, target_path)

    click.echo("Dataflow project created successfully!")
    click.echo("\nNext steps:")
    click.echo(f"  cd {target_path}")
    click.echo("  uv sync")
    click.echo("  python -m dataflow_starter_kit.pipeline --input=1 --runner=DirectRunner")


@cli.command()
def run_template():
    """Run the Dataflow template locally for testing."""
    template_dir = Path(__file__).parent.parent / "template_files"
    pipeline_py = template_dir / "dataflow_starter_kit" / "pipeline.py"

    if not pipeline_py.exists():
        click.echo(f"❌ Pipeline not found at {pipeline_py}", err=True)
        return

    click.echo("Running template pipeline...")
    import subprocess

    subprocess.run(
        ["python", "-m", "dataflow_starter_kit.pipeline", "--input=1", "--runner=DirectRunner"],
        cwd=template_dir,
    )


if __name__ == "__main__":
    cli()
