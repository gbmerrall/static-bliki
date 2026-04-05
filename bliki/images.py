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

        try:
            img = Image.open(file_path)
        except Exception as exc:
            logger.warning(f"Skipping image '{file_path.name}': {exc}")
            continue

        with img:
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
        src = Path(src).name  # normalize relative paths (e.g. "./hero.jpg") to bare filename
        if src not in manifest:
            return full_tag

        info = manifest[src]
        alt_match = re.search(r'alt="([^"]*)"', full_tag)
        alt = alt_match.group(1) if alt_match else ""

        srcset_parts = [f'{v["src"]} {v["width"]}w' for v in info["variants"]]
        srcset = ", ".join(srcset_parts)

        return (
            f"<picture>"
            f'<source type="image/webp" srcset="{srcset}">'
            f'<img alt="{alt}" src="{info["original"]}">'
            f"</picture>"
        )

    return re.sub(r"<img[^>]+>", _replace_img, html)
