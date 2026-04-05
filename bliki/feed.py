from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime

from bliki.models import Page, PageType


def generate_rss(
    pages: list[Page],
    site_name: str,
    site_url: str,
    site_description: str,
) -> str:
    """Generate an RSS 2.0 feed XML string from published posts.

    Args:
        pages: All pages (only posts are included in the feed).
        site_name: Name of the site for the channel title.
        site_url: Base URL of the site (no trailing slash).
        site_description: Description for the channel.

    Returns:
        RSS 2.0 XML as a string.
    """
    posts = sorted(
        [p for p in pages if p.page_type == PageType.POST and p.date],
        key=lambda p: p.date,
        reverse=True,
    )

    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = site_name
    ET.SubElement(channel, "link").text = site_url
    ET.SubElement(channel, "description").text = site_description

    for post in posts:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = post.title
        ET.SubElement(item, "link").text = f"{site_url}{post.url}"
        ET.SubElement(item, "guid").text = f"{site_url}{post.url}"
        ET.SubElement(item, "description").text = post.summary or post.title
        assert post.date is not None  # filtered by p.date above
        pub_date = datetime(post.date.year, post.date.month, post.date.day)
        ET.SubElement(item, "pubDate").text = pub_date.strftime(
            "%a, %d %b %Y %H:%M:%S +0000"
        )
        if post.category:
            ET.SubElement(item, "category").text = post.category

    return ET.tostring(rss, encoding="unicode", xml_declaration=True)
