from __future__ import annotations

import logging
import re
import shutil
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from bliki.config import SiteConfig
from bliki.feed import generate_rss
from bliki.images import process_images, rewrite_img_tags
from bliki.links import PageRegistry, build_backlinks
from bliki.models import Page, PageType, slugify_category
from bliki.renderer import Renderer
from bliki.scanner import scan_content

logger = logging.getLogger(__name__)

# Top-level entries the builder generates. Cleaning is scoped to these so that
# renamed/deleted pages don't leave orphans, while user-managed files in the
# output directory (e.g. CNAME, .nojekyll) are preserved across builds.
GENERATED_OUTPUTS = (
    "posts",
    "wiki",
    "categories",
    "search",
    "static",
    "pagefind",
    "index.html",
    "feed.xml",
)


@dataclass
class Category:
    """Represents a category with its slug and display name."""

    name: str
    slug: str
    pages: list[Page]


def build_site(
    content_dir: Path,
    output_dir: Path,
    templates_dir: Path,
    include_drafts: bool = False,
    config: SiteConfig | None = None,
) -> None:
    """Build the complete static site.

    Args:
        content_dir: Path to content/ directory.
        output_dir: Path to write generated site to.
        templates_dir: Path to Jinja2 templates.
        include_drafts: Whether to include draft posts.
        config: Site configuration. Defaults to SiteConfig() if not provided.
    """
    if config is None:
        config = SiteConfig()

    # Step 0: Remove stale output from a previous build before writing anything.
    _clean_output(output_dir, protected=[content_dir, templates_dir])

    # Step 1: Scan content
    pages = scan_content(content_dir, include_drafts=include_drafts)
    logger.info(f"Scanned {len(pages)} pages")

    # Step 2: Build registry and backlinks
    registry = PageRegistry(pages)
    backlinks_map = build_backlinks(pages)

    # Step 3: Attach backlinks to each target page.
    # Done as a single pass before rendering so all pages have backlinks populated.
    for bl_title, bl_sources in backlinks_map.items():
        target_page = registry.get_page(bl_title)
        if target_page:
            # Use extend so multiple different capitalizations of the same
            # target don't overwrite each other.
            target_page.backlinks.extend(bl_sources)

    # Step 4: Render markdown, process images, and write page HTML in one pass.
    # A single Renderer instance is reused across all pages to avoid reinitialising
    # the Markdown extensions on every call.
    env = Environment(loader=FileSystemLoader(str(templates_dir)), autoescape=True)
    post_template = env.get_template("post.html")
    wiki_template = env.get_template("wiki.html")
    renderer = Renderer(registry)

    for page in pages:
        page.content_html, page.toc_html = renderer.render(page.content_md)
        _warn_broken_links(page)
        out_dir = _page_output_dir(output_dir, page)

        manifest = process_images(page.source_dir, out_dir)
        if manifest:
            page.content_html = rewrite_img_tags(page.content_html, manifest)

        template = post_template if page.page_type == PageType.POST else wiki_template
        (out_dir / "index.html").write_text(template.render(page=page, site=config))

    # Step 5: Render listing pages (indexes, categories, search)
    _render_indexes(env, pages, output_dir, config)

    # Step 6: Copy static assets
    static_src = templates_dir / "static"
    if static_src.exists():
        shutil.copytree(static_src, output_dir / "static", dirs_exist_ok=True)

    # Step 7: Generate RSS feed and search index
    run_pagefind(output_dir)

    feed_xml = generate_rss(
        pages,
        site_name=config.name,
        site_url=config.url,
        site_description=config.description,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "feed.xml").write_text(feed_xml)


def _clean_output(output_dir: Path, protected: list[Path]) -> None:
    """Remove builder-generated entries from a previous build.

    Only the entries in GENERATED_OUTPUTS are removed, so files the user placed
    in the output directory (e.g. CNAME, .nojekyll) survive across builds.

    Args:
        output_dir: Root output directory.
        protected: Source directories that must never be cleaned. If output_dir
            resolves to any of them, cleaning is refused to avoid destroying
            source content.

    Raises:
        ValueError: If output_dir resolves to one of the protected directories.
    """
    if not output_dir.exists():
        return

    resolved_output = output_dir.resolve()
    for protected_dir in protected:
        if resolved_output == protected_dir.resolve():
            raise ValueError(
                f"Refusing to clean output dir '{output_dir}': it resolves to a "
                f"source directory ('{protected_dir}')"
            )

    for name in GENERATED_OUTPUTS:
        target = output_dir / name
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()


