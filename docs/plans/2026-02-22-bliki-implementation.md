# Bliki Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan
> task-by-task.

**Goal:** Build a static site generator that produces a blog with wiki-style cross-linking from
markdown files.

**Architecture:** Python CLI tool using Click. Content is markdown files with YAML front matter
in a directory-per-page structure. Build pipeline scans content, resolves `[[wiki links]]`,
renders markdown through Jinja2 templates, processes images via Pillow, and generates static
HTML. Dev server via livereload. Search via Pagefind.

**Tech Stack:** Python 3.12, click, python-markdown (wikilinks extension), jinja2,
python-frontmatter, pygments, pillow, livereload, pagefind (external binary)

**Design doc:** `docs/plans/2026-02-22-bliki-design.md`

---

### Task 1: Project scaffolding and dependencies

**Files:**
- Modify: `Pipfile`
- Create: `bliki/__init__.py`
- Create: `bliki/cli.py`
- Create: `tests/__init__.py`
- Create: `tests/test_cli.py`

**Step 1: Install dependencies**

```bash
pipenv install click jinja2 python-frontmatter markdown pygments pillow livereload
pipenv install --dev pytest pytest-cov
```

**Step 2: Create project structure**

```bash
mkdir -p bliki tests content/posts content/wiki templates/static
touch bliki/__init__.py tests/__init__.py
```

**Step 3: Write failing test for CLI entry point**

`tests/test_cli.py`:
```python
from click.testing import CliRunner

from bliki.cli import cli


def test_cli_has_build_command():
    runner = CliRunner()
    result = runner.invoke(cli, ["build", "--help"])
    assert result.exit_code == 0
    assert "Build the site" in result.output


def test_cli_has_serve_command():
    runner = CliRunner()
    result = runner.invoke(cli, ["serve", "--help"])
    assert result.exit_code == 0


def test_cli_has_new_command():
    runner = CliRunner()
    result = runner.invoke(cli, ["new", "--help"])
    assert result.exit_code == 0
```

**Step 4: Run test to verify it fails**

```bash
pytest tests/test_cli.py -v
```

Expected: FAIL (ImportError, cli not defined)

**Step 5: Implement CLI skeleton**

`bliki/cli.py`:
```python
import click


@click.group()
def cli():
    """Bliki -- a blog with wiki features."""


@cli.command()
@click.option("--drafts", is_flag=True, help="Include draft posts.")
@click.option(
    "--output",
    "-o",
    default="output",
    type=click.Path(),
    help="Output directory.",
)
def build(drafts, output):
    """Build the site to static HTML."""
    click.echo(f"Building site to {output}/ (drafts={drafts})")


@cli.command()
@click.option("--port", "-p", default=8000, help="Port for dev server.")
def serve(port):
    """Build and serve with live reload."""
    click.echo(f"Serving on port {port}")


@cli.group()
def new():
    """Scaffold new content."""


@new.command("post")
@click.argument("title")
def new_post(title):
    """Create a new blog post."""
    click.echo(f"Creating post: {title}")


@new.command("wiki")
@click.argument("title")
def new_wiki(title):
    """Create a new wiki page."""
    click.echo(f"Creating wiki page: {title}")
```

**Step 6: Run tests to verify they pass**

```bash
pytest tests/test_cli.py -v
```

Expected: all PASS

**Step 7: Commit**

```bash
git add bliki/ tests/ Pipfile Pipfile.lock content/ templates/
git commit -m "Scaffold project structure with CLI skeleton"
```

---

### Task 2: Content model and scanner

**Files:**
- Create: `bliki/models.py`
- Create: `bliki/scanner.py`
- Create: `tests/test_scanner.py`
- Create: `tests/conftest.py`

**Step 1: Write failing tests for the content model and scanner**

`tests/conftest.py`:
```python
from pathlib import Path

import pytest


@pytest.fixture
def content_dir(tmp_path):
    """Create a temporary content directory with sample posts and wiki pages."""
    posts_dir = tmp_path / "content" / "posts"
    wiki_dir = tmp_path / "content" / "wiki"

    # Post with image
    post1_dir = posts_dir / "2026-02-22-first-post"
    post1_dir.mkdir(parents=True)
    (post1_dir / "index.md").write_text(
        "---\n"
        "title: First Post\n"
        "category: programming\n"
        "summary: My first post\n"
        "date: 2026-02-22\n"
        "draft: false\n"
        "---\n"
        "Hello world. See [[Python]] for more.\n"
    )

    # Draft post
    post2_dir = posts_dir / "2026-02-20-draft-post"
    post2_dir.mkdir(parents=True)
    (post2_dir / "index.md").write_text(
        "---\n"
        "title: Draft Post\n"
        "category: programming\n"
        "summary: A draft\n"
        "date: 2026-02-20\n"
        "draft: true\n"
        "---\n"
        "This is a draft.\n"
    )

    # Wiki page
    wiki1_dir = wiki_dir / "python"
    wiki1_dir.mkdir(parents=True)
    (wiki1_dir / "index.md").write_text(
        "---\n"
        "title: Python\n"
        "category: languages\n"
        "summary: Notes on Python\n"
        "---\n"
        "Python is great. See [[First Post]].\n"
    )

    return tmp_path / "content"
```

`tests/test_scanner.py`:
```python
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
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_scanner.py -v
```

Expected: FAIL (ImportError)

**Step 3: Implement the content model**

