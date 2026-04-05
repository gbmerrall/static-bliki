from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

import markdown
from markdown.extensions.wikilinks import WikiLinkExtension

if TYPE_CHECKING:
    from bliki.links import PageRegistry

logger = logging.getLogger(__name__)

_DISPLAY_LINK_PATTERN = re.compile(r"\[\[([^\]|]+)\|([^\]]+)\]\]")


def _make_url_builder(registry: PageRegistry | None):
    """Create a URL builder function for the wikilinks extension.

    Args:
        registry: Page registry for resolving titles to URLs.

    Returns:
        Callable that takes (label, base, end) and returns a URL string.
    """
    def build_url(label: str, _base: str, _end: str) -> str:
        if registry:
            url = registry.resolve(label)
            if url:
                return url
        # Return a placeholder for broken links -- CSS class added via post-processing
        return f"#broken:{label}"

    return build_url


def _preprocess_display_links(text: str, registry: PageRegistry | None) -> str:
    """Replace [[Page|display text]] with markdown links before rendering.

    The wikilinks extension doesn't support display text syntax, so we
    pre-process these patterns into standard markdown links.

    Args:
        text: Markdown source text.
        registry: Page registry for URL resolution.

    Returns:
        Text with display-text wiki links converted to markdown links.
    """
    def replace(match: re.Match) -> str:
        target = match.group(1).strip()
        display = match.group(2).strip()
        if registry:
            url = registry.resolve(target)
            if url:
                return f"[{display}]({url})"
        return f'<a href="#broken:{target}">{display}</a>'

    return _DISPLAY_LINK_PATTERN.sub(replace, text)


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
            WikiLinkExtension(
                base_url="",
                end_url="",
                build_url=_make_url_builder(self._registry),
            ),
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
        text = _preprocess_display_links(text, self._registry)
        html = self._md.convert(text)
        toc = getattr(self._md, "toc", "")
        # Post-process broken links: add CSS class.
        # The wikilinks extension generates class="wikilink" on its anchors, so merge
        # broken-link into that attribute rather than emitting a duplicate class attr.
        html = html.replace(
            'class="wikilink" href="#broken:',
            'class="wikilink broken-link" href="#broken:',
        )
        # Display-text broken links (from _preprocess_display_links) have no class attr.
        html = html.replace('<a href="#broken:', '<a class="broken-link" href="#broken:')
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
