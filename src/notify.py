"""Notification channels. Console (always) + Telegram (optional, keys from .env)."""
import logging
import os
import requests
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger(__name__)


def send_console(text: str) -> bool:
    print(f"🔔 ALERT: {text}")
    return True


def send_telegram(text: str) -> bool:
    token, chat = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat:
        return False
    try:
        r = requests.get(f"https://api.telegram.org/bot{token}/sendMessage",
                         params={"chat_id": chat, "text": text}, timeout=15)
        return r.ok
    except requests.exceptions.RequestException as e:
        log.error("Telegram fail: %s", e)
        return False


def notify_all(text: str):
    send_console(text)
    send_telegram(text)
