from datetime import datetime
from typing import List

from .. import schemas

class BankConnector:
    """Базовый интерфейс коннектора банка."""

    def __init__(self, token: str) -> None:
        self.token = token

    async def fetch_transactions(
        self, start: datetime, end: datetime
    ) -> List[schemas.TransactionCreate]:
        """Получить список операций за период."""
        raise NotImplementedError
