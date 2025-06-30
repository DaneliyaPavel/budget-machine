"""Маршруты для импорта операций из разных банков."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .. import database, crud, models
from .users import get_current_user
from ..banks import get_connector

router = APIRouter(prefix="/банки", tags=["Банки"])


@router.post("/импорт", response_model=dict)
async def import_from_bank(
    bank: str = Query(..., description="Название банка"),
    token: str = Query(..., description="Токен или ключ доступа"),
    start: datetime = Query(..., description="Начало периода"),
    end: datetime = Query(..., description="Конец периода"),
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Загрузить операции из указанного банка."""
    try:
        connector = get_connector(bank, token)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неизвестный банк")

    transactions = await connector.fetch_transactions(start, end)
    if not transactions:
        raise HTTPException(status_code=400, detail="Не удалось получить операции")
    await crud.create_transactions_bulk(
        session, transactions, current_user.account_id, current_user.id
    )
    return {"created": len(transactions)}


@router.post("/импорт_по_токену", response_model=dict)
async def import_using_saved_token(
    bank: str = Query(..., description="Название банка"),
    start: datetime = Query(..., description="Начало периода"),
    end: datetime = Query(..., description="Конец периода"),
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Импортировать операции, используя сохранённый токен банка."""
    token_obj = await crud.get_bank_token(session, bank, current_user.account_id)
    if not token_obj:
        raise HTTPException(status_code=404, detail="Токен не найден")
    try:
        connector = get_connector(bank, token_obj.token)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неизвестный банк")
    transactions = await connector.fetch_transactions(start, end)
    if not transactions:
        raise HTTPException(status_code=400, detail="Не удалось получить операции")
    await crud.create_transactions_bulk(
        session, transactions, current_user.account_id, current_user.id
    )
    return {"created": len(transactions)}
