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
