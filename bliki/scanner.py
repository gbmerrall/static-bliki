from __future__ import annotations

import datetime
import logging
from pathlib import Path

import frontmatter

from bliki.models import Page, PageType

logger = logging.getLogger(__name__)


def scan_content(
    content_dir: Path,
    include_drafts: bool = False,
) -> list[Page]:
    """Scan content directory and return a list of Page objects.

    Args:
        content_dir: Path to the content directory containing posts/ and wiki/ subdirs.
        include_drafts: If True, include pages marked as draft.

    Returns:
        List of Page objects parsed from the content directory.
    """
    pages: list[Page] = []

    posts_dir = content_dir / "posts"
    wiki_dir = content_dir / "wiki"

    if posts_dir.exists():
        for page_dir in sorted(posts_dir.iterdir()):
            page = _load_page(page_dir, PageType.POST)
            if page:
                pages.append(page)

    if wiki_dir.exists():
        for page_dir in sorted(wiki_dir.iterdir()):
            page = _load_page(page_dir, PageType.WIKI)
            if page:
                pages.append(page)

    if not include_drafts:
        pages = [p for p in pages if not p.draft]

    return pages


def _load_page(page_dir: Path, page_type: PageType) -> Page | None:
    """Load a single page from a directory containing index.md.

    Args:
        page_dir: Directory containing index.md and optional assets.
        page_type: Whether this is a POST or WIKI page.

    Returns:
        Page object, or None if no index.md found.
    """
    index_file = page_dir / "index.md"
    if not index_file.exists():
        logger.debug(f"Skipping {page_dir.name}: no index.md found")
        return None

    post = frontmatter.load(index_file)

    date = post.get("date")
    if isinstance(date, str):
        date = datetime.date.fromisoformat(date)
    elif isinstance(date, datetime.datetime):
        date = date.date()

    return Page(
        title=post.get("title", page_dir.name),
        slug=page_dir.name,
        page_type=page_type,
        source_dir=page_dir,
        content_md=post.content,
        category=post.get("category", ""),
        summary=post.get("summary", ""),
        date=date,
        draft=post.get("draft", False),
    )
