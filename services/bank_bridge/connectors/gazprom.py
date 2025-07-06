from __future__ import annotations

from datetime import datetime
from typing import Any

from .base import BaseConnector


class GazpromConnector(BaseConnector):
    """Placeholder connector for Gazprombank."""

    name = "gazprom"
    display = "Газпромбанк"

    def __init__(self, user_id: str, token: str | None = None) -> None:
        super().__init__(user_id, token)

    async def auth(self) -> str:
        await self._save_token()
        return "https://example.com/gazprom/auth"

    async def refresh(self) -> str:
        await self._save_token()
        return ""

    async def fetch_accounts(self) -> list[dict[str, Any]]:
        return []

    async def fetch_txns(
        self, account_id: str, start: datetime, end: datetime
    ) -> list[dict[str, Any]]:
        return []
