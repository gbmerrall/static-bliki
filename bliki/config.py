from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class SiteConfig:
    """Site-wide configuration loaded from bliki.yaml."""

    name: str = "Bliki"
    url: str = ""
    description: str = ""
    author: str = ""


def load_config(config_path: Path) -> SiteConfig:
    """Load site configuration from a YAML file.

    Args:
        config_path: Path to the YAML config file.

    Returns:
        SiteConfig with values from the file, dataclass defaults for missing keys.
    """
    with open(config_path) as f:
        data = yaml.safe_load(f) or {}

    known_fields = {"name", "url", "description", "author"}
    kwargs = {k: v for k, v in data.items() if k in known_fields}
    return SiteConfig(**kwargs)
