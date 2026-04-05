import xml.etree.ElementTree as ET

from bliki.feed import generate_rss
from bliki.scanner import scan_content


def test_generate_rss_valid_xml(content_dir):
    """RSS feed is valid XML."""
    pages = scan_content(content_dir, include_drafts=False)
    xml_str = generate_rss(
        pages,
        site_name="Test Blog",
        site_url="https://example.com",
        site_description="A test blog",
    )
    root = ET.fromstring(xml_str)
    assert root.tag == "rss"


def test_generate_rss_contains_posts(content_dir):
    """RSS feed contains published posts."""
    pages = scan_content(content_dir, include_drafts=False)
    xml_str = generate_rss(
        pages,
        site_name="Test Blog",
        site_url="https://example.com",
        site_description="A test blog",
    )
    assert "First Post" in xml_str


def test_generate_rss_excludes_wiki_pages(content_dir):
    """RSS feed only contains posts, not wiki pages."""
    pages = scan_content(content_dir, include_drafts=False)
    xml_str = generate_rss(
        pages,
        site_name="Test Blog",
        site_url="https://example.com",
        site_description="A test blog",
    )
    root = ET.fromstring(xml_str)
    item_titles = [item.text for item in root.findall(".//item/title")]
    assert "Python" not in item_titles


def test_generate_rss_excludes_drafts(content_dir):
    """RSS feed does not include draft posts."""
    pages = scan_content(content_dir, include_drafts=False)
    xml_str = generate_rss(
        pages,
        site_name="Test Blog",
        site_url="https://example.com",
        site_description="A test blog",
    )
    assert "Draft Post" not in xml_str


def test_generate_rss_channel_metadata(content_dir):
    """RSS channel contains site name, url, and description."""
    pages = scan_content(content_dir, include_drafts=False)
    xml_str = generate_rss(
        pages,
        site_name="Test Blog",
        site_url="https://example.com",
        site_description="A test blog",
    )
    root = ET.fromstring(xml_str)
    channel = root.find("channel")
    assert channel.find("title").text == "Test Blog"
    assert channel.find("link").text == "https://example.com"
    assert channel.find("description").text == "A test blog"


def test_generate_rss_item_has_link(content_dir):
    """Each RSS item contains an absolute URL."""
    pages = scan_content(content_dir, include_drafts=False)
    xml_str = generate_rss(
        pages,
        site_name="Test Blog",
        site_url="https://example.com",
        site_description="A test blog",
    )
    root = ET.fromstring(xml_str)
    items = root.findall(".//item")
    assert len(items) == 1
    link = items[0].find("link").text
    assert link.startswith("https://example.com")
    assert "/posts/" in link


def test_generate_rss_item_has_guid(content_dir):
    """Each RSS item has a guid element matching its absolute URL."""
    pages = scan_content(content_dir, include_drafts=False)
    xml_str = generate_rss(
        pages,
        site_name="Test Blog",
        site_url="https://example.com",
        site_description="A test blog",
    )
    root = ET.fromstring(xml_str)
    for item in root.findall(".//item"):
        guid = item.find("guid")
        assert guid is not None, "RSS item is missing <guid>"
        assert guid.text.startswith("https://example.com")
        assert guid.text == item.find("link").text


def test_generate_rss_excludes_dateless_posts():
    """generate_rss with a mix of dated and dateless posts does not crash and omits dateless."""
    import datetime
    from pathlib import Path
    from bliki.models import Page, PageType

    dated = Page(
        title="Dated Post",
        slug="2026-02-22-dated-post",
        page_type=PageType.POST,
        source_dir=Path("/tmp"),
        content_md="",
        date=datetime.date(2026, 2, 22),
    )
    dateless = Page(
        title="Dateless Post",
        slug="2026-01-01-dateless-post",
        page_type=PageType.POST,
        source_dir=Path("/tmp"),
        content_md="",
        date=None,
    )
    xml_str = generate_rss([dated, dateless], "Test", "https://example.com", "Test")
    root = ET.fromstring(xml_str)
    item_titles = [item.find("title").text for item in root.findall(".//item")]
    assert "Dated Post" in item_titles
    assert "Dateless Post" not in item_titles
