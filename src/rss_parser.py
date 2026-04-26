"""Functions for parsing RSS feeds."""

from datetime import datetime
from email.utils import parsedate_to_datetime

import logging

import feedparser
import requests

from src.schemas import Incident, Source


logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (compatible; journalist-helper/1.0; +https://github.com/journalist-helper)"


def fetch_feed(feed_source: Source) -> tuple[bytes, int | None, str | None]:
    """Fetch a feed with explicit headers so failures are easier to diagnose."""
    try:
        response = requests.get(
            feed_source.url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8",
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.content, response.status_code, response.headers.get("Content-Type")
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to fetch RSS feed {feed_source.url}: {exc}") from exc


def parse_pubdate(value: str | None) -> datetime | None:
    """Parse a publication date from an RSS feed entry."""
    if not value:
        return None
    try:
        return parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None


def parse_rss_feed(feed_source: Source) -> list[Incident]:
    """Parse an RSS feed and return a list of entries."""
    feed_data, status, content_type = fetch_feed(feed_source)
    feed: dict = feedparser.parse(feed_data)

    if feed.get("bozo"):
        logger.warning(
            "RSS feed %s parsed with bozo=%s, status=%s, content-type=%s: %r",
            feed_source.url,
            feed.get("bozo"),
            status,
            content_type,
            feed.get("bozo_exception"),
        )

    if not feed.get("entries"):
        logger.warning(
            "RSS feed %s returned no entries, status=%s, content-type=%s",
            feed_source.url,
            status,
            content_type,
        )

    entries = feed.get("entries", [])
    incident_list = []
    for entry in entries:
        incident_list.append(
            Incident(
                source=feed_source.name,
                title=entry.get("title", ""),
                link=entry.get("link", ""),
                published_at=parse_pubdate(entry.get("published")),
                description=entry.get("summary", ""),
            )
        )

    return incident_list


if __name__ == "__main__":
    source = Source(name="České noviny - ČR", url="https://www.ceskenoviny.cz/sluzby/rss/cr.php")
    incidents = parse_rss_feed(source)

    print(incidents)