`bliki/models.py`:
```python
from __future__ import annotations

import datetime
import enum
from dataclasses import dataclass, field
from pathlib import Path


class PageType(enum.Enum):
    POST = "post"
    WIKI = "wiki"


@dataclass
class Page:
    """Represents a single content page (post or wiki)."""

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
    def url(self) -> str:
        """Generate the URL path for this page."""
        if self.page_type == PageType.POST and self.date:
            # Strip date prefix from slug for the URL
            # Slug is like "2026-02-22-first-post", we want "first-post"
            name = self.slug[11:]  # len("YYYY-MM-DD-") == 11
            return f"/posts/{self.date.year:04d}/{self.date.month:02d}/{name}/"
        return f"/wiki/{self.slug}/"
```

**Step 4: Implement the scanner**

`bliki/scanner.py`:
```python
import datetime
import logging
from pathlib import Path

import frontmatter

from bliki.models import Page, PageType

logger = logging.getLogger(__name__)


def scan_content(
    content_dir: Path,
    include_drafts: bool = True,
) -> list[Page]:
    """Scan content directory and return a list of Page objects.

    Args:
        content_dir: Path to the content directory containing posts/ and wiki/ subdirs.
        include_drafts: If True, include pages marked as draft.

    Returns:
        List of Page objects parsed from the content directory.
    """
    pages: list[Page] = []

    posts_dir = content_dir / "posts"
    wiki_dir = content_dir / "wiki"

    if posts_dir.exists():
        for page_dir in sorted(posts_dir.iterdir()):
            page = _load_page(page_dir, PageType.POST)
            if page:
                pages.append(page)

    if wiki_dir.exists():
        for page_dir in sorted(wiki_dir.iterdir()):
            page = _load_page(page_dir, PageType.WIKI)
            if page:
                pages.append(page)

    if not include_drafts:
        pages = [p for p in pages if not p.draft]

    return pages


def _load_page(page_dir: Path, page_type: PageType) -> Page | None:
    """Load a single page from a directory containing index.md.

    Args:
        page_dir: Directory containing index.md and optional assets.
        page_type: Whether this is a POST or WIKI page.

    Returns:
        Page object, or None if no index.md found.
    """
    index_file = page_dir / "index.md"
    if not index_file.exists():
        return None

    post = frontmatter.load(index_file)

    date = post.get("date")
    if isinstance(date, str):
        date = datetime.date.fromisoformat(date)

    return Page(
        title=post.get("title", page_dir.name),
        slug=page_dir.name,
        page_type=page_type,
        source_dir=page_dir,
        content_md=post.content,
        category=post.get("category", ""),
        summary=post.get("summary", ""),
        date=date,
        draft=post.get("draft", False),
    )
```

**Step 5: Run tests to verify they pass**

```bash
pytest tests/test_scanner.py -v
```

Expected: all PASS

**Step 6: Commit**

```bash
git add bliki/models.py bliki/scanner.py tests/conftest.py tests/test_scanner.py
git commit -m "Add content model and scanner with front matter parsing"
```

---

### Task 3: Wiki link resolution and backlinks

**Files:**
- Create: `bliki/links.py`
- Create: `tests/test_links.py`

**Step 1: Write failing tests**

`tests/test_links.py`:
```python
import re

from bliki.links import extract_wiki_links, build_backlinks, PageRegistry
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
    # "Python" wiki page is linked from "First Post"
    python_backlink_titles = {p.title for p in backlinks.get("Python", [])}
    assert "First Post" in python_backlink_titles
    # "First Post" is linked from "Python" wiki page
    first_post_backlink_titles = {p.title for p in backlinks.get("First Post", [])}
    assert "Python" in first_post_backlink_titles
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_links.py -v
```

Expected: FAIL (ImportError)

**Step 3: Implement link resolution**

`bliki/links.py`:
```python
from __future__ import annotations

import logging
import re

from bliki.models import Page

logger = logging.getLogger(__name__)

WIKI_LINK_PATTERN = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")


def extract_wiki_links(text: str) -> list[str]:
    """Extract wiki link targets from markdown text.

    Parses [[Page Name]] and [[Page Name|display text]] patterns, returning
    the target page name for each.

    Args:
        text: Markdown text to scan.

    Returns:
        List of page name targets found in the text.
    """
    return WIKI_LINK_PATTERN.findall(text)


class PageRegistry:
    """Registry of all pages, enabling title-based lookup for wiki link resolution."""

    def __init__(self, pages: list[Page]) -> None:
        self._by_title: dict[str, Page] = {}
        for page in pages:
            self._by_title[page.title.lower()] = page

    def resolve(self, title: str) -> str | None:
        """Resolve a page title to its URL.

        Args:
            title: The page title to look up (case-insensitive).

        Returns:
            The URL string, or None if no matching page exists.
        """
        page = self._by_title.get(title.lower())
        return page.url if page else None

    def get_page(self, title: str) -> Page | None:
        """Look up a Page by title.

        Args:
            title: The page title to look up (case-insensitive).

        Returns:
            The Page object, or None if not found.
        """
        return self._by_title.get(title.lower())


def build_backlinks(pages: list[Page]) -> dict[str, list[Page]]:
    """Build a backlinks map: target title -> list of source pages that link to it.

    Args:
        pages: All pages to scan for outgoing wiki links.

    Returns:
        Dict mapping page titles to list of pages that link to them.
    """
    backlinks: dict[str, list[Page]] = {}
    for page in pages:
        targets = extract_wiki_links(page.content_md)
        for target in targets:
            backlinks.setdefault(target, []).append(page)
    return backlinks
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_links.py -v
```

