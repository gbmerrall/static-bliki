# A bliki

A bliki is a hybrid website combining a blog and a wiki, often used to create a personal or 
collaborative knowledge base with chronological updates. The term, coined by Ward Cunningham, uses blog-style 
reverse chronological entries for quick updates while maintaining a wiki-like structure of linked pages 
for more expanded content.  See [Martin Fowlers page](https://martinfowler.com/bliki/WhatIsaBliki.html).

This is one I've whipped up to scartch the itch as a static site generator.  
Posts are date-stamped entries; wiki pages are evergreen reference notes. The two link to each other 
using `[[wiki link]]` syntax, and backlinks are tracked automatically so every page shows what else points to it.

Features:

- Blog posts organised by date and category
- Wiki pages with bidirectional backlinks
- `[[Page Name]]` and `[[Page Name|display text]]` wiki link syntax
- Broken links flagged with a CSS class rather than crashing the build
- Automatic image optimisation: WebP variants at 600w and 1200w, `<picture>` srcset rewriting
- RSS feed at `/feed.xml`
- Client-side search via [Pagefind](https://pagefind.app) (optional — skipped if not installed)
- Live-reload development server


## Setup

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone <repo>
cd bliki
uv sync
```

Copy `bliki.yaml` and edit it:

```yaml
name: My Site
url: https://example.com
description: A short description.
author: Your Name
```

The default content directory is `content/`, with `content/posts/` and `content/wiki/` subdirectories. Templates live in `templates/`.


## Keeping your content separate

Bliki is designed to be used as a standalone tool with your content in a separate repository. This keeps the generator clean for others to use while your posts and wiki pages stay under their own version control (and can be private).

A typical content repo looks like this:

```
my-site/
  content/
    posts/
    wiki/
  templates/
  bliki.yaml
  deploy.sh
```

Bliki needs a `templates/` directory to render pages. Copy the default templates from the bliki repo once to get started:

```bash
cp -r /path/to/bliki/templates ./templates
```

Commit them to your content repo — this also gives you full control to customise the look of your site.

Install bliki as a dependency by adding a `pyproject.toml`:

```toml
[project]
name = "my-site"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "bliki @ git+https://github.com/your-username/bliki.git",
]
```

Then `uv sync` in your content repo pulls in bliki, and your deploy script drives everything:

```bash
#!/bin/bash
set -e
CONTENT_DIR="$(cd "$(dirname "$0")/content" && pwd)"
uv run bliki build --content "$CONTENT_DIR"
rsync -avz --delete output/ user@host:/var/www/mysite/
```

Run `./deploy.sh` from the content repo to build and publish. Use `uv run bliki serve --content content/` for local preview.


## Writing and publishing

### Create a new post

```bash
uv run bliki new post "My Post Title"
```

This creates `content/posts/YYYY-MM-DD-my-post-title/index.md` with frontmatter pre-filled and `draft: true`. Write your post in that file, then set `draft: false` when ready to publish.

Post frontmatter fields:

| Field | Required | Description |
|-------|----------|-------------|
| `title` | yes | Display title |
| `date` | yes | ISO date, e.g. `2026-03-01` |
| `draft` | yes | Set to `false` to publish |
| `category` | no | Groups posts on the category index |
| `summary` | no | Used in the RSS feed description |

### Create a new wiki page

```bash
uv run bliki new wiki "Topic Name"
```

Creates `content/wiki/topic-name/index.md`. Wiki pages have no date and are never drafts.

### Link between pages

Use `[[Page Title]]` anywhere in Markdown to link to another page by its title (case-insensitive). Use `[[Page Title|display text]]` for custom link text. Backlinks are computed automatically at build time.

### Add images to a post

Place image files in the same directory as the post's `index.md`:

```
content/posts/2026-03-01-my-post/
    index.md
    hero.jpg
    diagram.png
```

Reference them with standard Markdown syntax:

```markdown
![A descriptive alt text](hero.jpg)
```

At build time, bliki automatically:

1. Copies the original image to the output directory
2. Generates resized WebP variants at 600px and 1200px wide (only if the source is wider than the target)
3. Rewrites the `<img>` tag to a `<picture>` element with a `srcset`, keeping the original as the fallback

The resulting HTML looks like:

```html
<picture>
  <source type="image/webp" srcset="hero-600.webp 600w, hero-1200.webp 1200w">
  <img alt="A descriptive alt text" src="hero.jpg">
</picture>
```

No configuration is needed. Supported formats: JPEG, PNG, GIF, WebP.

### Markdown reference

The following Markdown extensions are active on all pages:

| Syntax | Extension |
|--------|-----------|
| `` ```python `` fenced code blocks | `fenced_code` |
| Syntax highlighting on fenced blocks | `codehilite` (via Pygments) |
| `\| col \| col \|` GFM-style tables | `tables` |
| `[[Page Title]]` wiki links | `wikilinks` |
| `[[Page Title\|display text]]` wiki links with custom text | built-in pre-processor |
| Heading anchors and `[TOC]` tag | `toc` (with permalink anchors) |

Code blocks are highlighted using Pygments and wrapped in a `<div class="highlight">`. The specific language is declared in the fence:

````markdown
```python
def hello():
    return "world"
```
````

### Build and preview

```bash
uv run bliki serve              # live-reload dev server on http://localhost:8000
uv run bliki serve --drafts     # include draft posts in the preview
uv run bliki serve --port 9000  # use a different port

uv run bliki build              # production build to output/
uv run bliki build --drafts     # production build including drafts
```

Built output goes to `output/` by default. Deploy the contents of that directory to any static host.

> **Note:** new posts created with `bliki new post` are set to `draft: true` by default and will not appear until you either set `draft: false` in the frontmatter or run the server with `--drafts`.


## Theming

Templates live in `templates/` and use Jinja2. The stylesheet is `templates/static/css/main.css`.

### CSS custom properties

All colours are defined as CSS variables at the top of `main.css` and can be changed in one place:

```css
:root {
    --primary-color: #2563eb;
    --text-color: #1f2937;
    --background-color: #ffffff;
    --secondary-background: #f3f4f6;
    --border-color: #e5e7eb;
    --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
```

### Dark mode

Dark mode is implemented via `[data-theme="dark"]` overrides that re-define the same variables. The toggle is handled in `templates/static/js/main.js` and stores the preference in `localStorage`. No additional configuration is needed.

### Layout

`templates/base.html` defines the outer shell: sticky header with site title and nav links (Posts / Wiki / Categories / Search), a centred `<main>` content area, and a footer showing the author name from `bliki.yaml`.

Each page type has its own template that extends `base.html`:

| Template | Used for |
|----------|----------|
| `post.html` | Individual blog posts |
| `wiki.html` | Individual wiki pages |
| `post_index.html` | Homepage (post listing) |
| `wiki_index.html` | `/wiki/` index |
| `category.html` | Per-category post listing |
| `category_index.html` | `/categories/` overview |
| `search.html` | `/search/` page (Pagefind UI) |

Everything in `templates/static/` (CSS, JS, images) is copied verbatim to `output/static/` at build time, so adding fonts, icons, or additional stylesheets is just a matter of dropping files there.


## Code overview

The build pipeline runs in `bliki/builder.py` as a sequence of steps:

1. **Scan** (`scanner.py`) — walks `content/posts/` and `content/wiki/`, parses YAML frontmatter, and returns a list of `Page` objects.
2. **Registry + backlinks** (`links.py`) — builds a case-insensitive title-to-URL index (`PageRegistry`) and scans all pages for outgoing `[[wiki links]]` to construct a backlinks map.
3. **Render** (`renderer.py`) — converts each page's Markdown to HTML. A single `Renderer` instance is reused across all pages (resetting between each) to avoid re-initialising the Markdown extensions on every call. Display-text links (`[[Title|text]]`) are pre-processed before the standard wikilinks extension runs.
4. **Images** (`images.py`) — copies source images to the output directory, generates resized WebP variants, and rewrites `<img>` tags as `<picture>` elements with `srcset`.
5. **Templates** — Jinja2 renders each page, then the index pages (post list, wiki list, per-category pages, search).
6. **Static assets** — `templates/static/` is copied verbatim to the output.
7. **Search + feed** — Pagefind builds a client-side search index (if available); `feed.py` writes `feed.xml`.

Key data structures:

- `Page` (`models.py`) — central dataclass. Fields set from frontmatter at scan time; `content_html`, `toc_html`, and `backlinks` are populated by the builder before templates are rendered.
- `SiteConfig` (`config.py`) — loaded from `bliki.yaml`, passed to every template as `site`.
- `PageRegistry` (`links.py`) — in-memory title index; must be fully populated before rendering begins so that all links can be resolved in a single pass.
