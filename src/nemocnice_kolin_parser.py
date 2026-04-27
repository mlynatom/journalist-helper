"""Parser for Nemocnice Kolin document overview page."""

from datetime import datetime
import html
import importlib
import logging
import re
from urllib.parse import urljoin

import requests

try:
    from src.schemas import NewsItem, Source
except ModuleNotFoundError:  # Allows `uv run src/nemocnice_kolin_parser.py`
    schemas = importlib.import_module("schemas")
    NewsItem = schemas.NewsItem
    Source = schemas.Source


logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (compatible; journalist-helper/1.0; +https://github.com/journalist-helper)"
DETAIL_TIMEOUT = 20
DETAIL_MAX_CHARS = 700


def fetch_documents_page(feed_source: Source) -> tuple[str, int | None, str | None]:
    """Fetch Nemocnice Kolin document overview page."""
    try:
        response = requests.get(
            feed_source.url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
            timeout=60,
        )
        response.raise_for_status()
        return response.text, response.status_code, response.headers.get("Content-Type")
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to fetch Nemocnice Kolin page {feed_source.url}: {exc}") from exc


def normalize_text(value: str) -> str:
    """Clean up HTML entities and compress whitespace."""
    text = re.sub(r"<[^>]+>", " ", value)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def parse_embedded_date(text: str) -> datetime | None:
    """Parse first date found in item description when available."""
    match = re.search(r"(\d{1,2})\.?\s*(\d{1,2})\.?\s*(\d{4})", text)
    if not match:
        return None

    day, month, year = match.groups()
    try:
        return datetime(int(year), int(month), int(day))
    except ValueError:
        return None


def fetch_detail_page(url: str, session: requests.Session) -> str:
    """Fetch a detail page and return HTML content."""
    try:
        response = session.get(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
            timeout=DETAIL_TIMEOUT,
        )
        response.raise_for_status()
        return response.text
    except requests.RequestException as exc:
        logger.warning("Failed to fetch detail page %s: %s", url, exc)
        return ""


def trim_description(text: str) -> str:
    """Limit description length for downstream triage readability."""
    if len(text) <= DETAIL_MAX_CHARS:
        return text
    return text[: DETAIL_MAX_CHARS - 1].rstrip() + "..."


def extract_detail_description(detail_html: str) -> str:
    """Extract article description/body text from a detail page HTML."""
    if not detail_html:
        return ""

    # Restrict parsing to the actual document detail block.
    content_match = re.search(
        r'<div class="obsah"\s+id="dokument">(?P<content>.*?)<div class="popis dpopis">',
        detail_html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    content_html = content_match.group("content") if content_match else detail_html

    editor_match = re.search(
        r'<div class="editor[^\"]*">(?P<editor>.*?)</div>\s*<div class="sf">',
        content_html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    editor_html = editor_match.group("editor") if editor_match else content_html

    def looks_like_navigation(text: str) -> bool:
        lowered = text.casefold()
        navigation_markers = (
            "nabídka menu",
            "hlavní nabídka",
            "přeskočit nabídku",
            "pro pacienty",
            "odborná veřejnost",
            "praktické informace",
        )
        return any(marker in lowered for marker in navigation_markers)

    # Prefer teaser/intro blocks when available.
    intro_patterns = [
        r'<div[^>]+class="[^"]*perex[^"]*"[^>]*>(?P<text>.*?)</div>',
        r'<div[^>]+class="[^"]*anotac[^"]*"[^>]*>(?P<text>.*?)</div>',
        r'<p[^>]+class="[^"]*perex[^"]*"[^>]*>(?P<text>.*?)</p>',
    ]
    for pattern in intro_patterns:
        match = re.search(pattern, editor_html, flags=re.IGNORECASE | re.DOTALL)
        if match:
            text = normalize_text(match.group("text"))
            if text and not looks_like_navigation(text):
                return trim_description(text)

    # Fallback to first meaningful paragraph from the editor content.
    for paragraph in re.finditer(r"<p[^>]*>(?P<text>.*?)</p>", editor_html, flags=re.IGNORECASE | re.DOTALL):
        text = normalize_text(paragraph.group("text"))
        if text and len(text) > 20 and not looks_like_navigation(text):
            return trim_description(text)

    # Last fallback: HTML metadata description.
    meta_match = re.search(
        r'<meta\s+name="description"\s+content="(?P<text>[^"]+)"',
        detail_html,
        flags=re.IGNORECASE,
    )
    if meta_match:
        text = normalize_text(meta_match.group("text"))
        if text:
            return trim_description(text)

    return ""


def parse_nemocnice_kolin_page(feed_source: Source) -> list[NewsItem]:
    """Parse Nemocnice Kolin document cards into NewsItem entries."""
    page_html, status, content_type = fetch_documents_page(feed_source)

    # Each item is represented by a content link ending with /d-<id>.
    item_pattern = re.compile(
        r'<a[^>]+href="(?P<href>[^"]*/d-\d+[^"]*)"[^>]*>(?P<title>.*?)</a>(?P<tail>.*?)(?=<a[^>]+href="[^"]*/d-\d+[^"]*"|Zobrazeno je|</main>|$)',
        flags=re.IGNORECASE | re.DOTALL,
    )

    news_items: list[NewsItem] = []
    seen_links: set[str] = set()

    with requests.Session() as session:
        for match in item_pattern.finditer(page_html):
            href = match.group("href")
            if "/d-" not in href:
                continue

            link = urljoin(feed_source.url, href)
            if link in seen_links:
                continue

            title = normalize_text(match.group("title"))
            if not title:
                continue

            tail = match.group("tail")
            if "Složka dokumentů:" not in tail:
                continue

            # Keep listing text as fallback, prefer text extracted from the detail page.
            description_part = tail.split("Složka dokumentů:", 1)[0]
            listing_description = normalize_text(description_part)
            detail_html = fetch_detail_page(link, session)
            detail_description = extract_detail_description(detail_html)
            description = detail_description or listing_description
            published_at = parse_embedded_date(description) or parse_embedded_date(listing_description)

            news_items.append(
                NewsItem(
                    source=feed_source.name,
                    title=title,
                    link=link,
                    published_at=published_at,
                    description=description,
                    always_relevant=feed_source.always_relevant,
                )
            )
            seen_links.add(link)

    if not news_items:
        logger.warning(
            "Nemocnice Kolin page returned no parseable cards, status=%s, content-type=%s",
            status,
            content_type,
        )

    return news_items

if __name__ == "__main__":
    source = Source(name="Nemocnice Kolín - dokumenty", url="https://www.nemocnicekolin.cz/dp", always_relevant=True)
    parsed_news_items = parse_nemocnice_kolin_page(source)

    print(parsed_news_items)
