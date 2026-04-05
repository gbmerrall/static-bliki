from bliki.links import PageRegistry
from bliki.renderer import render_markdown
from bliki.scanner import scan_content


def test_render_basic_markdown():
    """Render simple markdown to HTML."""
    html, toc = render_markdown("# Hello\n\nParagraph.", registry=None)
    assert "<h1" in html
    assert "<p>Paragraph.</p>" in html


def test_render_wiki_link_resolved(content_dir):
    """Wiki links are rendered as <a> tags when target exists."""
    pages = scan_content(content_dir)
    registry = PageRegistry(pages)
    html, toc = render_markdown("See [[Python]] here.", registry=registry)
    assert 'href="/wiki/python/"' in html
    assert "Python</a>" in html


def test_render_wiki_link_with_display_text(content_dir):
    """Wiki links with display text use the display text."""
    pages = scan_content(content_dir)
    registry = PageRegistry(pages)
    html, toc = render_markdown("See [[Python|the docs]] here.", registry=registry)
    assert 'href="/wiki/python/"' in html
    assert "the docs</a>" in html


def test_render_wiki_link_broken(content_dir):
    """Broken wiki links get a special CSS class."""
    pages = scan_content(content_dir)
    registry = PageRegistry(pages)
    html, toc = render_markdown("See [[Nonexistent]] here.", registry=registry)
    assert "broken-link" in html
    assert "Nonexistent</a>" in html


def test_render_fenced_code():
    """Fenced code blocks are rendered with syntax highlighting."""
    md = '```python\nprint("hello")\n```'
    html, toc = render_markdown(md, registry=None)
    assert "<code" in html


def test_render_toc():
    """Table of contents is generated from headings."""
    md = "## Section One\n\nText\n\n## Section Two\n\nMore text"
    html, toc = render_markdown(md, registry=None)
    assert "Section One" in toc
    assert "Section Two" in toc


def test_render_broken_display_link_class_appears_once(content_dir):
    """Broken display-text wiki links get class='broken-link' exactly once."""
    pages = scan_content(content_dir)
    registry = PageRegistry(pages)
    html, _ = render_markdown("See [[Nonexistent|click here]] for info.", registry=registry)
    assert 'class="broken-link"' in html
    assert html.count('class="broken-link"') == 1
    assert "click here</a>" in html
