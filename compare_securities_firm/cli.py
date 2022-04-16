"""CLI functions."""

import click
import rootpath


@click.group()
def cli():
    """Excute on CLI."""
    pass


@cli.command()
def root():
    """Return root directory of this package."""
    root = rootpath.detect()
    print(root)
