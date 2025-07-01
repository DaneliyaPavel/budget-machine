from datetime import datetime
from typing import List

from .. import schemas
from .base import BankConnector


class GazpromConnector(BankConnector):
    """Заглушка коннектора Газпромбанка."""

    token_key = "gazprom_token"

    async def fetch_transactions(
        self, start: datetime, end: datetime
    ) -> List[schemas.TransactionCreate]:
        # В будущем здесь будет обращение к API Газпромбанка
        return []
