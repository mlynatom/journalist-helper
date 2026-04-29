"""Parser for nehody-uzavirky.cz traffic incidents and closures."""

import html
import logging
import re
from datetime import datetime

import requests

from src.schemas import NewsItem, Source

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (compatible; journalist-helper/1.0; +https://github.com/journalist-helper)"
)
KOLIN_OKRES_VALUE = "73"


def fetch_kolin_page(feed_source: Source) -> tuple[str, int | None, str | None]:
    """Fetch the Kolín-selected page using the site's POST filter."""
    try:
        response = requests.post(
            feed_source.url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
            data={"di-okres": KOLIN_OKRES_VALUE, "di-submit": "zobrazit"},
            timeout=60,
        )
        response.raise_for_status()
        return response.text, response.status_code, response.headers.get("Content-Type")
    except requests.RequestException as exc:
        msg = f"Failed to fetch Kolín incidents from {feed_source.url}: {exc}"
        raise RuntimeError(msg) from exc


def normalize_text(fragment: str) -> str:
    """Collapse HTML fragments into a readable single string."""
    fragment = re.sub(r"<br\s*/?>", "\n", fragment, flags=re.IGNORECASE)
    fragment = re.sub(r"<[^>]+>", "", fragment)
    lines = [re.sub(r"\s+", " ", html.unescape(line)).strip() for line in fragment.splitlines()]
    return " | ".join(line for line in lines if line)


def parse_published_at(date_text: str | None, time_text: str | None) -> datetime | None:
    """Parse the incident or closure start time from the page metadata."""
    if not date_text:
        return None

    start_time = (time_text or "").split("-", 1)[0].strip()
    try:
        if start_time:
            return datetime.strptime(f"{date_text.strip()} {start_time}", "%d.%m.%Y %H:%M")  # noqa: DTZ007
        return datetime.strptime(date_text.strip(), "%d.%m.%Y")  # noqa: DTZ007
    except ValueError:
        return None


def parse_date_block(block_html: str) -> tuple[str | None, str | None]:
    """Extract the date block from a traffic card."""
    date_block_match = re.search(
        r'<div class="date"><div class="t-right">(.*?)</div></div>',
        block_html,
        flags=re.DOTALL,
    )
    if not date_block_match:
        return None, None

    date_block = normalize_text(date_block_match.group(1))

    incident_match = re.search(
        r"(?P<date>\d{1,2}\.\d{1,2}\.\d{4})\s+(?P<start>\d{1,2}:\d{2})\s*-\s*(?P<end>\d{1,2}:\d{2})",
        date_block,
    )
    if incident_match:
        return incident_match.group("date"), incident_match.group("start")

    closure_match = re.search(
        r"Od:\s*(?P<start_date>\d{1,2}\.\d{1,2}\.\d{4})(?:\s*[•·]\s*(?P<start_time>\d{1,2}:\d{2}))?.*?Do:\s*(?P<end_date>\d{1,2}\.\d{1,2}\.\d{4})(?:\s*[•·]\s*(?P<end_time>\d{1,2}:\d{2}))?",
        date_block,
    )
    if closure_match:
        return closure_match.group("start_date"), closure_match.group("start_time")

    bare_date_match = re.search(r"(\d{1,2}\.\d{1,2}\.\d{4})", date_block)
    if bare_date_match:
        return bare_date_match.group(1), None

    return None, None


def parse_traffic_block(block_html: str, source: Source, page_url: str) -> NewsItem | None:
    """Parse one incident card into a NewsItem."""
    box_id_match = re.search(r'id="(bdi-[^"]+)"', block_html)
    title_match = re.search(r"<h2>(.*?)</h2>", block_html, flags=re.DOTALL)
    description_match = re.search(
        r'<div class="hidden" id="[^"]+"><p>(.*?)</p>', block_html, flags=re.DOTALL
    )

    if not title_match:
        return None

    title = normalize_text(title_match.group(1))
    description = normalize_text(description_match.group(1)) if description_match else ""
    date_text, time_text = parse_date_block(block_html)
    published_at = parse_published_at(date_text, time_text)
    box_id = box_id_match.group(1) if box_id_match else ""
    link = f"{page_url}#{box_id}" if box_id else page_url

    return NewsItem(
        source=source.name,
        title=title,
        link=link,
        published_at=published_at,
        description=description,
        always_relevant=source.always_relevant,
    )


def parse_nehody_uzavirky_page(feed_source: Source) -> list[NewsItem]:
    """Parse Kolín incidents from nehody-uzavirky.cz."""
    page_html, status, content_type = fetch_kolin_page(feed_source)
    box_segments = page_html.split('<div class="cols doprava-box"')

    if len(box_segments) <= 1:
        logger.warning(
            "Kolín page returned no incident boxes, status=%s, content-type=%s",
            status,
            content_type,
        )
        return []

    news_items: list[NewsItem] = []
    page_url = feed_source.url.rstrip("/")
    for segment in box_segments[1:]:
        block_html = '<div class="cols doprava-box"' + segment
        news_item = parse_traffic_block(block_html, feed_source, page_url)
        if news_item is not None:
            news_items.append(news_item)

    if not news_items:
        logger.warning(
            "Kolín page did not yield any parseable incident boxes, status=%s, content-type=%s",
            status,
            content_type,
        )

    return news_items
