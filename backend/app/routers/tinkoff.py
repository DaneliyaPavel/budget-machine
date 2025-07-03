"""Маршруты для интеграции с банком Тинькофф."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from .. import database, crud
from ..api.utils import api_error
from ..models import User
from ..api.v1.users import get_current_user
from ..banks.tinkoff import TinkoffConnector

router = APIRouter(prefix="/тинькофф", tags=["Тинькофф"])


@router.post("/импорт", response_model=dict)
async def import_tinkoff(
    token: str,
    start: datetime = Query(..., description="Начало периода"),
    end: datetime = Query(..., description="Конец периода"),
    session: AsyncSession = Depends(database.get_session),
    current_user: User = Depends(get_current_user),
):
    """Загрузить операции с помощью токена Тинькофф."""
    connector = TinkoffConnector(token)
    transactions = await connector.fetch_transactions(start, end)
    if not transactions:
        raise api_error(400, "Не удалось получить операции", "BANK_FETCH_ERROR")
    await crud.create_transactions_bulk(
        session, transactions, current_user.account_id, current_user.id
    )
    return {"created": len(transactions)}
