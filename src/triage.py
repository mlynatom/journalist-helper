"""Triage incidents using LLMs through OpenRouter API."""
import logging
import os

from dotenv import load_dotenv
from openrouter import OpenRouter
from openrouter.components import ChatResult
from src.config import DEFAULT_MODEL

logger = logging.getLogger(__name__)

load_dotenv()
 
api_key = os.getenv("OPENROUTER_API_KEY")

def build_model_prompt(incidents: list[Incident]) -> str:
    """Build a prompt for the LLM based on the list of incidents."""
    if not incidents:
        return "Žádné incidenty k posouzení."

    prompt = "Následující incidenty byly nalezeny v RSS feedu:\n\n"
    for idx, incident in enumerate(incidents, start=1):
        prompt += f"{idx}. [{incident.source}] {incident.title}\n"
        if incident.published_at:
            prompt += f"   Datum: {incident.published_at.isoformat()}\n"
        if incident.link:
            prompt += f"   Odkaz: {incident.link}\n"
        if incident.description:
            prompt += f"   Popis: {incident.description}\n"
        prompt += "\n"

    prompt += """Posuďte, které z těchto incidentů jsou relevantní pro okres Kolín a proč. U každého relevantního incidentu uveďte stručné shrnutí a důvod relevance. Pokud žádný incident není relevantní, vysvětlete proč.
    Pro každý také uveďte odkaz na původní zdroj a datum publikace. Buďte struční a konkrétní, zaměřte se na klíčové informace. Pište česky.
    
    Incidenty by měly být seřazeny podle důležitosti a předpokládané čtenosti a relevance pro místní publikum. Vyhodnoť o čem je důležité informovat čtenáře v Kolíně a co by mohlo být pro ně nejzajímavější. Pokud je incident pouze okrajově relevantní, uveď to. Pokud je zásah vážný nebo neobvyklý, uveď to na první místo.

    V odpovědích používej i tučné zvýraznění a emoji, aby bylo jasné, které informace jsou klíčové.
    """
    return prompt


def perform_triage(incidents: list[Incident]) -> str:
    """Perform triage using the OpenRouter API."""
    prompt = build_model_prompt(incidents)
    if not api_key:
        logger.warning("OPENROUTER_API_KEY is not set, skipping OpenRouter triage.")
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    try:
        with OpenRouter(api_key=api_key) as client:
            response: ChatResult = client.chat.send(
                model=DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant who is proffesional journalist that helps triage news incidents."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
            )
    except Exception as exc:  # pragma: no cover - defensive runtime guard
        logger.error(f"OpenRouter triage failed: {exc}")
        raise RuntimeError(f"OpenRouter triage failed: {exc}") from exc


    content = response.choices[0].message.content

    return content
