"""Configuration for the application."""
import os

from src.schemas import Source

# List of RSS sources to monitor
SOURCES: list[Source] = [
    Source(
        name="České noviny - ČR",
        url="https://www.ceskenoviny.cz/sluzby/rss/cr.php"
    ),
    Source(
        name="Zásahy JPO",
        url="https://proud-union-e70d.tom-mlynar1.workers.dev/" #https://pkr.kr-stredocesky.cz/pkr/zasahy-jpo/feed.xml
    ),
    Source(
        name="PID - mimorádnosti",
        url="https://pid.cz/feed/rss-mimoradnosti/"
    ),
]

DEFAULT_MODEL = os.getenv("OPENROUTER_MODEL", "z-ai/glm-4.5-air:free")
DEFAULT_FILTER_KEYWORDS = ["okres kolín", "kolín"]