Expected: all PASS

**Step 5: Commit**

```bash
git add bliki/links.py tests/test_links.py
git commit -m "Add wiki link extraction, page registry, and backlink computation"
```

---

### Task 4: Markdown rendering with wiki links

**Files:**
- Create: `bliki/renderer.py`
- Create: `tests/test_renderer.py`

**Step 1: Write failing tests**

`tests/test_renderer.py`:
```python
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
    assert '<a href="/wiki/python/"' in html
    assert "Python</a>" in html


def test_render_wiki_link_with_display_text(content_dir):
    """Wiki links with display text use the display text."""
    pages = scan_content(content_dir)
    registry = PageRegistry(pages)
    html, toc = render_markdown("See [[Python|the docs]] here.", registry=registry)
    assert '<a href="/wiki/python/"' in html
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
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_renderer.py -v
```

Expected: FAIL (ImportError)

**Step 3: Implement the renderer**

`bliki/renderer.py`:
```python
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import markdown
from markdown.extensions.wikilinks import WikiLinkExtension

if TYPE_CHECKING:
    from bliki.links import PageRegistry

logger = logging.getLogger(__name__)


def _make_url_builder(registry: PageRegistry | None):
    """Create a URL builder function for the wikilinks extension.

    Args:
        registry: Page registry for resolving titles to URLs.

    Returns:
        Callable that takes (label, base, end) and returns a URL string.
    """
    def build_url(label: str, base: str, end: str) -> str:
        if registry:
            url = registry.resolve(label)
            if url:
                return url
        # Return a placeholder for broken links -- we'll add CSS class via post-processing
        return f"#broken:{label}"

    return build_url


def render_markdown(
    text: str,
    registry: PageRegistry | None = None,
) -> tuple[str, str]:
    """Render markdown text to HTML with wiki link support.

    Args:
        text: Markdown source text.
        registry: Optional PageRegistry for resolving [[wiki links]].

    Returns:
        Tuple of (content_html, toc_html).
    """
    extensions = [
        "fenced_code",
        "codehilite",
        "tables",
        WikiLinkExtension(
            base_url="",
            end_url="",
            build_url=_make_url_builder(registry),
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

    md = markdown.Markdown(
        extensions=extensions,
        extension_configs=extension_configs,
    )

    html = md.convert(text)
    toc = getattr(md, "toc", "")

    # Post-process broken links: add CSS class
    html = html.replace('href="#broken:', 'class="broken-link" href="#broken:')

    return html, toc
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_renderer.py -v
```

Expected: all PASS

**Step 5: Commit**

```bash
git add bliki/renderer.py tests/test_renderer.py
git commit -m "Add markdown renderer with wiki links, code highlighting, and TOC"
```

---

### Task 5: Image processing

**Files:**
- Create: `bliki/images.py`
- Create: `tests/test_images.py`

**Step 1: Write failing tests**

`tests/test_images.py`:
```python
from pathlib import Path

from PIL import Image

from bliki.images import process_images, rewrite_img_tags


def _create_test_image(path: Path, width: int = 2000, height: int = 1200):
    """Helper to create a test JPEG image."""
    img = Image.new("RGB", (width, height), color="red")
    img.save(path, "JPEG")


def test_process_images_creates_resized_variants(tmp_path):
    """Process images creates 600w and 1200w variants."""
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    _create_test_image(source_dir / "hero.jpg")

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    manifest = process_images(source_dir, output_dir)

    assert (output_dir / "hero.jpg").exists()
    assert (output_dir / "hero-600.webp").exists()
    assert (output_dir / "hero-1200.webp").exists()
    assert "hero.jpg" in manifest


def test_process_images_skips_small_images(tmp_path):
    """Images smaller than a target width don't get that variant."""
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    _create_test_image(source_dir / "small.jpg", width=400, height=300)

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    manifest = process_images(source_dir, output_dir)

    assert (output_dir / "small.jpg").exists()
    # 400px wide -- should not create 600 or 1200 variants
    assert not (output_dir / "small-600.webp").exists()
    assert not (output_dir / "small-1200.webp").exists()


def test_process_images_skips_non_images(tmp_path):
    """Non-image files in the directory are ignored."""
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "notes.txt").write_text("not an image")

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    manifest = process_images(source_dir, output_dir)
    assert manifest == {}


def test_rewrite_img_tags_to_picture():
    """Rewrite <img> tags to <picture> elements with srcset."""
    html = '<p><img alt="Hero" src="hero.jpg"></p>'
    manifest = {
        "hero.jpg": {
            "original": "hero.jpg",
            "variants": [
                {"src": "hero-600.webp", "width": 600, "format": "webp"},
                {"src": "hero-1200.webp", "width": 1200, "format": "webp"},
            ],
        },
    }
    result = rewrite_img_tags(html, manifest)
    assert "<picture>" in result
    assert "srcset" in result
    assert "hero-600.webp" in result
    assert "hero-1200.webp" in result
    # Original is still the fallback <img>
    assert 'src="hero.jpg"' in result


def test_rewrite_img_tags_no_manifest_match():
    """Images not in manifest are left unchanged."""
    html = '<p><img alt="Other" src="other.jpg"></p>'
    result = rewrite_img_tags(html, manifest={})
    assert result == html
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_images.py -v
```

Expected: FAIL (ImportError)

