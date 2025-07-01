from datetime import datetime
from typing import List

from .. import schemas, vault


class BankConnector:
    """Базовый интерфейс коннектора банка."""

    token_key: str = ""

    def __init__(self, user_id: int, token: str | None = None) -> None:
        self.user_id = user_id
        self.token = token
        self.vault = vault.get_vault_client()

    async def _get_token(self) -> str | None:
        if self.token is None and self.token_key:
            self.token = await self.vault.read(f"{self.token_key}/{self.user_id}")
        return self.token

    async def fetch_transactions(
        self, start: datetime, end: datetime
    ) -> List[schemas.TransactionCreate]:
        """Получить список операций за период."""
        raise NotImplementedError
