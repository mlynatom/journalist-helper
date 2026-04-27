"""Triage news items using LLMs through OpenRouter API."""
import logging
import os

from dotenv import load_dotenv
from openrouter import OpenRouter
from openrouter.components import ChatResult
from src.config import DEFAULT_MODEL
from src.schemas import NewsItem

logger = logging.getLogger(__name__)

load_dotenv()
 
api_key = os.getenv("OPENROUTER_API_KEY")

def build_model_prompt(news_items: list[NewsItem]) -> str:
    """Build a prompt for the LLM based on the list of news items."""
    if not news_items:
        return "Žádné novinky ani zprávy k posouzení."

    prompt = "Následující zprávy a důležitá zjištění byly nalezeny ve zdrojích:\n\n"
    for idx, news_item in enumerate(news_items, start=1):
        prompt += f"{idx}. [{news_item.source}] {news_item.title}\n"
        if news_item.published_at:
            prompt += f"   Datum: {news_item.published_at.isoformat()}\n"
        if news_item.link:
            prompt += f"   Odkaz: {news_item.link}\n"
        if news_item.description:
            prompt += f"   Popis: {news_item.description}\n"
        prompt += "\n"

    prompt += """Posuďte, které z těchto zpráv, událostí nebo incidentů jsou relevantní pro okres Kolín a proč. U každé relevantní zprávy uveďte stručné shrnutí a důvod relevance. Pokud žádná položka není relevantní, vysvětlete proč.
    Pro každý také uveďte odkaz na původní zdroj a datum publikace. Buďte struční a konkrétní, zaměřte se na klíčové informace. Pište česky.
    
    Položky by měly být seřazeny podle důležitosti, předpokládané čtenosti a relevance pro místní publikum. Vyhodnoťte, o čem je důležité informovat čtenáře v Kolíně a co by pro ně mohlo být nejzajímavější. Pokud je položka pouze okrajově relevantní, uveď to. Pokud je zpráva mimořádně důležitá nebo neobvyklá, uveď ji na první místo.

    V odpovědích používej i tučné zvýraznění a emoji, aby bylo jasné, které informace jsou klíčové. Uveď všechny zprávy, žádné nevynechávej, ale jasně označuj, které jsou nejdůležitější. Pokud je zpráva relevantní, ale není zcela jasné, proč, uveď to a navrhni možné důvody relevance. Pokud je zpráva zcela nerelevantní, vysvětli proč. Zaměř se na to, co by mohlo být důležité pro místní komunitu v Kolíně, a nezapomeň zohlednit i širší kontext, například pokud se jedná o událost, která by mohla mít dopad na dopravu, bezpečnost nebo jiné aspekty života v Kolíně. Buď co nejkonkrétnější a nejstručnější, ale zároveň poskytni dostatek informací pro pochopení důležitosti každé zprávy.
    """
    return prompt


def perform_triage(news_items: list[NewsItem]) -> str:
    """Perform triage using the OpenRouter API."""
    prompt = build_model_prompt(news_items)
    if not api_key:
        logger.warning("OPENROUTER_API_KEY is not set, skipping OpenRouter triage.")
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    try:
        with OpenRouter(api_key=api_key) as client:
            response: ChatResult = client.chat.send(
                model=DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant who is a professional journalist that helps triage news and important updates."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
            )
    except Exception as exc:  # pragma: no cover - defensive runtime guard
        logger.error("OpenRouter triage failed: %s", exc)
        raise RuntimeError(f"OpenRouter triage failed: {exc}") from exc


    content = response.choices[0].message.content

    return content