**Step 3: Implement image processing**

`bliki/images.py`:
```python
from __future__ import annotations

import logging
import re
import shutil
from pathlib import Path

from PIL import Image

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
TARGET_WIDTHS = [600, 1200]


def process_images(
    source_dir: Path,
    output_dir: Path,
) -> dict:
    """Process images in a content directory: copy originals, create resized WebP variants.

    Args:
        source_dir: Directory containing source images alongside index.md.
        output_dir: Directory to write processed images to.

    Returns:
        Manifest dict mapping original filename to variant info for srcset rewriting.
    """
    manifest: dict = {}
    output_dir.mkdir(parents=True, exist_ok=True)

    for file_path in source_dir.iterdir():
        if file_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        # Copy original
        shutil.copy2(file_path, output_dir / file_path.name)

        stem = file_path.stem
        variants = []

        with Image.open(file_path) as img:
            orig_width = img.width

            for target_width in TARGET_WIDTHS:
                if orig_width <= target_width:
                    continue

                ratio = target_width / orig_width
                target_height = int(img.height * ratio)
                resized = img.resize(
                    (target_width, target_height),
                    Image.Resampling.LANCZOS,
                )

                variant_name = f"{stem}-{target_width}.webp"
                resized.save(output_dir / variant_name, "WebP", quality=85)

                variants.append({
                    "src": variant_name,
                    "width": target_width,
                    "format": "webp",
                })

        if variants:
            manifest[file_path.name] = {
                "original": file_path.name,
                "variants": variants,
            }

    return manifest


def rewrite_img_tags(html: str, manifest: dict) -> str:
    """Rewrite <img> tags to <picture> elements with WebP srcset.

    Args:
        html: Rendered HTML content.
        manifest: Image manifest from process_images().

    Returns:
        HTML with <img> tags replaced by <picture> elements where applicable.
    """
    def _replace_img(match: re.Match) -> str:
        full_tag = match.group(0)
        src_match = re.search(r'src="([^"]+)"', full_tag)
        if not src_match:
            return full_tag

        src = src_match.group(1)
        if src not in manifest:
            return full_tag

        info = manifest[src]
        alt_match = re.search(r'alt="([^"]*)"', full_tag)
        alt = alt_match.group(1) if alt_match else ""

        # Build srcset from variants
        srcset_parts = [f'{v["src"]} {v["width"]}w' for v in info["variants"]]
        srcset = ", ".join(srcset_parts)

        return (
            f"<picture>"
            f'<source type="image/webp" srcset="{srcset}">'
            f'<img alt="{alt}" src="{info["original"]}">'
            f"</picture>"
        )

    return re.sub(r"<img[^>]+>", _replace_img, html)
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_images.py -v
```

Expected: all PASS

**Step 5: Commit**

```bash
git add bliki/images.py tests/test_images.py
git commit -m "Add image processing with resize, WebP conversion, and srcset rewriting"
```

---

### Task 6: Adapt pickles templates for Jinja2

**Files:**
- Create: `templates/base.html`
- Create: `templates/post.html`
- Create: `templates/wiki.html`
- Create: `templates/post_index.html`
- Create: `templates/wiki_index.html`
- Create: `templates/category.html`
- Create: `templates/category_index.html`
- Create: `templates/search.html`
- Copy and modify: CSS/JS from `themes/pelican-pickles/static/`

This task is template adaptation -- no unit tests. The templates will be integration-tested
when we wire up the build pipeline in Task 7.

**Step 1: Copy static assets from pickles**

```bash
cp -r themes/pelican-pickles/static/css templates/static/css
cp -r themes/pelican-pickles/static/js templates/static/js
cp -r themes/pelican-pickles/static/images templates/static/images
```

**Step 2: Create base.html**

Adapt from `themes/pelican-pickles/templates/base.html`. Key changes:
- Remove all Pelican-specific variables (SITEURL, FEED_ALL_ATOM, etc.)
- Replace with bliki context: `site.name`, `site.description`, `site.url`
- Keep: CSS custom properties, dark mode toggle, responsive nav, reading progress bar
- Drop: Google Analytics, Disqus, social share buttons, Open Graph (add later)
- Add: navigation links for Posts, Wiki, Categories, Search

**Step 3: Create content templates**

`post.html`: extends base. Shows title, date, category, content HTML, backlinks section.

`wiki.html`: extends base. Shows title, category, content HTML, backlinks section. No date.

`post_index.html`: extends base. Lists posts chronologically (newest first). Each shows
title, date, category, summary.

`wiki_index.html`: extends base. Lists wiki pages alphabetically. Each shows title, category,
summary.

`category.html`: extends base. Shows category name, then lists posts and wiki pages in that
category.

`category_index.html`: extends base. Lists all categories with page counts.

`search.html`: extends base. Includes Pagefind CSS/JS and the search UI div.

**Step 4: Modify CSS**

Strip Pelican-specific styles. Add:
- `.broken-link` style (red text, dashed underline) for unresolved wiki links
- `.backlinks` section styling
- Ensure `<picture>` and responsive images work within article content

**Step 5: Commit**

```bash
git add templates/
git commit -m "Adapt pickles theme templates for bliki"
```

---

### Task 7: Build pipeline

**Files:**
- Create: `bliki/builder.py`
- Create: `tests/test_builder.py`

**Step 1: Write failing tests**

