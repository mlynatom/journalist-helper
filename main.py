"""Main entry point for the journalist helper application."""
from cmath import e
from urllib3.connection import log
import logging
import os
from pathlib import Path

from src.config import DEFAULT_FILTER_KEYWORDS, DEFAULT_MODEL, SOURCES
from src.rss_parser import parse_rss_feed
from src.schemas import Incident, Source
from src.telegram import send_telegram_alert
from src.triage import perform_triage

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def save_triage_result(triage_result: str) -> None:
    """Persist triage output for downstream automation consumers."""
    output_path = Path(os.getenv("TRIAGE_OUTPUT_FILE", "triage_result.txt"))
    output_path.write_text(triage_result, encoding="utf-8")


def extract_incidents() -> list[Incident]:
    """Extract incidents from all configured sources."""
    incidents: list[Incident] = []
    for source in SOURCES:
        logger.info("Načítám zdroj: %s (%s)", source.name, source.url)
        try:
            source_incidents = parse_rss_feed(source)
            logger.info(" - Načteno %d incidentů.", len(source_incidents))
            incidents.extend(source_incidents)
        except Exception as exc:
            logger.error(" - Chyba při načítání zdroje: %s", exc)
    return incidents


def is_related(incident: Incident, keywords: list[str]) -> bool:
    """Determine if an incident is related based on keywords."""
    if not keywords:
        return True

    text = incident.relevance_text
    return any(keyword.casefold() in text for keyword in keywords)


def main():
    """Main function to run the application."""
    logger.info("Spouštím zpravodajský monitor...")
    logger.info("Používám model: %s", DEFAULT_MODEL)
    logger.info("Sleduji zdroje: %s", [source.name for source in SOURCES])
    
    # Prepare incidents
    incidents = extract_incidents()

    # Filter relevant incidents
    relevant_incidents = [incident for incident in incidents if is_related(incident=incident, keywords=DEFAULT_FILTER_KEYWORDS)]
    logger.info(
        " - Filtrováno na %d relevantních incidentů z %d celkových.",
        len(relevant_incidents),
        len(incidents),
    )

    # For debugging purposes, print the relevant incidents
    for incident in relevant_incidents:
        logger.debug("%s", incident)

    if len(relevant_incidents) == 0:
        triage_result = "Žádné relevantní incidenty nenalezeny."
        logger.info("Žádné relevantní incidenty nenalezeny, triage přeskočen.")
    else:
        # Perform triage using the LLM
        try:
            triage_result = perform_triage(relevant_incidents)
            logger.info("Triage completed successfully.")

        except RuntimeError as exc:
            logger.error("Triage failed: %s", exc)


    save_triage_result(triage_result)
    logger.info("Odesílám triage výsledek do Telegramu...")
    send_telegram_alert(triage_result)
    logger.info("Triage výsledek odeslán do Telegramu.")

    return triage_result
    

if __name__ == "__main__":
    result = main()
    if result is not None:
        print(result)
