"""Module for generating text using Gemini and OpenRouter as a fallback."""

import logging

from google import genai
from google.genai import types
from openrouter import OpenRouter

from src.config import settings

logger = logging.getLogger(__name__)


def generate(prompt_text: str, system_prompt: str | None = None) -> str:
    """
    Generate text using Gemini by default, fall back to OpenRouter on error.

    Args:
        prompt_text: The user prompt for generation.
        system_prompt: Optional system prompt to guide the LLM behavior.

    If `prompt_text` is None the function reads `GEMINI_INPUT` env var or a
    short placeholder.

    """
    gemini_error: Exception | None = None

    # Try Gemini first
    try:
        client = genai.Client(api_key=settings.gemini_api_key)

        model = "gemini-3.1-flash-lite"
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt_text)],
            ),
        ]

        generate_content_config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            thinking_config=types.ThinkingConfig(thinking_level="MINIMAL"),
        )

        response = client.models.generate_content(
            model=model, contents=contents, config=generate_content_config
        )
    except Exception as exc:
        gemini_error = exc
        logger.exception("Gemini generation failed")
    else:
        if response.text:
            return response.text
        logger.error("Gemini response did not contain text")

    # Try openrouter as a fallback
    if not settings.openrouter_api_key:
        msg = "Both Gemini and OpenRouter generation failed"
        raise RuntimeError(msg) from gemini_error

    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt_text})

        with OpenRouter(api_key=settings.openrouter_api_key) as client:
            response = client.chat.send(
                model=settings.openrouter_model,
                messages=messages,
                temperature=0.2,
            )
        return response.choices[0].message.content
    except Exception as exc:
        logger.exception("OpenRouter fallback failed")
        msg = "Both Gemini and OpenRouter generation failed"
        raise RuntimeError(msg) from exc