`tests/test_builder.py`:
```python
from pathlib import Path

from bliki.builder import build_site


def test_build_creates_output_dir(content_dir, tmp_path):
    """Build creates the output directory."""
    output_dir = tmp_path / "output"
    templates_dir = tmp_path / "templates"
    _create_minimal_templates(templates_dir)

    build_site(
        content_dir=content_dir,
        output_dir=output_dir,
        templates_dir=templates_dir,
        include_drafts=False,
    )

    assert output_dir.exists()


def test_build_generates_post_html(content_dir, tmp_path):
    """Build generates HTML for each published post."""
    output_dir = tmp_path / "output"
    templates_dir = tmp_path / "templates"
    _create_minimal_templates(templates_dir)

    build_site(
        content_dir=content_dir,
        output_dir=output_dir,
        templates_dir=templates_dir,
        include_drafts=False,
    )

    post_html = output_dir / "posts" / "2026" / "02" / "first-post" / "index.html"
    assert post_html.exists()
    content = post_html.read_text()
    assert "First Post" in content


def test_build_generates_wiki_html(content_dir, tmp_path):
    """Build generates HTML for each wiki page."""
    output_dir = tmp_path / "output"
    templates_dir = tmp_path / "templates"
    _create_minimal_templates(templates_dir)

    build_site(
        content_dir=content_dir,
        output_dir=output_dir,
        templates_dir=templates_dir,
        include_drafts=False,
    )

    wiki_html = output_dir / "wiki" / "python" / "index.html"
    assert wiki_html.exists()
    content = wiki_html.read_text()
    assert "Python" in content


def test_build_generates_index_pages(content_dir, tmp_path):
    """Build generates post index, wiki index, and category index."""
    output_dir = tmp_path / "output"
    templates_dir = tmp_path / "templates"
    _create_minimal_templates(templates_dir)

    build_site(
        content_dir=content_dir,
        output_dir=output_dir,
        templates_dir=templates_dir,
        include_drafts=False,
    )

    assert (output_dir / "index.html").exists()
    assert (output_dir / "wiki" / "index.html").exists()
    assert (output_dir / "categories" / "index.html").exists()


def test_build_generates_category_pages(content_dir, tmp_path):
    """Build generates a page for each category."""
    output_dir = tmp_path / "output"
    templates_dir = tmp_path / "templates"
    _create_minimal_templates(templates_dir)

    build_site(
        content_dir=content_dir,
        output_dir=output_dir,
        templates_dir=templates_dir,
        include_drafts=False,
    )

    assert (output_dir / "categories" / "programming" / "index.html").exists()
    assert (output_dir / "categories" / "languages" / "index.html").exists()


def test_build_wiki_links_resolve_in_output(content_dir, tmp_path):
    """Wiki links in rendered HTML point to correct URLs."""
    output_dir = tmp_path / "output"
    templates_dir = tmp_path / "templates"
    _create_minimal_templates(templates_dir)

    build_site(
        content_dir=content_dir,
        output_dir=output_dir,
        templates_dir=templates_dir,
        include_drafts=False,
    )

    post_html = output_dir / "posts" / "2026" / "02" / "first-post" / "index.html"
    content = post_html.read_text()
    assert 'href="/wiki/python/"' in content


def _create_minimal_templates(templates_dir: Path):
    """Create minimal Jinja2 templates for testing."""
    templates_dir.mkdir(parents=True, exist_ok=True)

    (templates_dir / "base.html").write_text(
        "<!DOCTYPE html><html><body>{% block content %}{% endblock %}</body></html>"
    )
    (templates_dir / "post.html").write_text(
        '{% extends "base.html" %}{% block content %}'
        "<h1>{{ page.title }}</h1>{{ page.content_html | safe }}"
        "{% for bl in page.backlinks %}<a href=\"{{ bl.url }}\">{{ bl.title }}</a>{% endfor %}"
        "{% endblock %}"
    )
    (templates_dir / "wiki.html").write_text(
        '{% extends "base.html" %}{% block content %}'
        "<h1>{{ page.title }}</h1>{{ page.content_html | safe }}"
        "{% for bl in page.backlinks %}<a href=\"{{ bl.url }}\">{{ bl.title }}</a>{% endfor %}"
        "{% endblock %}"
    )
    (templates_dir / "post_index.html").write_text(
        '{% extends "base.html" %}{% block content %}'
        "{% for p in posts %}<a href=\"{{ p.url }}\">{{ p.title }}</a>{% endfor %}"
        "{% endblock %}"
    )
    (templates_dir / "wiki_index.html").write_text(
        '{% extends "base.html" %}{% block content %}'
        "{% for p in pages %}<a href=\"{{ p.url }}\">{{ p.title }}</a>{% endfor %}"
        "{% endblock %}"
    )
    (templates_dir / "category.html").write_text(
        '{% extends "base.html" %}{% block content %}'
        "<h1>{{ category }}</h1>"
        "{% for p in pages %}<a href=\"{{ p.url }}\">{{ p.title }}</a>{% endfor %}"
        "{% endblock %}"
    )
    (templates_dir / "category_index.html").write_text(
        '{% extends "base.html" %}{% block content %}'
        "{% for cat in categories %}<a href=\"/categories/{{ cat.slug }}/\">{{ cat.name }}</a>"
        "{% endfor %}{% endblock %}"
    )
    (templates_dir / "search.html").write_text(
        '{% extends "base.html" %}{% block content %}<div id="search"></div>{% endblock %}'
    )
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_builder.py -v
```

Expected: FAIL (ImportError)

