"""Optional Telegram delivery of scan summaries. Enabled when both
TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are set (get a token from
@BotFather, then message the bot once and read your chat id from
https://api.telegram.org/bot<TOKEN>/getUpdates)."""

from __future__ import annotations

import os

import requests

TELEGRAM_API = "https://api.telegram.org"
MAX_MESSAGE = 4000  # Telegram's hard limit is 4096 characters


def telegram_config() -> tuple[str, str] | None:
    token, chat_id = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    return (token, chat_id) if token and chat_id else None


def send_telegram(text: str, token: str, chat_id: str, session: requests.Session | None = None) -> int:
    """Send `text`, split into chunks under Telegram's size limit on blank
    lines. Returns the number of messages sent."""
    session = session or requests.Session()
    chunks: list[str] = []
    current = ""
    for block in text.split("\n\n"):
        candidate = f"{current}\n\n{block}" if current else block
        if len(candidate) > MAX_MESSAGE and current:
            chunks.append(current)
            current = block[:MAX_MESSAGE]
        else:
            current = candidate[:MAX_MESSAGE]
    if current:
        chunks.append(current)

    for chunk in chunks:
        response = session.post(
            f"{TELEGRAM_API}/bot{token}/sendMessage", json={"chat_id": chat_id, "text": chunk}, timeout=15
        )
        response.raise_for_status()
    return len(chunks)
