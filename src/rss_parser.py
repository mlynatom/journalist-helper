"""Functions for parsing RSS feeds."""

from datetime import datetime
from email.utils import parsedate_to_datetime

import feedparser

try:
    from src.schemas import Incident, Source
except ModuleNotFoundError:
    # Allows running this file directly: python src/rss_parser.py
    from schemas import Incident, Source


def parse_pubdate(value: str | None) -> datetime | None:
    """Parse a publication date from an RSS feed entry."""
    if not value:
        return None
    try:
        return parsedate_to_datetime(value)
    except TypeError, ValueError:
        return None


def parse_rss_feed(source: Source) -> list[Incident]:
    """Parse an RSS feed and return a list of entries."""
    feed: dict = feedparser.parse(source.url)

    entries = feed.get("entries", [])
    incidents = []
    for entry in entries:
        incidents.append(
            Incident(
                source=source.name,
                title=entry.get("title", ""),
                link=entry.get("link", ""),
                published_at=parse_pubdate(entry.get("published")),
                description=entry.get("summary", ""),
            )
        )

    return incidents


if __name__ == "__main__":
    source = Source(name="České noviny - ČR", url="https://www.ceskenoviny.cz/sluzby/rss/cr.php")
    incidents = parse_rss_feed(source)

    print(incidents)
