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
        url="https://pkr.kr-stredocesky.cz/pkr/zasahy-jpo/feed.xml"
    ),
    Source(
        name="PID - mimorádnosti",
        url="https://pid.cz/feed/rss-mimoradnosti/"
    ),
    Source(
        name="Nehody a uzavírky - Kolín",
        url="https://www.nehody-uzavirky.cz/nehody/",
        parser="nehody_uzavirky",
        always_relevant=True,
    ),
    Source(
        name="Uzavírky - Kolín (krátkodobé)",
        url="https://www.nehody-uzavirky.cz/uzavirky",
        parser="nehody_uzavirky",
        always_relevant=True,
    ),
    Source(
        name="Uzavírky - Kolín (dlouhodobé)",
        url="https://www.nehody-uzavirky.cz/uzavirky-dlouhodobe",
        parser="nehody_uzavirky",
        always_relevant=True,
    ),
    Source(
        name="Uzavírky - Kolín (plánované)",
        url="https://www.nehody-uzavirky.cz/uzavirky-planovane",
        parser="nehody_uzavirky",
        always_relevant=True,
    ),
    Source(
        name="Nemocnice Kolín - Přehled dokumentů",
        url="https://www.nemocnicekolin.cz/dp",
        parser="nemocnice_kolin",
        always_relevant=True,
    ),
    Source(
        name="Policie České republiky – KŘP Středočeského kraje",
        url="https://policie.gov.cz/SCRIPT/rss.aspx?nid=1314"
    ),
    Source(
        name="IDNES - Praha a střední Čechy",
        url="https://servis.idnes.cz/rss.aspx?c=prahah"
    ),
    Source(
        name="Novinky.cz - Domácí",
        url="https://api-web.novinky.cz/v1/timelines/section_5ad5a5fcc25e64000bd6e7ab?xml=rss"
    ),
    Source(
        name="HZS Středočeského kraje",
        url="https://hzscr.gov.cz/SCRIPT/rss.aspx?nid=17314"
    )
]

DEFAULT_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b:free")
DEFAULT_FILTER_KEYWORDS = ["okres kolín", "kolín"]
