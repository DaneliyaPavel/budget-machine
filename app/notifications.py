"""Уведомления через Telegram."""

from typing import Optional
import os
import httpx
from pywebpush import webpush

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY")
VAPID_CLAIMS = {"sub": os.getenv("VAPID_SUB", "mailto:admin@example.com")}


async def send_message(
    text: str, token: Optional[str] = None, chat_id: Optional[str] = None
) -> None:
    """Отправить сообщение в Telegram."""
    token = token or TOKEN
    chat_id = chat_id or CHAT_ID
    if not token or not chat_id:
        # Если данные не заданы, просто ничего не делаем
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    async with httpx.AsyncClient() as client:
        await client.post(url, json={"chat_id": chat_id, "text": text})


def send_push(endpoint: str, p256dh: str, auth: str, payload: str) -> None:
    """Отправить Web Push сообщение."""
    if not VAPID_PRIVATE_KEY:
        return
    webpush(
        subscription_info={
            "endpoint": endpoint,
            "keys": {"p256dh": p256dh, "auth": auth},
        },
        data=payload,
        vapid_private_key=VAPID_PRIVATE_KEY,
        vapid_claims=VAPID_CLAIMS,
    )
