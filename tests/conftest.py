from pathlib import Path

import pytest


def create_minimal_templates(templates_dir: Path) -> None:
    """Create minimal Jinja2 templates sufficient for build pipeline tests.

    Used by test_builder, test_cli, and test_integration. Kept here to
    avoid duplication across test modules.
    """
    templates_dir.mkdir(parents=True, exist_ok=True)

    (templates_dir / "base.html").write_text(
        "<!DOCTYPE html><html><body>{% block content %}{% endblock %}</body></html>"
    )
    (templates_dir / "post.html").write_text(
        '{% extends "base.html" %}{% block content %}'
        "<h1>{{ page.title }}</h1>{{ page.content_html | safe }}"
        '{% for bl in page.backlinks %}<a href="{{ bl.url }}">{{ bl.title }}</a>{% endfor %}'
        "{% endblock %}"
    )
    (templates_dir / "wiki.html").write_text(
        '{% extends "base.html" %}{% block content %}'
        "<h1>{{ page.title }}</h1>{{ page.content_html | safe }}"
        '{% for bl in page.backlinks %}<a href="{{ bl.url }}">{{ bl.title }}</a>{% endfor %}'
        "{% endblock %}"
    )
    (templates_dir / "post_index.html").write_text(
        '{% extends "base.html" %}{% block content %}'
        '{% for p in posts %}<a href="{{ p.url }}">{{ p.title }}</a>{% endfor %}'
        "{% endblock %}"
    )
    (templates_dir / "wiki_index.html").write_text(
        '{% extends "base.html" %}{% block content %}'
        '{% for p in pages %}<a href="{{ p.url }}">{{ p.title }}</a>{% endfor %}'
        "{% endblock %}"
    )
    (templates_dir / "category.html").write_text(
        '{% extends "base.html" %}{% block content %}'
        "<h1>{{ category }}</h1>"
        '{% for p in pages %}<a href="{{ p.url }}">{{ p.title }}</a>{% endfor %}'
        "{% endblock %}"
    )
    (templates_dir / "category_index.html").write_text(
        '{% extends "base.html" %}{% block content %}'
        '{% for cat in categories %}<a href="/categories/{{ cat.slug }}/">{{ cat.name }}</a>'
        "{% endfor %}{% endblock %}"
    )
    (templates_dir / "search.html").write_text(
        '{% extends "base.html" %}{% block content %}<div id="search"></div>{% endblock %}'
    )


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
