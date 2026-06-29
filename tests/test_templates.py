from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from bliki.config import SiteConfig
from bliki.models import Page, PageType
from bliki.renderer import Renderer

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def _build_page(content_md: str, page_type: PageType = PageType.WIKI) -> Page:
    """Build a Page with content_html and toc_html populated by the renderer."""
    page = Page(
        title="Sample",
        slug="sample",
        page_type=page_type,
        source_dir=Path("/tmp"),
        content_md=content_md,
    )
    page.content_html, page.toc_html = Renderer(registry=None).render(content_md)
    return page


def _render_template(template_name: str, page: Page) -> str:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)
    return env.get_template(template_name).render(page=page, site=SiteConfig())


def test_page_show_toc_threshold():
    """show_toc is True only when there are at least three headings."""
    assert _build_page("## A\n\n## B\n\n## C").show_toc is True
    assert _build_page("## A\n\n## B").show_toc is False
    assert _build_page("No headings here.").show_toc is False


def test_wiki_template_renders_toc_with_three_headings():
    """toc_html is rendered into the wiki page when the threshold is met."""
    page = _build_page("## Alpha\n\nx\n\n## Beta\n\ny\n\n## Gamma\n\nz")
    out = _render_template("wiki.html", page)
    assert 'class="table-of-contents"' in out
    assert "Table of Contents" in out
    assert 'href="#alpha"' in out


def test_wiki_template_omits_toc_below_threshold():
    """No TOC markup is emitted below the 3-heading threshold."""
    page = _build_page("## Alpha\n\nx\n\n## Beta\n\ny")
    out = _render_template("wiki.html", page)
    assert "table-of-contents" not in out


def test_post_template_renders_toc_with_three_headings():
    """The post template renders the TOC the same way as the wiki template."""
    page = _build_page(
        "## Alpha\n\nx\n\n## Beta\n\ny\n\n## Gamma\n\nz", page_type=PageType.POST
    )
    out = _render_template("post.html", page)
    assert 'class="table-of-contents"' in out
