"""Functions for parsing RSS feeds."""

from datetime import datetime
from email.utils import parsedate_to_datetime
from contextlib import contextmanager
import errno
import socket
import time

import logging

import feedparser
import requests
from urllib3.util import connection as urllib3_connection

from src.schemas import Incident, Source


logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (compatible; journalist-helper/1.0; +https://github.com/journalist-helper)"
MAX_FETCH_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 2


@contextmanager
def prefer_ipv4_connections():
    """Temporarily force requests/urllib3 to resolve only IPv4 addresses."""
    original_allowed_gai_family = urllib3_connection.allowed_gai_family
    urllib3_connection.allowed_gai_family = lambda: socket.AF_INET
    try:
        yield
    finally:
        urllib3_connection.allowed_gai_family = original_allowed_gai_family


def has_errno(exc: BaseException, code: int) -> bool:
    """Check whether an exception chain contains a specific errno."""
    current: BaseException | None = exc
    while current is not None:
        if isinstance(current, OSError) and current.errno == code:
            return True
        current = current.__cause__ or current.__context__
    return False


def fetch_feed(feed_source: Source) -> tuple[bytes, int | None, str | None]:
    """Fetch a feed with explicit headers so failures are easier to diagnose."""
    request_kwargs = {
        "headers": {
            "User-Agent": USER_AGENT,
            "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8",
        },
        "timeout": (10, 30),
    }

    def _do_request(force_ipv4: bool = False) -> requests.Response:
        if force_ipv4:
            with prefer_ipv4_connections():
                return requests.get(feed_source.url, **request_kwargs)
        return requests.get(feed_source.url, **request_kwargs)

    force_ipv4 = False
    last_error: requests.RequestException | None = None

    for attempt in range(1, MAX_FETCH_ATTEMPTS + 1):
        try:
            response = _do_request(force_ipv4=force_ipv4)
            response.raise_for_status()
            return response.content, response.status_code, response.headers.get("Content-Type")
        except requests.RequestException as exc:
            last_error = exc

            if has_errno(exc, errno.ENETUNREACH) and not force_ipv4:
                logger.warning(
                    "RSS feed %s failed over the default route with ENETUNREACH; retrying via IPv4",
                    feed_source.url,
                )
                force_ipv4 = True
            elif attempt < MAX_FETCH_ATTEMPTS:
                logger.warning(
                    "RSS feed %s request attempt %d/%d failed: %s; retrying in %ds",
                    feed_source.url,
                    attempt,
                    MAX_FETCH_ATTEMPTS,
                    exc,
                    RETRY_BACKOFF_SECONDS,
                )

            if attempt < MAX_FETCH_ATTEMPTS:
                time.sleep(RETRY_BACKOFF_SECONDS)

    raise RuntimeError(f"Failed to fetch RSS feed {feed_source.url}: {last_error}") from last_error


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
