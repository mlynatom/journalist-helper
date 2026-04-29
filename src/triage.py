"""Triage news items using LLMs through OpenRouter API."""

import logging

from openrouter import OpenRouter
from openrouter.components import ChatResult

from src.config import DEFAULT_MODEL, settings
from src.schemas import NewsItem

logger = logging.getLogger(__name__)


def build_model_prompt(news_items: list[NewsItem]) -> str:
    """Build a prompt for the LLM based on the list of news items."""
    if not news_items:
        return "Žádné novinky ani zprávy k posouzení."

    prompt = "Zde jsou nalezené zprávy k analýze:\n\n"
    for idx, news_item in enumerate(news_items, start=1):
        prompt += f"[{idx}] Titulek: {news_item.title}\n"
        prompt += f"    Zdroj: {news_item.source}\n"
        if news_item.published_at:
            prompt += f"    Datum: {news_item.published_at.isoformat()}\n"
        if news_item.link:
            prompt += f"    Odkaz: {news_item.link}\n"
        if news_item.description:
            prompt += f"    Popis: {news_item.description}\n"
        prompt += "\n"

    prompt += """
Proveď triage těchto zpráv pro novináře z okresu Kolín. Tvým hlavním úkolem je VYHODNOTIT NOVINÁŘSKÝ POTENCIÁL – tedy zjistit, ze kterých zpráv by byl nejlepší, nejčtenější a nejdůležitější článek pro místní obyvatele.

**PRAVIDLA PRO ROZDĚLENÍ A ŘAZENÍ (Použij tyto 3 nadpisy):**

1. 🔥 **HLAVNÍ TÉMATA K ZPRACOVÁNÍ**
   - Zde zařaď 1 až 3 absolutně nejdůležitější události z okresu Kolín (závažné nehody, důležitá rozhodnutí města, významné kauzy, velké investice, dopady na běžný život).
   - To jsou zprávy, které si zaslouží přednostní sepsání do vlastního plnohodnotného článku.
   - Seřaď je od té s absolutně nejvyšším potenciálem.

2. 📌 **DALŠÍ RELEVANTNÍ ZPRÁVY**
   - Zprávy z okresu Kolín, které jsou relevantní, ale mají menší dopad (běžné tiskové zprávy, drobnější krimi, lokální akce, zajímavosti).
   - Vhodné spíše pro krátkou zmínku nebo denní svodku.

3. ⚠️ **MIMO OKRES KOLÍN (Možná chyba)**
   - Zprávy, které se reálně netýkají Kolína a okolí, nebo jsou zcela irelevantní.

**POŽADOVANÁ STRUKTURA PRO KAŽDOU ZPRÁVU:**
Použij striktně tento formát pro každou jednu zprávu. Zvýrazňuj tučně přesně podle vzoru.

[Emoji podle typu] **[Titulek zprávy]**
📍 **Kde:** [Konkrétní místo, město nebo obec]
⏰ **Kdy:** [Zformátované datum]
❓ **O co jde:** [Stručně v jedné větě: Co se stalo faktuálně.]
💡 **Proč napsat článek:** [V jedné větě navrhni novinářský úhel. Proč to lidi bude zajímat? Jaký to má dopad? U sekce "Mimo okres" sem naopak napiš důvod vyřazení.]
🔗 **Zdroj:** [[Název zdroje]]({Odkaz})

---
Vygeneruj finální zprávu pro Telegram podle těchto pravidel. Pamatuj na maximální stručnost, aby se text pohodlně četl na mobilu.
"""  # noqa: E501, RUF001
    return prompt


def perform_triage(news_items: list[NewsItem]) -> str:
    """Perform triage using the OpenRouter API."""
    prompt = build_model_prompt(news_items)
    if not settings.openrouter_api_key:
        logger.warning("OPENROUTER_API_KEY is not set, skipping OpenRouter triage.")
        msg = "OPENROUTER_API_KEY is not set"
        raise RuntimeError(msg)

    try:
        with OpenRouter(api_key=settings.openrouter_api_key) as client:
            system_prompt = (
                "You are an expert news editor and journalist assistant. "
                "Your task is to triage and summarize local news for a journalist "
                "focusing on the Kolín district (okres Kolín, Czech Republic). "
                "Your output will be sent directly as a Telegram message. Therefore, "
                "it MUST be strictly structured, highly readable on mobile, use "
                "appropriate emojis, and strictly formatted using Telegram-compatible "
                "Markdown. Never exceed 4000 characters. Always output in Czech."
            )

            response: ChatResult = client.chat.send(
                model=DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
    except Exception as exc:  # pragma: no cover - defensive runtime guard
        logger.exception("OpenRouter triage failed")
        msg = f"OpenRouter triage failed: {exc}"
        raise RuntimeError(msg) from exc

    return response.choices[0].message.content
