"""Main entry point for the journalist helper application."""
from collections import Counter
import logging
import os
from pathlib import Path

import requests

from src.config import DEFAULT_FILTER_KEYWORDS, DEFAULT_MODEL, SOURCES
from src.nemocnice_kolin_parser import parse_nemocnice_kolin_page
from src.nehody_uzavirky_parser import parse_nehody_uzavirky_page
from src.rss_parser import parse_rss_feed
from src.schemas import NewsItem
from src.telegram import send_telegram_alert
from src.triage import perform_triage

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def save_triage_result(triage_result: str) -> None:
    """Persist triage output for downstream automation consumers."""
    output_path = Path(os.getenv("TRIAGE_OUTPUT_FILE", "triage_result.txt"))
    output_path.write_text(triage_result, encoding="utf-8")


def format_source_statistics(news_items: list[NewsItem]) -> str:
    """Render a compact per-source summary for the triage output."""
    counts = Counter(news_item.source for news_item in news_items)
    lines = ["Přehled relevantních zpráv podle zdroje:"]

    for source in SOURCES:
        lines.append(f"- {source.name}: {counts.get(source.name, 0)}")

    lines.append(f"Celkem relevantních zpráv: {len(news_items)}")
    return "\n".join(lines)


def prepend_source_statistics(triage_result: str, news_items: list[NewsItem]) -> str:
    """Add the source statistics block before the triage result."""
    statistics_block = format_source_statistics(news_items)
    return f"{statistics_block}\n\n{triage_result}"


def extract_news_items() -> list[NewsItem]:
    """Extract news items from all configured sources."""
    news_items: list[NewsItem] = []
    for source in SOURCES:
        logger.info("Načítám zdroj zpráv: %s (%s)", source.name, source.url)
        try:
            if source.parser == "nehody_uzavirky":
                source_news_items = parse_nehody_uzavirky_page(source)
            elif source.parser == "nemocnice_kolin":
                source_news_items = parse_nemocnice_kolin_page(source)
            else:
                source_news_items = parse_rss_feed(source)
            logger.info(" - Načteno %d zpráv.", len(source_news_items))
            news_items.extend(source_news_items)
        except RuntimeError as exc:
            logger.error(" - Chyba při načítání zdroje: %s", exc)
    return news_items


def is_related(news_item: NewsItem, keywords: list[str]) -> bool:
    """Determine if a news item is related based on keywords."""
    if news_item.always_relevant or not keywords:
        return True

    text = news_item.relevance_text
    return any(keyword.casefold() in text for keyword in keywords)


def main():
    """Main function to run the application."""
    logger.info("Spouštím zpravodajský monitor důležitých zpráv...")
    logger.info("Používám model: %s", DEFAULT_MODEL)
    logger.info("Sleduji zdroje: %s", [source.name for source in SOURCES])
    
    # Prepare news items
    news_items = extract_news_items()

    # Filter relevant news items
    relevant_news_items = [news_item for news_item in news_items if is_related(news_item=news_item, keywords=DEFAULT_FILTER_KEYWORDS)]
    logger.info(
        " - Filtrováno na %d relevantních zpráv z %d celkových.",
        len(relevant_news_items),
        len(news_items),
    )

    # For debugging purposes, print the relevant news items
    for news_item in relevant_news_items:
        logger.debug("%s", news_item)

    if len(relevant_news_items) == 0:
        triage_result = "Žádné relevantní zprávy ani důležitá nová témata nenalezeny."
        logger.info("Žádné relevantní zprávy nenalezeny, triage přeskočen.")
    else:
        # Perform triage using the LLM
        try:
            triage_result = perform_triage(relevant_news_items)
            logger.info("Triage completed successfully.")

        except RuntimeError as exc:
            logger.error("Triage failed: %s", exc)
            triage_result = "Triage selhal: " + str(exc)

    triage_result = prepend_source_statistics(triage_result, relevant_news_items)

    save_triage_result(triage_result)
    logger.info("Odesílám triage výsledek do Telegramu...")
    try:
        send_telegram_alert(triage_result)
        logger.info("Triage výsledek odeslán do Telegramu.")
    except requests.RequestException as exc:
        logger.error("Failed to send Telegram alert: %s", exc)

    return triage_result
    

if __name__ == "__main__":
    result = main()
    if result is not None:
        print(result)