**Step 3: Implement the builder**

`bliki/builder.py`:
```python
from __future__ import annotations

import logging
import shutil
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from bliki.images import process_images, rewrite_img_tags
from bliki.links import PageRegistry, build_backlinks
from bliki.models import Page, PageType
from bliki.renderer import render_markdown
from bliki.scanner import scan_content

logger = logging.getLogger(__name__)


@dataclass
class Category:
    """Represents a category with its slug and display name."""

    name: str
    slug: str
    pages: list[Page]


def build_site(
    content_dir: Path,
    output_dir: Path,
    templates_dir: Path,
    include_drafts: bool = False,
) -> None:
    """Build the complete static site.

    Args:
        content_dir: Path to content/ directory.
        output_dir: Path to write generated site to.
        templates_dir: Path to Jinja2 templates.
        include_drafts: Whether to include draft posts.
    """
    # Step 1: Scan
    pages = scan_content(content_dir, include_drafts=include_drafts)
    logger.info(f"Scanned {len(pages)} pages")

    # Step 2: Build registry and backlinks
    registry = PageRegistry(pages)
    backlinks_map = build_backlinks(pages)

    # Step 3: Render markdown and process images
    for page in pages:
        page.content_html, page.toc_html = render_markdown(
            page.content_md, registry=registry
        )

        # Process images for this page
        manifest = process_images(
            page.source_dir,
            _page_output_dir(output_dir, page),
        )
        if manifest:
            page.content_html = rewrite_img_tags(page.content_html, manifest)

        # Attach backlinks
        for bl_title, bl_sources in backlinks_map.items():
            target_page = registry.get_page(bl_title)
            if target_page and target_page is page:
                page.backlinks = bl_sources

    # Step 4: Render templates
    env = Environment(loader=FileSystemLoader(str(templates_dir)), autoescape=True)
    _render_pages(env, pages, output_dir)
    _render_indexes(env, pages, output_dir)

    # Step 5: Copy static assets
    static_src = templates_dir / "static"
    if static_src.exists():
        shutil.copytree(static_src, output_dir / "static", dirs_exist_ok=True)


def _page_output_dir(output_dir: Path, page: Page) -> Path:
    """Determine the output directory for a page.

    Args:
        output_dir: Root output directory.
        page: The page to get output dir for.

    Returns:
        Path to the page's output directory.
    """
    url = page.url.strip("/")
    out = output_dir / url
    out.mkdir(parents=True, exist_ok=True)
    return out


def _render_pages(env: Environment, pages: list[Page], output_dir: Path) -> None:
    """Render individual page HTML files.

    Args:
        env: Jinja2 environment.
        pages: All pages to render.
        output_dir: Root output directory.
    """
    post_template = env.get_template("post.html")
    wiki_template = env.get_template("wiki.html")

    for page in pages:
        template = post_template if page.page_type == PageType.POST else wiki_template
        html = template.render(page=page)
        out_dir = _page_output_dir(output_dir, page)
        (out_dir / "index.html").write_text(html)


def _render_indexes(env: Environment, pages: list[Page], output_dir: Path) -> None:
    """Render index pages: post listing, wiki listing, categories.

    Args:
        env: Jinja2 environment.
        pages: All pages.
        output_dir: Root output directory.
    """
    posts = sorted(
        [p for p in pages if p.page_type == PageType.POST],
        key=lambda p: p.date or "",
        reverse=True,
    )
    wiki_pages = sorted(
        [p for p in pages if p.page_type == PageType.WIKI],
        key=lambda p: p.title.lower(),
    )

    # Post index (homepage)
    post_index_tpl = env.get_template("post_index.html")
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "index.html").write_text(post_index_tpl.render(posts=posts))

    # Wiki index
    wiki_index_tpl = env.get_template("wiki_index.html")
    wiki_dir = output_dir / "wiki"
    wiki_dir.mkdir(parents=True, exist_ok=True)
    (wiki_dir / "index.html").write_text(wiki_index_tpl.render(pages=wiki_pages))

    # Categories
    categories_map: dict[str, list[Page]] = defaultdict(list)
    for page in pages:
        if page.category:
            categories_map[page.category].append(page)

    categories = [
        Category(name=name, slug=name.lower().replace(" ", "-"), pages=cat_pages)
        for name, cat_pages in sorted(categories_map.items())
    ]

    cat_tpl = env.get_template("category.html")
    cat_index_tpl = env.get_template("category_index.html")

    cat_root = output_dir / "categories"
    cat_root.mkdir(parents=True, exist_ok=True)
    (cat_root / "index.html").write_text(cat_index_tpl.render(categories=categories))

    for cat in categories:
        cat_dir = cat_root / cat.slug
        cat_dir.mkdir(parents=True, exist_ok=True)
        (cat_dir / "index.html").write_text(
            cat_tpl.render(category=cat.name, pages=cat.pages)
        )

    # Search page
    search_tpl = env.get_template("search.html")
    search_dir = output_dir / "search"
    search_dir.mkdir(parents=True, exist_ok=True)
    (search_dir / "index.html").write_text(search_tpl.render())
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_builder.py -v
```

Expected: all PASS

**Step 5: Commit**

```bash
git add bliki/builder.py tests/test_builder.py
git commit -m "Add build pipeline: scan, render, image processing, template output"
```

---

### Task 8: Wire up CLI commands

**Files:**
- Modify: `bliki/cli.py`
- Modify: `tests/test_cli.py`

