from click.testing import CliRunner

from bliki.cli import cli
from tests.conftest import create_minimal_templates


def test_full_build_workflow(content_dir, tmp_path):
    """Full end-to-end: scaffold content, build, verify output."""
    templates_dir = tmp_path / "templates"
    create_minimal_templates(templates_dir)
    output_dir = tmp_path / "output"

    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "build",
            "--content", str(content_dir),
            "--templates", str(templates_dir),
            "--output", str(output_dir),
        ],
    )
    assert result.exit_code == 0, result.output

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
