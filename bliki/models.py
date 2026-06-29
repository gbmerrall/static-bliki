from __future__ import annotations

import datetime
import enum
import re
from dataclasses import dataclass, field
from pathlib import Path

# Leading YYYY-MM-DD- prefix conventionally present on post directory names.
_DATE_PREFIX = re.compile(r"^\d{4}-\d{2}-\d{2}-")


class PageType(enum.Enum):
    POST = "post"
    WIKI = "wiki"


def slugify(text: str) -> str:
    """Convert human-readable text to a URL-safe slug.

    Lowercases, removes characters that are not letters, digits, whitespace or
    hyphens, collapses runs of whitespace and underscores into single hyphens,
    and trims leading/trailing hyphens. Used for both content directory names
    (via the new command) and category URLs so slugs are always formed the same
    way.

    Args:
        text: Human-readable string (a title or category name).

    Returns:
        URL-safe slug. May be empty if text has no slug-able characters.
    """
    slug = text.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug.strip("-")


@dataclass
class Page:
    """Represents a single content page (post or wiki).

    Fields set at construction time (from frontmatter):
        title, slug, page_type, source_dir, content_md, category,
        summary, date, draft

    Fields populated by the builder after construction:
        content_html  -- set by renderer after markdown conversion
        toc_html      -- set by renderer after markdown conversion
        backlinks     -- populated by build_backlinks() before rendering
    """

    title: str
    slug: str
    page_type: PageType
    source_dir: Path
    content_md: str
    category: str = ""
    summary: str = ""
    date: datetime.date | None = None
    draft: bool = False
    content_html: str = ""
    toc_html: str = ""
    backlinks: list[Page] = field(default_factory=list)

    @property
    def category_url(self) -> str:
        """Return the URL path for this page's category, or empty string if none."""
        if not self.category:
            return ""
        return f"/categories/{slugify(self.category)}/"

    @property
    def url(self) -> str:
        """Generate the URL path for this page.

        The frontmatter date is the canonical publish date and drives the
        year/month in a post's URL. Any leading YYYY-MM-DD- prefix on the
        directory name is stripped to form the URL slug, so the directory prefix
        and the frontmatter date do not have to stay in lock-step (editing one
        without the other no longer breaks the build).

        Raises:
            ValueError: If a POST page has no date.
        """
        if self.page_type == PageType.POST:
            if not self.date:
                raise ValueError(f"Post '{self.title}' has no date")
            name = _DATE_PREFIX.sub("", self.slug)
            return f"/posts/{self.date.year:04d}/{self.date.month:02d}/{name}/"
        return f"/wiki/{self.slug}/"

    @property
    def show_toc(self) -> bool:
        """Whether to render a table of contents for this page.

        True only when toc_html contains at least three heading entries. This
        mirrors the previous client-side rule (minHeadings: 3) now that the TOC
        is rendered server-side from the markdown TOC extension output.
        """
        return self.toc_html.count("<li") >= 3