**Step 1: Write failing tests for real CLI behavior**

Add to `tests/test_cli.py`:
```python
def test_build_command_generates_output(content_dir, tmp_path):
    """bliki build generates HTML output."""
    templates_dir = tmp_path / "templates"
    _create_minimal_templates(templates_dir)  # reuse from test_builder.py
    output_dir = tmp_path / "output"

    runner = CliRunner()
    result = runner.invoke(cli, [
        "build",
        "--content", str(content_dir),
        "--templates", str(templates_dir),
        "--output", str(output_dir),
    ])

    assert result.exit_code == 0
    assert (output_dir / "index.html").exists()


def test_new_post_scaffolds_directory(tmp_path):
    """bliki new post creates the content directory and index.md."""
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "posts").mkdir()

    runner = CliRunner()
    result = runner.invoke(cli, [
        "new", "post", "My Great Post",
        "--content", str(content_dir),
    ])

    assert result.exit_code == 0
    # Find the created directory (name includes today's date)
    posts = list((content_dir / "posts").iterdir())
    assert len(posts) == 1
    assert (posts[0] / "index.md").exists()
    content = (posts[0] / "index.md").read_text()
    assert "title: My Great Post" in content


def test_new_wiki_scaffolds_directory(tmp_path):
    """bliki new wiki creates the content directory and index.md."""
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "wiki").mkdir()

    runner = CliRunner()
    result = runner.invoke(cli, [
        "new", "wiki", "Python Tips",
        "--content", str(content_dir),
    ])

    assert result.exit_code == 0
    wiki_dir = content_dir / "wiki" / "python-tips"
    assert (wiki_dir / "index.md").exists()
    content = (wiki_dir / "index.md").read_text()
    assert "title: Python Tips" in content
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_cli.py -v
```

Expected: new tests FAIL (missing options, no real implementation)

**Step 3: Update CLI with real implementations**

Update `bliki/cli.py` to:
- `build` command: call `build_site()` with path options for `--content`, `--templates`,
  `--output`
- `new post`: create `content/posts/YYYY-MM-DD-<slug>/index.md` with front matter template
- `new wiki`: create `content/wiki/<slug>/index.md` with front matter template
- `serve`: call `build_site()` then start livereload server, watching content/ and templates/

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_cli.py -v
```

Expected: all PASS

**Step 5: Commit**

```bash
git add bliki/cli.py tests/test_cli.py
git commit -m "Wire up build, new, and serve CLI commands"
```

---

### Task 9: RSS feed generation

**Files:**
- Create: `bliki/feed.py`
- Create: `tests/test_feed.py`

**Step 1: Write failing tests**

`tests/test_feed.py`:
```python
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
    # "Python" is a wiki page title, should not appear as an <item>
    root = ET.fromstring(xml_str)
    items = root.findall(".//item/title")
    item_titles = [item.text for item in items]
    assert "Python" not in item_titles
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_feed.py -v
```

Expected: FAIL (ImportError)

**Step 3: Implement RSS generation**

`bliki/feed.py`:
```python
from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime

from bliki.models import Page, PageType


def generate_rss(
    pages: list[Page],
    site_name: str,
    site_url: str,
    site_description: str,
) -> str:
    """Generate an RSS 2.0 feed XML string from published posts.

    Args:
        pages: All pages (only posts are included in the feed).
        site_name: Name of the site for the channel title.
        site_url: Base URL of the site.
        site_description: Description for the channel.

    Returns:
        RSS 2.0 XML as a string.
    """
    posts = sorted(
        [p for p in pages if p.page_type == PageType.POST],
        key=lambda p: p.date or "",
        reverse=True,
    )

    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = site_name
    ET.SubElement(channel, "link").text = site_url
    ET.SubElement(channel, "description").text = site_description

    for post in posts:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = post.title
        ET.SubElement(item, "link").text = f"{site_url}{post.url}"
        ET.SubElement(item, "description").text = post.summary or post.title
        if post.date:
            pub_date = datetime(post.date.year, post.date.month, post.date.day)
            ET.SubElement(item, "pubDate").text = pub_date.strftime(
                "%a, %d %b %Y %H:%M:%S +0000"
            )
        if post.category:
            ET.SubElement(item, "category").text = post.category

    return ET.tostring(rss, encoding="unicode", xml_declaration=True)
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_feed.py -v
```

Expected: all PASS

**Step 5: Integrate feed generation into builder**

Add to `bliki/builder.py` `build_site()`, after rendering indexes:
```python
from bliki.feed import generate_rss
# ...
feed_xml = generate_rss(pages, site_name="Bliki", site_url="", site_description="")
(output_dir / "feed.xml").write_text(feed_xml)
```

Note: site config (name, url, description) needs to come from a config file or CLI options.
For now, use placeholder values. Config will be added in Task 10.

**Step 6: Commit**

```bash
git add bliki/feed.py tests/test_feed.py bliki/builder.py
git commit -m "Add RSS feed generation for blog posts"
```

---

### Task 10: Site configuration

**Files:**
- Create: `bliki/config.py`
- Create: `tests/test_config.py`
- Create: `bliki.yaml` (example config)
- Modify: `bliki/builder.py` (use config)
- Modify: `bliki/cli.py` (load config)

**Step 1: Write failing tests**

`tests/test_config.py`:
```python
from pathlib import Path

from bliki.config import load_config, SiteConfig


