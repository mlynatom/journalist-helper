"""Telegram alerting module for journalist-helper."""

import requests
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

load_dotenv()

# Telegram's message length limit
TELEGRAM_MAX_LENGTH = 4096


def send_telegram_alert(message):
    """Send a message to a Telegram chat using the Bot API.
    
    If the message exceeds Telegram's 4096 character limit, it will be split
    into multiple messages automatically.
    
    Uses MarkdownV2 parse mode to support LLM-generated Markdown formatting
    (bold **text**, tables, code blocks, etc.).
    """
    token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("USER_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    # Split message if it's too long
    messages = _split_message(message)
    
    responses = []
    for idx, msg in enumerate(messages):
        payload = {
            "chat_id": chat_id,
            "text": msg,
            "parse_mode": "MARKDOWN",
        }

        logger.info("Sending Telegram message %d/%d (length: %d)", idx + 1, len(messages), len(msg))

        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()  # Raise an error for bad responses
        responses.append(response.json())
    
    return responses


def _split_message(message, max_length=TELEGRAM_MAX_LENGTH):
    """Split a long message into chunks that fit Telegram's limit.
    
    Tries to split at sensible boundaries (paragraphs, lines) when possible.
    """
    if len(message) <= max_length:
        return [message]
    
    chunks = []
    current_chunk = ""
    
    # Try to split by double newlines first (paragraph breaks)
    paragraphs = message.split("\n\n")
    
    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 <= max_length:
            if current_chunk:
                current_chunk += "\n\n"
            current_chunk += para
        else:
            # If current chunk is not empty, save it
            if current_chunk:
                chunks.append(current_chunk)
            
            # If paragraph is too long by itself, split it further
            if len(para) > max_length:
                sub_chunks = _split_long_paragraph(para, max_length)
                chunks.extend(sub_chunks)
            else:
                current_chunk = para
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks


def _split_long_paragraph(text, max_length=TELEGRAM_MAX_LENGTH):
    """Split a paragraph that's too long by breaking at line boundaries."""
    lines = text.split("\n")
    chunks = []
    current = ""
    
    for line in lines:
        if len(current) + len(line) + 1 <= max_length:
            if current:
                current += "\n"
            current += line
        else:
            if current:
                chunks.append(current)
            # If a single line is too long, just add it as is
            if len(line) > max_length:
                chunks.append(line)
            else:
                current = line
    
    if current:
        chunks.append(current)
    
    return chunks
