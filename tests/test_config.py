from bliki.config import SiteConfig, load_config


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
    assert config.author == ""


def test_load_config_empty_file(tmp_path):
    """Empty config file returns all defaults."""
    config_file = tmp_path / "bliki.yaml"
    config_file.write_text("")
    config = load_config(config_file)
    assert config.name == "Bliki"
    assert config.url == ""