def test_load_config_from_yaml(tmp_path):
    """Load site config from YAML file."""
    config_file = tmp_path / "bliki.yaml"
    config_file.write_text(
        "name: My Bliki\n"
        "url: https://example.com\n"
        "description: A blog with wiki features\n"
        "author: Test Author\n"
    )
    config = load_config(config_file)
    assert config.name == "My Bliki"
    assert config.url == "https://example.com"
    assert config.description == "A blog with wiki features"
    assert config.author == "Test Author"


def test_load_config_defaults(tmp_path):
    """Missing config values get sensible defaults."""
    config_file = tmp_path / "bliki.yaml"
    config_file.write_text("name: Minimal\n")
    config = load_config(config_file)
    assert config.name == "Minimal"
    assert config.url == ""
    assert config.description == ""
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_config.py -v
```

Expected: FAIL (ImportError)

**Step 3: Implement config**

`bliki/config.py`:
```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class SiteConfig:
    """Site-wide configuration."""

    name: str = "Bliki"
    url: str = ""
    description: str = ""
    author: str = ""


def load_config(config_path: Path) -> SiteConfig:
    """Load site configuration from a YAML file.

    Args:
        config_path: Path to the YAML config file.

    Returns:
        SiteConfig with values from the file, defaults for missing keys.
    """
    with open(config_path) as f:
        data = yaml.safe_load(f) or {}

    return SiteConfig(
        name=data.get("name", "Bliki"),
        url=data.get("url", ""),
        description=data.get("description", ""),
        author=data.get("author", ""),
    )
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_config.py -v
```

Expected: all PASS

**Step 5: Create example config and integrate into builder/CLI**

Create `bliki.yaml` in project root:
```yaml
name: My Bliki
url: https://example.com
description: A blog with wiki features
author: Your Name
```

Update `bliki/builder.py` to accept `SiteConfig` and pass it to templates and feed generation.
Update `bliki/cli.py` to load config from `--config` option (default: `bliki.yaml`).

**Step 6: Commit**

```bash
git add bliki/config.py tests/test_config.py bliki.yaml bliki/builder.py bliki/cli.py
git commit -m "Add YAML site configuration"
```

---

### Task 11: Pagefind integration

**Files:**
- Modify: `bliki/builder.py`
- Create: `tests/test_pagefind.py`

**Step 1: Write failing test**

`tests/test_pagefind.py`:
```python
import shutil

import pytest

from bliki.builder import run_pagefind


@pytest.mark.skipif(
    shutil.which("pagefind") is None,
    reason="pagefind binary not installed",
)
def test_pagefind_creates_index(tmp_path):
    """Pagefind generates search index in output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "index.html").write_text(
        "<html><body><h1>Test</h1><p>Content</p></body></html>"
    )

    run_pagefind(output_dir)

    assert (output_dir / "pagefind").exists()
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_pagefind.py -v
```

Expected: FAIL (ImportError for run_pagefind)

**Step 3: Implement Pagefind runner**

Add to `bliki/builder.py`:
```python
import subprocess

def run_pagefind(output_dir: Path) -> None:
    """Run Pagefind to generate search index.

    Args:
        output_dir: Path to the built site output directory.
    """
    pagefind = shutil.which("pagefind")
    if not pagefind:
        logger.warning("pagefind not found in PATH -- skipping search index generation")
        return

    result = subprocess.run(
        [pagefind, "--site", str(output_dir)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        logger.error(f"Pagefind failed: {result.stderr}")
    else:
        logger.info("Search index generated")
```

Call `run_pagefind(output_dir)` at the end of `build_site()`.

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_pagefind.py -v
```

Expected: PASS (or skip if pagefind not installed)

**Step 5: Commit**

```bash
git add bliki/builder.py tests/test_pagefind.py
git commit -m "Add Pagefind integration for search index generation"
```

---

### Task 12: End-to-end integration test

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write integration test**

`tests/test_integration.py`:
```python
from pathlib import Path

from click.testing import CliRunner

from bliki.cli import cli


def test_full_build_workflow(content_dir, tmp_path):
    """Full end-to-end: scaffold content, build, verify output."""
    templates_dir = tmp_path / "templates"
    _create_minimal_templates(templates_dir)
    output_dir = tmp_path / "output"

    runner = CliRunner()

    # Build
    result = runner.invoke(cli, [
        "build",
        "--content", str(content_dir),
        "--templates", str(templates_dir),
        "--output", str(output_dir),
    ])
    assert result.exit_code == 0

    # Verify structure
    assert (output_dir / "index.html").exists()
    assert (output_dir / "wiki" / "index.html").exists()
    assert (output_dir / "categories" / "index.html").exists()
    assert (output_dir / "feed.xml").exists()

    # Verify wiki links resolved
    post_html = (
        output_dir / "posts" / "2026" / "02" / "first-post" / "index.html"
    ).read_text()
    assert "/wiki/python/" in post_html

    # Verify backlinks
    wiki_html = (output_dir / "wiki" / "python" / "index.html").read_text()
    assert "First Post" in wiki_html
```

Reuse `_create_minimal_templates` helper (extract to conftest.py if needed).

**Step 2: Run test**

```bash
pytest tests/test_integration.py -v
```

Expected: PASS

**Step 3: Run full test suite with coverage**

```bash
pytest --cov=bliki --cov-report=term-missing -v
```

Target: 75%+ coverage

**Step 4: Commit**

```bash
git add tests/test_integration.py tests/conftest.py
git commit -m "Add end-to-end integration test"
```
