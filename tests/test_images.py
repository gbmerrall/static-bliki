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


def test_process_images_skips_corrupt_file(tmp_path):
    """A corrupt image file is skipped with a warning rather than crashing the build."""
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "corrupt.jpg").write_bytes(b"not a real image")

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    manifest = process_images(source_dir, output_dir)
    assert "corrupt.jpg" not in manifest


def test_rewrite_img_tags_with_relative_path_src():
    """Img tags with a relative path src (e.g. './hero.jpg') match the manifest by basename."""
    html = '<p><img alt="Hero" src="./hero.jpg"></p>'
    manifest = {
        "hero.jpg": {
            "original": "hero.jpg",
            "variants": [{"src": "hero-600.webp", "width": 600, "format": "webp"}],
        }
    }
    result = rewrite_img_tags(html, manifest)
    assert "<picture>" in result
    assert "hero-600.webp" in result
