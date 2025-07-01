"""Интеграция с банком Тинькофф."""

from datetime import datetime
from typing import List

import httpx

from .. import schemas
from .base import BankConnector


class TinkoffConnector(BankConnector):
    """Простейший коннектор к API Тинькофф."""

    BASE_URL = "https://api.tinkoff.ru/v1/"
    token_key = "tinkoff_token"

    async def fetch_transactions(
        self, start: datetime, end: datetime
    ) -> List[schemas.TransactionCreate]:
        """Получить операции за период.

        В реальном приложении здесь будет вызов API банка. Этот код лишь
        демонстрирует общую структуру и не обращается к закрытым эндпоинтам.
        """
        token = await self._get_token()
        if not token:
            return []
        headers = {"Authorization": f"Bearer {token}"}
        params = {
            "from": int(start.timestamp() * 1000),
            "to": int(end.timestamp() * 1000),
        }
        url = self.BASE_URL + "transactions"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params, headers=headers, timeout=10)
                resp.raise_for_status()
                data = resp.json()
        except Exception:
            # При ошибке возвращаем пустой список
            return []

        txs: List[schemas.TransactionCreate] = []
        for item in data.get("payload", []):
            txs.append(
                schemas.TransactionCreate(
                    amount=float(item.get("amount")),
                    currency=item.get("currency", "RUB"),
                    description=item.get("description"),
                    category_id=1,  # категорию следует определить отдельно
                    created_at=datetime.fromtimestamp(item.get("date") / 1000),
                )
            )
        return txs