def _warn_broken_links(page: Page) -> None:
    """Log a warning for each broken wiki link found in a rendered page.

    Args:
        page: Page whose content_html to inspect.
    """
    broken = re.findall(r'href="#broken:([^"]*)"', page.content_html)
    for title in broken:
        logger.warning(f"Broken wiki link on '{page.title}': [[{title}]]")


def _page_output_dir(output_dir: Path, page: Page) -> Path:
    """Determine and create the output directory for a page.

    Args:
        output_dir: Root output directory.
        page: The page to get output dir for.

    Returns:
        Path to the page's output directory (created if it does not exist).
    """
    url = page.url.strip("/")
    out = output_dir / url
    out.mkdir(parents=True, exist_ok=True)
    return out


def _render_indexes(
    env: Environment, pages: list[Page], output_dir: Path, config: SiteConfig
) -> None:
    """Render listing pages: post index, wiki index, categories, search.

    Args:
        env: Jinja2 environment.
        pages: All pages.
        output_dir: Root output directory.
        config: Site configuration passed to templates as `site`.
    """
    posts = sorted(
        [p for p in pages if p.page_type == PageType.POST and p.date],
        key=lambda p: p.date,
        reverse=True,
    )
    wiki_pages = sorted(
        [p for p in pages if p.page_type == PageType.WIKI],
        key=lambda p: p.title.lower(),
    )

    # Post index (homepage)
    output_dir.mkdir(parents=True, exist_ok=True)
    post_index_tpl = env.get_template("post_index.html")
    (output_dir / "index.html").write_text(post_index_tpl.render(posts=posts, site=config))

    # Wiki index
    wiki_dir = output_dir / "wiki"
    wiki_dir.mkdir(parents=True, exist_ok=True)
    wiki_index_tpl = env.get_template("wiki_index.html")
    (wiki_dir / "index.html").write_text(wiki_index_tpl.render(pages=wiki_pages, site=config))

    # Per-category pages
    categories_map: dict[str, list[Page]] = defaultdict(list)
    for page in pages:
        if page.category:
            categories_map[page.category].append(page)

    categories = [
        Category(name=name, slug=slugify_category(name), pages=cat_pages)
        for name, cat_pages in sorted(categories_map.items())
    ]

    cat_root = output_dir / "categories"
    cat_root.mkdir(parents=True, exist_ok=True)
    cat_index_tpl = env.get_template("category_index.html")
    (cat_root / "index.html").write_text(
        cat_index_tpl.render(categories=categories, site=config)
    )

    cat_tpl = env.get_template("category.html")
    for cat in categories:
        cat_dir = cat_root / cat.slug
        cat_dir.mkdir(parents=True, exist_ok=True)
        (cat_dir / "index.html").write_text(
            cat_tpl.render(category=cat.name, pages=cat.pages, site=config)
        )

    # Search page
    search_dir = output_dir / "search"
    search_dir.mkdir(parents=True, exist_ok=True)
    search_tpl = env.get_template("search.html")
    (search_dir / "index.html").write_text(search_tpl.render(site=config))


def run_pagefind(output_dir: Path) -> None:
    """Run Pagefind to generate a client-side search index.

    Args:
        output_dir: Path to the built site output directory. No-ops if the
            pagefind binary is not found on PATH.
    """
    pagefind = shutil.which("pagefind")
    if not pagefind:
        logger.warning("pagefind not found in PATH -- skipping search index generation")
        return

    result = subprocess.run(
        [pagefind, "--site", str(output_dir)],
        capture_output=True,
        text=True,
        timeout=60,
    )

    if result.returncode != 0:
        logger.error(f"Pagefind failed: {result.stderr}")
    else:
        logger.info("Search index generated")
