from click.testing import CliRunner

from bliki.cli import _slugify, cli
from tests.conftest import create_minimal_templates


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


def test_build_command_generates_output(content_dir, tmp_path):
    """bliki build generates HTML output."""
    templates_dir = tmp_path / "templates"
    create_minimal_templates(templates_dir)
    output_dir = tmp_path / "output"

    runner = CliRunner()
    result = runner.invoke(cli, [
        "build",
        "--content", str(content_dir),
        "--templates", str(templates_dir),
        "--output", str(output_dir),
    ])

    assert result.exit_code == 0, result.output
    assert (output_dir / "index.html").exists()


def test_new_post_scaffolds_directory(tmp_path):
    """bliki new post creates the content directory and index.md."""
    content_dir = tmp_path / "content"
    (content_dir / "posts").mkdir(parents=True)

    runner = CliRunner()
    result = runner.invoke(cli, [
        "new", "post", "My Great Post",
        "--content", str(content_dir),
    ])

    assert result.exit_code == 0, result.output
    posts = list((content_dir / "posts").iterdir())
    assert len(posts) == 1
    assert (posts[0] / "index.md").exists()
    content = (posts[0] / "index.md").read_text()
    assert "title: My Great Post" in content


def test_new_wiki_scaffolds_directory(tmp_path):
    """bliki new wiki creates the content directory and index.md."""
    content_dir = tmp_path / "content"
    (content_dir / "wiki").mkdir(parents=True)

    runner = CliRunner()
    result = runner.invoke(cli, [
        "new", "wiki", "Python Tips",
        "--content", str(content_dir),
    ])

    assert result.exit_code == 0, result.output
    wiki_dir = content_dir / "wiki" / "python-tips"
    assert (wiki_dir / "index.md").exists()
    content = (wiki_dir / "index.md").read_text()
    assert "title: Python Tips" in content


def test_serve_help_shows_drafts_flag():
    """serve command exposes a --drafts flag."""
    runner = CliRunner()
    result = runner.invoke(cli, ["serve", "--help"])
    assert "--drafts" in result.output


def test_serve_passes_drafts_flag_to_build(tmp_path):
    """serve --drafts passes include_drafts=True to build_site."""
    from unittest.mock import MagicMock, patch

    with patch("bliki.cli.build_site") as mock_build, \
         patch("livereload.Server") as mock_server_cls:
        mock_server_cls.return_value = MagicMock()

        runner = CliRunner()
        runner.invoke(cli, [
            "serve", "--drafts",
            "--content", str(tmp_path),
            "--templates", str(tmp_path),
            "--output", str(tmp_path),
        ])

    assert mock_build.called
    _, kwargs = mock_build.call_args
    assert kwargs.get("include_drafts") is True


def test_new_post_slug_from_title(tmp_path):
    """Post directory name is derived from the title slug and today's date."""
    content_dir = tmp_path / "content"
    (content_dir / "posts").mkdir(parents=True)

    runner = CliRunner()
    runner.invoke(cli, [
        "new", "post", "Hello World",
        "--content", str(content_dir),
    ])

    posts = list((content_dir / "posts").iterdir())
    assert len(posts) == 1
    # Directory name should be YYYY-MM-DD-hello-world
    assert posts[0].name.endswith("-hello-world")
    # Verify date prefix format: 4 digits, dash, 2 digits, dash, 2 digits
    parts = posts[0].name.split("-")
    assert len(parts[0]) == 4 and parts[0].isdigit()


# --- _slugify unit tests ---

def test_slugify_basic():
    assert _slugify("Hello World") == "hello-world"


def test_slugify_already_lowercase():
    assert _slugify("python tips") == "python-tips"


def test_slugify_strips_special_chars():
    assert _slugify("What's New?") == "whats-new"


def test_slugify_collapses_multiple_spaces():
    assert _slugify("too   many   spaces") == "too-many-spaces"


def test_slugify_replaces_underscores():
    assert _slugify("snake_case_title") == "snake-case-title"


def test_slugify_strips_leading_trailing_hyphens():
    assert _slugify("-leading and trailing-") == "leading-and-trailing"


def test_slugify_numbers_preserved():
    assert _slugify("Python 3.12 Release") == "python-312-release"


def test_slugify_empty_string():
    assert _slugify("") == ""
