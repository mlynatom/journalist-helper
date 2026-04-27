"""Pydantic schemas for the application."""

from datetime import datetime

from pydantic import BaseModel

class NewsItem(BaseModel):
    """Model representing a single news item worth tracking."""
    source: str
    title: str = ""
    link: str = ""
    published_at: datetime | None = None
    description: str = ""

    @property
    def relevance_text(self) -> str:
        """Text used for relevance filtering."""
        return f"{self.title} {self.description} {self.source} {self.link}".casefold()

    def __str__(self) -> str:
        """Human-friendly output used by print()."""
        title = self.title or "(untitled)"
        published = self.published_at.isoformat() if self.published_at else "unknown time"
        return f"[{self.source}] {title} | {published} | {self.link} | {self.description}"


class Source(BaseModel):
    """Model representing an RSS source of news items."""
    name: str
    url: str
