from __future__ import annotations

import logging
import re

from bliki.models import Page

logger = logging.getLogger(__name__)

# Single source of truth for what counts as a wiki link. Group 1 is the target
# title; group 2 (optional) is the display text. The renderer imports this same
# pattern so that link rendering and backlink extraction always agree.
WIKI_LINK_PATTERN = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")


def extract_wiki_links(text: str) -> list[str]:
    """Extract wiki link targets from markdown text.

    Parses [[Page Name]] and [[Page Name|display text]] patterns, returning
    the target page name for each.

    Args:
        text: Markdown text to scan.

    Returns:
        List of page name targets found in the text.
    """
    return [target.strip() for target, _display in WIKI_LINK_PATTERN.findall(text)]


class PageRegistry:
    """Registry of all pages, enabling title-based lookup for wiki link resolution."""

    def __init__(self, pages: list[Page]) -> None:
        self._by_title: dict[str, Page] = {}
        for page in pages:
            self._by_title[page.title.lower()] = page

    def resolve(self, title: str) -> str | None:
        """Resolve a page title to its URL.

        Args:
            title: The page title to look up (case-insensitive).

        Returns:
            The URL string, or None if no matching page exists.
        """
        page = self._by_title.get(title.lower())
        return page.url if page else None

    def get_page(self, title: str) -> Page | None:
        """Look up a Page by title.

        Args:
            title: The page title to look up (case-insensitive).

        Returns:
            The Page object, or None if not found.
        """
        return self._by_title.get(title.lower())


def build_backlinks(pages: list[Page]) -> dict[str, list[Page]]:
    """Build a backlinks map: target title -> list of source pages that link to it.

    Args:
        pages: All pages to scan for outgoing wiki links.

    Returns:
        Dict mapping page titles to list of pages that link to them.
    """
    backlinks: dict[str, list[Page]] = {}
    seen_ids: dict[str, set[int]] = {}
    for page in pages:
        for target in extract_wiki_links(page.content_md):
            key = target.lower()
            ids = seen_ids.setdefault(key, set())
            # A page that links the same target more than once is a single backlink.
            if id(page) not in ids:
                ids.add(id(page))
                backlinks.setdefault(key, []).append(page)
    return backlinks
