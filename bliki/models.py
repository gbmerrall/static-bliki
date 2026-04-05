from __future__ import annotations

import datetime
import enum
from dataclasses import dataclass, field
from pathlib import Path


class PageType(enum.Enum):
    POST = "post"
    WIKI = "wiki"


def slugify_category(name: str) -> str:
    """Convert a category name to a URL slug.

    Args:
        name: Human-readable category name.

    Returns:
        Lowercase slug with spaces replaced by hyphens.
    """
    return name.lower().replace(" ", "-")


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
        return f"/categories/{slugify_category(self.category)}/"

    @property
    def url(self) -> str:
        """Generate the URL path for this page.

        Raises:
            ValueError: If a POST page has no date, or if the slug does not
                start with the expected YYYY-MM-DD- date prefix.
        """
        if self.page_type == PageType.POST:
            if not self.date:
                raise ValueError(f"Post '{self.title}' has no date")
            date_prefix = self.date.isoformat() + "-"
            if not self.slug.startswith(date_prefix):
                raise ValueError(
                    f"Post slug '{self.slug}' must start with date prefix '{date_prefix}'"
                )
            name = self.slug[len(date_prefix):]
            return f"/posts/{self.date.year:04d}/{self.date.month:02d}/{name}/"
        return f"/wiki/{self.slug}/"
