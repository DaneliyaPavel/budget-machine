from __future__ import annotations

from datetime import datetime
from typing import Any

from .base import BaseConnector


class SberConnector(BaseConnector):
    """Placeholder connector for Sberbank."""

    name = "sber"
    display = "Сбербанк"

    async def auth(self) -> str:
        return "https://example.com/sber/auth"

    async def refresh(self) -> str:
        return ""

    async def fetch_accounts(self) -> list[dict[str, Any]]:
        return []

    async def fetch_txns(
        self, account_id: str, start: datetime, end: datetime
    ) -> list[dict[str, Any]]:
        return []
