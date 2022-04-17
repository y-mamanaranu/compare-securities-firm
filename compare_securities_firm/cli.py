"""CLI functions."""

import click
import rootpath
from selenium.webdriver.chrome.options import Options

from .foreign_etf import Foreign_ETF


@click.group()
def cli():
    """Excute on CLI."""
    pass


@cli.command()
def root():
    """Return root directory of this package."""
    root = rootpath.detect()
    print(root)


@cli.command()
def foreign_etf():
    """Update foreign ETF data."""
    options = Options()

    obj = Foreign_ETF()
    obj.upate(options=options)
    obj.update_json()
