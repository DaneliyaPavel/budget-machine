from __future__ import annotations

from datetime import date
from typing import Any, AsyncGenerator

from .base import Account, BaseConnector, RawTxn, TokenPair


class SberConnector(BaseConnector):
    """Placeholder connector for Sberbank."""

    name = "sber"
    display = "Сбербанк"

    def __init__(self, user_id: str, token: TokenPair | None = None) -> None:
        super().__init__(user_id, token)

    async def auth(self, code: str | None, **kwargs: Any) -> TokenPair:
        token = TokenPair(access_token="https://example.com/sber/auth")
        await self._save_token(token)
        return token

    async def refresh(self, token: TokenPair) -> TokenPair:
        await self._save_token(token)
        return token

    async def fetch_accounts(self, token: TokenPair) -> list[Account]:
        return []

    async def fetch_txns(
        self,
        token: TokenPair,
        account: Account,
        date_from: date,
        date_to: date,
    ) -> AsyncGenerator[RawTxn, None]:
        if False:
            yield
        return
