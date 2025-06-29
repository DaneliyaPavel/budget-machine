from datetime import datetime
from typing import List

from .. import schemas
from .base import BankConnector

class SberConnector(BankConnector):
    """Заглушка коннектора Сбербанка."""

    async def fetch_transactions(
        self, start: datetime, end: datetime
    ) -> List[schemas.TransactionCreate]:
        # Тут будет обращение к API Сбербанка
        return []
