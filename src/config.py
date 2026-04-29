"""Configuration for the application."""

from pydantic import Field
from pydantic_settings import BaseSettings

from src.schemas import Source

# List of RSS sources to monitor
SOURCES: list[Source] = [
    Source(name="České noviny - ČR", url="https://www.ceskenoviny.cz/sluzby/rss/cr.php"),
    Source(name="Zásahy JPO", url="https://pkr.kr-stredocesky.cz/pkr/zasahy-jpo/feed.xml"),
    Source(name="PID - mimorádnosti", url="https://pid.cz/feed/rss-mimoradnosti/"),
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
        url="https://policie.gov.cz/SCRIPT/rss.aspx?nid=1314",
    ),
    Source(
        name="IDNES - Praha a střední Čechy",
        url="https://servis.idnes.cz/rss.aspx?c=prahah",
    ),
    Source(
        name="Novinky.cz - Domácí",
        url="https://api-web.novinky.cz/v1/timelines/section_5ad5a5fcc25e64000bd6e7ab?xml=rss",
    ),
    Source(
        name="HZS Středočeského kraje",
        url="https://hzscr.gov.cz/SCRIPT/rss.aspx?nid=17314",
    ),
]


class AppSettings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OpenRouter API settings
    openrouter_api_key: str = Field(
        default="", description="API key for OpenRouter API. Required for LLM triaging."
    )
    openrouter_model: str = Field(
        default="openai/gpt-oss-120b:free",
        description="LLM model to use for triaging (OpenRouter model name).",
    )

    # Telegram settings
    bot_token: str = Field(default="", description="Telegram bot token for sending alerts.")
    user_id: str = Field(default="", description="Telegram user/chat ID for receiving alerts.")

    # Redis settings
    redis_url: str = Field(
        default="",
        description="Redis URL for deduplication. Format: redis://user:password@host:port/db",
    )

    # Output settings
    triage_output_file: str = Field(
        default="triage_result.txt", description="File path to save triage results."
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Initialize settings instance
settings = AppSettings()

# For backward compatibility, expose settings as module-level constants
DEFAULT_MODEL = settings.openrouter_model
DEFAULT_FILTER_KEYWORDS = [
    "okres kolín",
    "Kolín",
    "Český Brod",
    "Pečky",
    "Velký Osek",
    "Velim",
    "Týnec nad Labem",
    "Zásmuky",
    "Červené Pečky",
    "Kouřim",
    "Plaňany",
    "Cerhenice",
    "Žiželice",
    "Starý Kolín",
    "Poříčany",
    "Veltruby",
    "Doubravčice",
    "Nová Ves I",
    "Radim",
    "Vitice",
    "Klučov",
    "Tuklaty",
    "Bečváry",
    "Tři Dvory",
    "Konárovice",
    "Krakovany",
    "Břežany II",
    "Ovčáry",
    "Přišimasy",
    "Dobřichov",
    "Nebovidy",
    "Chrášťany",
    "Býchory",
    "Ratenice",
    "Tuchoraz",
    "Tatce",
    "Rostoklaty",
    "Polepy",
    "Pňov-Předhradí",
    "Kořenice",
    "Tismice",
    "Hradešín",
    "Křečhoř",
    "Volárna",
    "Ratboř",
    "Třebovle",
    "Jestřabí Lhota",
    "Svojšice",
    "Radovesnice II",
    "Dolní Chvatliny",
    "Horní Kruty",
    "Chotutice",
    "Přistoupim",
    "Žehuň",
    "Vrbčany",
    "Krupá",
    "Němčice",
    "Radovesnice I",
    "Toušice",
    "Ždánice",
    "Malotice",
    "Uhlířská Lhota",
    "Pašinka",
    "Lošany",
    "Přehvozdí",
    "Libodřice",
    "Libenice",
    "Bělušice",
    "Břežany I",
    "Vrátkov",
    "Žabonosy",
    "Barchovice",
    "Veletov",
    "Choťovice",
    "Drahobudice",
    "Kšely",
    "Skvrňov",
    "Kbel",
    "Polní Voděrady",
    "Církvice",
    "Lipec",
    "Polní Chrčice",
    "Černíky",
    "Mrzky",
    "Klášterní Skalice",
    "Masojedy",
    "Dománovice",
    "Zalešany",
    "Krychnov",
    "Grunta",
]
