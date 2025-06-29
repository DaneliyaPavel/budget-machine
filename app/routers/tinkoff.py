"""Маршруты для интеграции с банком Тинькофф."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .. import database, crud, models
from .users import get_current_user
from ..banks.tinkoff import TinkoffConnector

router = APIRouter(prefix="/тинькофф", tags=["Тинькофф"])


@router.post("/импорт", response_model=dict)
async def import_tinkoff(
    token: str,
    start: datetime = Query(..., description="Начало периода"),
    end: datetime = Query(..., description="Конец периода"),
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Загрузить операции с помощью токена Тинькофф."""
    connector = TinkoffConnector(token)
    transactions = await connector.fetch_transactions(start, end)
    if not transactions:
        raise HTTPException(status_code=400, detail="Не удалось получить операции")
    await crud.create_transactions_bulk(session, transactions, current_user.id)
    return {"created": len(transactions)}
