"""Уведомления через Telegram и Web Push."""

from typing import Optional
import os
import httpx
import redis.asyncio as redis
from pywebpush import webpush

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
REDIS_URL = os.getenv(
    "REDIS_URL", os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
)
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY")
VAPID_CLAIMS = {"sub": os.getenv("VAPID_SUB", "mailto:admin@example.com")}

redis_client = redis.from_url(REDIS_URL, decode_responses=True)


async def send_message(text: str, account_id: int | None = None) -> None:
    """Добавить сообщение в стрим Redis."""
    data = {"text": text}
    if account_id is not None:
        data["account_id"] = str(account_id)
    await redis_client.xadd("notifications", data)


async def send_telegram(
    text: str, token: Optional[str] = None, chat_id: Optional[str] = None
) -> None:
    """Отправить сообщение в Telegram непосредственно."""
    token = token or TOKEN
    chat_id = chat_id or CHAT_ID
    if not token or not chat_id:
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
