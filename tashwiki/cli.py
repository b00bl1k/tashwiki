import logging

import click

from tashwiki import __version__
from tashwiki.config import Config
from tashwiki.builder import build as build_site

logger = logging.getLogger()


@click.group("tashwiki")
@click.option(
    "--config",
    type=click.Path(exists=True),
    default="config.cfg",
    help="Path to the configuration file."
)
@click.pass_context
def cli(ctx, config):
    logging.basicConfig(format="%(message)s", level=logging.INFO)
    logger.info(f"TashWiki v{__version__}")
    ctx.obj = {
        "config": Config.from_file(config),
    }


@cli.command()
@click.pass_context
def build(ctx):
    """Build the website."""
    config = ctx.obj["config"]
    build_site(config)


@cli.command()
@click.option("--reload", is_flag=True, help="Enable automatic reloading.")
@click.option("--port", type=int, default=8080, help="Webserver port.")
@click.pass_context
def serve(ctx, reload, port):
    """Run development web server"""
    # TODO use livereload to run dev server
    pass


def main():
    cli()
