"""Redis DB deduplication logic."""

import logging

import redis

from src.config import settings
from src.schemas import NewsItem

logger = logging.getLogger(__name__)


def deduplicate_news_items(news_items: list[NewsItem]) -> list[NewsItem]:
    """Deduplicate news items using Redis."""
    if not settings.redis_url:
        raise ValueError("REDIS_URL environment variable is not set.")

    r = redis.Redis.from_url(settings.redis_url)

    unique_items: list[NewsItem] = []

    for item in news_items:
        # Create a unique key for the news item, e.g., based on title and published date
        item_key = f"{item.title}:{item.published_at.isoformat() if item.published_at else 'unknown'}:{item.source}"

        if not r.exists(item_key):
            unique_items.append(item)
            r.set(item_key, "1", ex=24 * 3600)  # Mark this item as seen with a 24-hour expiration
        else:
            logger.debug("Duplicate news item skipped: %s", item_key)
            # reset expiration for existing key to keep it in the deduplication window
            r.expire(item_key, 24 * 3600)

    return unique_items
