import datetime
from pathlib import Path

import pytest

from bliki.models import Page, PageType
from bliki.scanner import scan_content


def test_scan_finds_all_pages(content_dir):
    """Scanner finds posts and wiki pages."""
    pages = scan_content(content_dir)
    titles = {p.title for p in pages}
    assert "First Post" in titles
    assert "Draft Post" in titles
    assert "Python" in titles


def test_scan_identifies_page_types(content_dir):
    """Scanner correctly assigns PageType."""
    pages = scan_content(content_dir)
    by_title = {p.title: p for p in pages}
    assert by_title["First Post"].page_type == PageType.POST
    assert by_title["Python"].page_type == PageType.WIKI


def test_scan_parses_front_matter(content_dir):
    """Scanner extracts front matter metadata."""
    pages = scan_content(content_dir)
    by_title = {p.title: p for p in pages}
    post = by_title["First Post"]
    assert post.category == "programming"
    assert post.summary == "My first post"
    assert str(post.date) == "2026-02-22"


def test_scan_excludes_drafts_by_default(content_dir):
    """Scanner excludes drafts unless include_drafts=True."""
    pages = scan_content(content_dir, include_drafts=False)
    titles = {p.title for p in pages}
    assert "Draft Post" not in titles


def test_scan_includes_drafts_when_requested(content_dir):
    """Scanner includes drafts when include_drafts=True."""
    pages = scan_content(content_dir, include_drafts=True)
    titles = {p.title for p in pages}
    assert "Draft Post" in titles


def test_page_slug_derived_from_directory(content_dir):
    """Slug comes from the content directory name."""
    pages = scan_content(content_dir)
    by_title = {p.title: p for p in pages}
    assert by_title["First Post"].slug == "2026-02-22-first-post"
    assert by_title["Python"].slug == "python"


def test_page_url_for_post(content_dir):
    """Posts get date-based URLs."""
    pages = scan_content(content_dir)
    by_title = {p.title: p for p in pages}
    assert by_title["First Post"].url == "/posts/2026/02/first-post/"


def test_page_url_for_wiki(content_dir):
    """Wiki pages get /wiki/<slug>/ URLs."""
    pages = scan_content(content_dir)
    by_title = {p.title: p for p in pages}
    assert by_title["Python"].url == "/wiki/python/"


def test_scan_normalizes_datetime_to_date(tmp_path):
    """Frontmatter date parsed as datetime.datetime by YAML is normalized to datetime.date."""
    posts_dir = tmp_path / "posts" / "2026-02-22-test-post"
    posts_dir.mkdir(parents=True)
    # YAML parses "2026-02-22 00:00:00" as datetime.datetime, not datetime.date
    (posts_dir / "index.md").write_text(
        "---\ntitle: Test Post\ndate: 2026-02-22 00:00:00\n---\nContent."
    )
    pages = scan_content(tmp_path)
    post = next(p for p in pages if p.title == "Test Post")
    assert type(post.date) is datetime.date
    assert str(post.date) == "2026-02-22"


def test_scanner_logs_debug_for_directory_without_index_md(tmp_path, caplog):
    """Scanner emits a debug log when skipping a directory with no index.md."""
    import logging

    posts_dir = tmp_path / "posts" / "2026-02-22-no-index"
    posts_dir.mkdir(parents=True)

    with caplog.at_level(logging.DEBUG, logger="bliki.scanner"):
        scan_content(tmp_path)

    assert "2026-02-22-no-index" in caplog.text


def test_page_category_url_returns_slugified_path(content_dir):
    """Page.category_url returns the /categories/<slug>/ URL for the page's category."""
    pages = scan_content(content_dir)
    by_title = {p.title: p for p in pages}
    assert by_title["First Post"].category_url == "/categories/programming/"
    assert by_title["Python"].category_url == "/categories/languages/"


def test_page_category_url_empty_when_no_category():
    """Page.category_url returns an empty string when category is not set."""
    page = Page(
        title="No Category",
        slug="no-category",
        page_type=PageType.WIKI,
        source_dir=Path("/tmp"),
        content_md="",
        category="",
    )
    assert page.category_url == ""


def test_page_category_url_slugifies_spaces():
    """Page.category_url converts spaces in category names to hyphens."""
    page = Page(
        title="Test",
        slug="test",
        page_type=PageType.WIKI,
        source_dir=Path("/tmp"),
        content_md="",
        category="Web Development",
    )
    assert page.category_url == "/categories/web-development/"


def test_post_url_without_date_raises():
    """Post with no date raises ValueError rather than silently returning a wiki URL."""
    page = Page(
        title="Dateless Post",
        slug="dateless-post",
        page_type=PageType.POST,
        source_dir=Path("/tmp"),
        content_md="",
        date=None,
    )
    with pytest.raises(ValueError, match="date"):
        _ = page.url


def test_post_url_without_date_prefix_uses_full_slug():
    """A post directory with no YYYY-MM-DD- prefix uses the whole slug as the name
    instead of crashing."""
    page = Page(
        title="No Prefix Post",
        slug="no-date-prefix",
        page_type=PageType.POST,
        source_dir=Path("/tmp"),
        content_md="",
        date=datetime.date(2026, 2, 22),
    )
    assert page.url == "/posts/2026/02/no-date-prefix/"


def test_post_url_follows_frontmatter_date_when_dir_prefix_differs():
    """The URL follows the frontmatter date; a stale directory date prefix is
    stripped rather than causing a crash."""
    page = Page(
        title="Re-dated Post",
        slug="2026-02-22-hello-world",
        page_type=PageType.POST,
        source_dir=Path("/tmp"),
        content_md="",
        date=datetime.date(2026, 3, 1),
    )
    assert page.url == "/posts/2026/03/hello-world/"


def test_scan_content_with_only_posts_dir(tmp_path):
    """scan_content works when only posts/ exists (no wiki/ directory)."""
    posts_dir = tmp_path / "posts" / "2026-02-22-solo-post"
    posts_dir.mkdir(parents=True)
    (posts_dir / "index.md").write_text(
        "---\ntitle: Solo Post\ndate: 2026-02-22\n---\nContent.\n"
    )
    pages = scan_content(tmp_path)
    assert len(pages) == 1
    assert pages[0].title == "Solo Post"


def test_scan_content_with_only_wiki_dir(tmp_path):
    """scan_content works when only wiki/ exists (no posts/ directory)."""
    wiki_dir = tmp_path / "wiki" / "solo-wiki"
    wiki_dir.mkdir(parents=True)
    (wiki_dir / "index.md").write_text("---\ntitle: Solo Wiki\n---\nContent.\n")
    pages = scan_content(tmp_path)
    assert len(pages) == 1
    assert pages[0].title == "Solo Wiki"


def test_scan_content_empty_directory(tmp_path):
    """scan_content returns empty list for a content directory with no posts or wiki."""
    pages = scan_content(tmp_path)
    assert pages == []
