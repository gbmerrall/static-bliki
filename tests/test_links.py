from bliki.links import PageRegistry, build_backlinks, extract_wiki_links
from bliki.scanner import scan_content


def test_extract_wiki_links_simple():
    """Extract [[Page Name]] from markdown."""
    text = "See [[Python]] and [[First Post]] for details."
    links = extract_wiki_links(text)
    assert links == ["Python", "First Post"]


def test_extract_wiki_links_with_display_text():
    """Extract target from [[Page Name|display text]]."""
    text = "See [[Python|the Python page]] here."
    links = extract_wiki_links(text)
    assert links == ["Python"]


def test_extract_wiki_links_none():
    """Return empty list when no wiki links present."""
    text = "No links here."
    links = extract_wiki_links(text)
    assert links == []


def test_page_registry_resolve(content_dir):
    """Registry resolves page titles to URLs."""
    pages = scan_content(content_dir)
    registry = PageRegistry(pages)
    assert registry.resolve("Python") == "/wiki/python/"
    assert registry.resolve("First Post") == "/posts/2026/02/first-post/"


def test_page_registry_resolve_case_insensitive(content_dir):
    """Registry resolves case-insensitively."""
    pages = scan_content(content_dir)
    registry = PageRegistry(pages)
    assert registry.resolve("python") == "/wiki/python/"


def test_page_registry_resolve_missing(content_dir):
    """Registry returns None for unknown pages."""
    pages = scan_content(content_dir)
    registry = PageRegistry(pages)
    assert registry.resolve("Nonexistent Page") is None


def test_build_backlinks(content_dir):
    """Build backlinks maps target titles to source pages."""
    pages = scan_content(content_dir)
    backlinks = build_backlinks(pages)
    # Keys are normalized to lowercase
    python_backlink_titles = {p.title for p in backlinks.get("python", [])}
    assert "First Post" in python_backlink_titles
    first_post_backlink_titles = {p.title for p in backlinks.get("first post", [])}
    assert "Python" in first_post_backlink_titles


def test_build_backlinks_normalizes_target_case():
    """Links to [[python]] and [[Python]] from the same source produce one backlinks key."""
    from pathlib import Path
    from bliki.models import Page, PageType

    source = Page(
        title="Source",
        slug="source",
        page_type=PageType.WIKI,
        source_dir=Path("/tmp"),
        content_md="See [[python]] and [[Python]].",
    )
    backlinks = build_backlinks([source])
    python_keys = [k for k in backlinks if k.lower() == "python"]
    assert len(python_keys) == 1, f"Expected one key, got: {python_keys}"


def test_build_backlinks_dedupes_repeated_links_from_same_page():
    """A page that links the same target twice appears only once in its backlinks."""
    from pathlib import Path

    from bliki.models import Page, PageType

    source = Page(
        title="Source",
        slug="source",
        page_type=PageType.WIKI,
        source_dir=Path("/tmp"),
        content_md="See [[Python]] and again [[Python]].",
    )
    backlinks = build_backlinks([source])
    assert len(backlinks["python"]) == 1
