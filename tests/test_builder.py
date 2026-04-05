import pytest

from bliki.builder import build_site
from tests.conftest import create_minimal_templates


@pytest.fixture
def built_site(content_dir, tmp_path):
    """Run a default build (no drafts) and return the output directory."""
    templates_dir = tmp_path / "templates"
    create_minimal_templates(templates_dir)
    output_dir = tmp_path / "output"
    build_site(
        content_dir=content_dir,
        output_dir=output_dir,
        templates_dir=templates_dir,
        include_drafts=False,
    )
    return output_dir


def test_build_creates_output_dir(built_site):
    """Build creates the output directory."""
    assert built_site.exists()


def test_build_generates_post_html(built_site):
    """Build generates HTML for each published post."""
    post_html = built_site / "posts" / "2026" / "02" / "first-post" / "index.html"
    assert post_html.exists()
    assert "<h1>First Post</h1>" in post_html.read_text()


def test_build_generates_wiki_html(built_site):
    """Build generates HTML for each wiki page."""
    wiki_html = built_site / "wiki" / "python" / "index.html"
    assert wiki_html.exists()
    assert "<h1>Python</h1>" in wiki_html.read_text()


def test_build_generates_index_pages(built_site):
    """Build generates post index, wiki index, and category index."""
    assert (built_site / "index.html").exists()
    assert (built_site / "wiki" / "index.html").exists()
    assert (built_site / "categories" / "index.html").exists()


def test_build_generates_category_pages(built_site):
    """Build generates a page for each category."""
    assert (built_site / "categories" / "programming" / "index.html").exists()
    assert (built_site / "categories" / "languages" / "index.html").exists()


def test_build_wiki_links_resolve_in_output(built_site):
    """Wiki links in rendered HTML point to correct URLs."""
    content = (built_site / "posts" / "2026" / "02" / "first-post" / "index.html").read_text()
    assert 'href="/wiki/python/"' in content


def test_build_backlinks_appear_in_output(built_site):
    """Backlinks are rendered on both the source and target pages."""
    wiki_html = (built_site / "wiki" / "python" / "index.html").read_text()
    assert "First Post" in wiki_html

    post_html = (built_site / "posts" / "2026" / "02" / "first-post" / "index.html").read_text()
    assert "Python" in post_html


def test_build_excludes_drafts(built_site):
    """Draft posts are not included in the output by default."""
    draft_html = built_site / "posts" / "2026" / "02" / "draft-post" / "index.html"
    assert not draft_html.exists()
    assert "Draft Post" not in (built_site / "index.html").read_text()


def test_build_includes_drafts_when_requested(content_dir, tmp_path):
    """Draft posts appear in output when include_drafts=True."""
    templates_dir = tmp_path / "templates"
    create_minimal_templates(templates_dir)
    output_dir = tmp_path / "output"
    build_site(
        content_dir=content_dir,
        output_dir=output_dir,
        templates_dir=templates_dir,
        include_drafts=True,
    )
    assert (output_dir / "posts" / "2026" / "02" / "draft-post" / "index.html").exists()


def test_build_broken_wiki_link_has_css_class(content_dir, tmp_path):
    """Broken [[wiki links]] in built HTML have class='broken-link'."""
    # Add a post that links to a page that doesn't exist
    post_dir = content_dir / "posts" / "2026-03-01-broken-link-post"
    post_dir.mkdir(parents=True)
    (post_dir / "index.md").write_text(
        "---\n"
        "title: Broken Link Post\n"
        "date: 2026-03-01\n"
        "draft: false\n"
        "---\n"
        "See [[Nonexistent Page]] for details.\n"
    )

    templates_dir = tmp_path / "templates"
    create_minimal_templates(templates_dir)
    output_dir = tmp_path / "output"
    build_site(
        content_dir=content_dir,
        output_dir=output_dir,
        templates_dir=templates_dir,
        include_drafts=False,
    )

    post_html = (
        output_dir / "posts" / "2026" / "03" / "broken-link-post" / "index.html"
    ).read_text()
    assert "broken-link" in post_html
    assert "Nonexistent Page" in post_html
