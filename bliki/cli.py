from __future__ import annotations

import datetime
from pathlib import Path

import click

from bliki.builder import build_site
from bliki.config import SiteConfig, load_config
from bliki.models import slugify


def _site_options(f):
    """Shared Click options for commands that need the four site path settings."""
    f = click.option(
        "--config", "-c",
        default="bliki.yaml",
        type=click.Path(),
        help="Site config file.",
        show_default=True,
    )(f)
    f = click.option(
        "--output", "-o",
        default="output",
        type=click.Path(),
        help="Output directory.",
        show_default=True,
    )(f)
    f = click.option(
        "--templates",
        default="templates",
        type=click.Path(),
        help="Templates directory.",
        show_default=True,
    )(f)
    f = click.option(
        "--content",
        default="content",
        type=click.Path(),
        help="Content directory.",
        show_default=True,
    )(f)
    return f


@click.group()
def cli():
    """Bliki -- a blog with wiki features."""


@cli.command()
@click.option("--drafts", is_flag=True, help="Include draft posts.")
@_site_options
def build(drafts, content, templates, output, config):
    """Build the site to static HTML."""
    site_config = _load_config_or_default(config)
    build_site(
        content_dir=Path(content),
        output_dir=Path(output),
        templates_dir=Path(templates),
        include_drafts=drafts,
        config=site_config,
    )
    click.echo(f"Built to {output}/")


@cli.command()
@click.option("--drafts", is_flag=True, help="Include draft posts.")
@click.option("--port", "-p", default=8000, help="Port for dev server.", show_default=True)
@_site_options
def serve(drafts, port, content, templates, output, config):
    """Build and serve with live reload."""
    from livereload import Server

    content_dir = Path(content)
    templates_dir = Path(templates)
    output_dir = Path(output)

    def rebuild():
        # Re-read config on every rebuild so changes to bliki.yaml are picked up.
        site_config = _load_config_or_default(config)
        build_site(
            content_dir=content_dir,
            output_dir=output_dir,
            templates_dir=templates_dir,
            include_drafts=drafts,
            config=site_config,
        )

    rebuild()

    server = Server()
    server.watch(str(content_dir), rebuild)
    server.watch(str(templates_dir), rebuild)
    server.watch(config, rebuild)
    server.serve(root=str(output_dir), port=port)


@cli.group()
def new():
    """Scaffold new content."""


@new.command("post")
@click.argument("title")
@click.option(
    "--content",
    default="content",
    type=click.Path(),
    help="Content directory.",
    show_default=True,
)
def new_post(title, content):
    """Create a new blog post."""
    today = datetime.date.today().isoformat()
    slug = slugify(title)
    post_dir = Path(content) / "posts" / f"{today}-{slug}"
    post_dir.mkdir(parents=True, exist_ok=True)
    index_md = post_dir / "index.md"
    index_md.write_text(
        f"---\n"
        f"title: {title}\n"
        f"category: \n"
        f"summary: \n"
        f"date: {today}\n"
        f"draft: true\n"
        f"---\n\n"
    )
    click.echo(f"Created {index_md}")


@new.command("wiki")
@click.argument("title")
@click.option(
    "--content",
    default="content",
    type=click.Path(),
    help="Content directory.",
    show_default=True,
)
def new_wiki(title, content):
    """Create a new wiki page."""
    slug = slugify(title)
    wiki_dir = Path(content) / "wiki" / slug
    wiki_dir.mkdir(parents=True, exist_ok=True)
    index_md = wiki_dir / "index.md"
    index_md.write_text(
        f"---\n"
        f"title: {title}\n"
        f"category: \n"
        f"summary: \n"
        f"---\n\n"
    )
    click.echo(f"Created {index_md}")


def _load_config_or_default(config_path: str) -> SiteConfig:
    """Load site config from file if it exists, otherwise return defaults.

    Args:
        config_path: Path to bliki.yaml (may not exist).

    Returns:
        SiteConfig loaded from file, or default SiteConfig if file not found.
    """
    path = Path(config_path)
    if path.exists():
        return load_config(path)
    return SiteConfig()


if __name__ == "__main__":
    cli()
