# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Run a single test file
uv run pytest tests/test_builder.py

# Run a single test
uv run pytest tests/test_builder.py::test_function_name

# Run tests with coverage
uv run pytest --cov

# Build the site
uv run bliki build

# Development server with live reload
uv run bliki serve

# Create new content
uv run bliki new post "Title"
uv run bliki new wiki "Title"
```

No dedicated linter/formatter is configured. Use `ruff` if adding one.

## Architecture

Bliki is a static site generator (blog + wiki). The core is a sequential build pipeline in `bliki/builder.py`:

1. **Scan** (`scanner.py`) — discovers posts and wiki pages from the content directory, loading frontmatter into `Page` objects
2. **Registry** (`links.py`) — builds a `PageRegistry` for case-insensitive title-to-URL resolution
3. **Backlinks** (`links.py`) — parses all pages to extract `[[WikiLink]]` references and builds bidirectional backlink maps
4. **Render** (`renderer.py`) — converts Markdown to HTML; wiki links `[[Title]]` and `[[Title|display text]]` are resolved via the registry
5. **Images** (`images.py`) — copies images to output, generates WebP variants, rewrites `<img>` tags with responsive `srcset`
6. **Templates** (`builder.py`) — Jinja2 renders each page, index, category, search, and feed using templates in `templates/`
7. **Search** (`pagefind.py`) — optionally runs the `pagefind` CLI to build a client-side search index

**Key data flow:** `Page` (models.py) is the central dataclass — created by the scanner, enriched with backlinks, passed through rendering, and handed to Jinja2 templates.

**`PageRegistry`** is critical: it enables wiki links to resolve titles to URLs and must be fully populated before any rendering begins.

**Site config** lives in `bliki.yaml` and is loaded into `SiteConfig` (config.py) — passed to all templates as `site`.

**Templates** in `templates/` are Jinja2. The `templates/static/` directory is copied verbatim to output.
