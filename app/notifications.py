"""Уведомления через Telegram."""

from typing import Optional
import os
import httpx

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


async def send_message(text: str, token: Optional[str] = None, chat_id: Optional[str] = None) -> None:
    """Отправить сообщение в Telegram."""
    token = token or TOKEN
    chat_id = chat_id or CHAT_ID
    if not token or not chat_id:
        # Если данные не заданы, просто ничего не делаем
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    async with httpx.AsyncClient() as client:
        await client.post(url, json={"chat_id": chat_id, "text": text})
