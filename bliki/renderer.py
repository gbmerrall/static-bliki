from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

import markdown

from bliki.links import WIKI_LINK_PATTERN

if TYPE_CHECKING:
    from bliki.links import PageRegistry

logger = logging.getLogger(__name__)


def _resolve_wiki_links(text: str, registry: PageRegistry | None) -> str:
    """Replace [[Target]] and [[Target|display]] wiki links before Markdown conversion.

    Resolution uses WIKI_LINK_PATTERN -- the same pattern backlink extraction uses --
    so any link that produces a backlink also renders as a link, and vice versa.
    Resolved links become Markdown links; unresolved links become anchors flagged
    with class="broken-link" and an href of "#broken:<target>" so the builder can
    warn about them.

    Args:
        text: Markdown source text.
        registry: Page registry for URL resolution. None resolves nothing (every
            link is treated as broken).

    Returns:
        Text with wiki links converted, ready for Markdown conversion.
    """
    def replace(match: re.Match) -> str:
        target = match.group(1).strip()
        display = (match.group(2) or match.group(1)).strip()
        url = registry.resolve(target) if registry else None
        if url:
            return f"[{display}]({url})"
        return f'<a class="broken-link" href="#broken:{target}">{display}</a>'

    return WIKI_LINK_PATTERN.sub(replace, text)


class Renderer:
    """Markdown renderer that reuses a single Markdown instance across pages.

    Create one Renderer per build (with the build's PageRegistry), then call
    render() for each page. The Markdown instance is reset between calls so
    extension state (e.g. TOC) does not bleed across pages.
    """

    def __init__(self, registry: PageRegistry | None = None) -> None:
        self._registry = registry
        self._md = self._make_md()

    def _make_md(self) -> markdown.Markdown:
        extensions = [
            "fenced_code",
            "codehilite",
            "tables",
            "toc",
        ]
        extension_configs = {
            "codehilite": {
                "css_class": "highlight",
                "guess_lang": False,
            },
            "toc": {
                "permalink": True,
            },
        }
        return markdown.Markdown(
            extensions=extensions,
            extension_configs=extension_configs,
        )

    def render(self, text: str) -> tuple[str, str]:
        """Render markdown text to HTML with wiki link support.

        Args:
            text: Markdown source text.

        Returns:
            Tuple of (content_html, toc_html).
        """
        self._md.reset()
        text = _resolve_wiki_links(text, self._registry)
        html = self._md.convert(text)
        toc = getattr(self._md, "toc", "")
        return html, toc


def render_markdown(
    text: str,
    registry: PageRegistry | None = None,
) -> tuple[str, str]:
    """Render markdown text to HTML with wiki link support.

    Convenience wrapper that creates a one-shot Renderer. For building many
    pages in a single pass, create a Renderer directly and call render() to
    avoid re-initialising the Markdown instance on every page.

    Args:
        text: Markdown source text.
        registry: Optional PageRegistry for resolving [[wiki links]].

    Returns:
        Tuple of (content_html, toc_html).
    """
    return Renderer(registry).render(text)
