import requests
import os
from dotenv import load_dotenv

load_dotenv()

def send_telegram_alert(message):
    token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("USER_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML" # Allows <b>bold</b>, <i>italic</i>, etc.
    }
    
    response = requests.post(url, json=payload)
    return response.json()

send_telegram_alert("<b>⚠️ ALERT:</b> The application server is down!")