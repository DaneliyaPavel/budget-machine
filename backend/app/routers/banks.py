"""Маршруты для импорта операций из разных банков."""

from datetime import datetime

import os
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from .. import database, crud
from ..api.utils import api_error
from ..models import User
from ..api.v1.users import get_current_user
from ..banks import get_connector
from ..kafka_producer import publish

USE_KAFKA = os.getenv("KAFKA_BROKER_URL") is not None
KAFKA_TOPIC = os.getenv("BANK_TOPIC", "bank.raw")

router = APIRouter(prefix="/банки", tags=["Банки"])


@router.post("/импорт", response_model=dict)
async def import_from_bank(
    bank: str = Query(..., description="Название банка"),
    token: str = Query(..., description="Токен или ключ доступа"),
    start: datetime = Query(..., description="Начало периода"),
    end: datetime = Query(..., description="Конец периода"),
    session: AsyncSession = Depends(database.get_session),
    current_user: User = Depends(get_current_user),
):
    """Загрузить операции из указанного банка."""
    if USE_KAFKA:
        await publish(
            KAFKA_TOPIC,
            {
                "bank": bank,
                "token": token,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "account_id": current_user.account_id,
                "user_id": current_user.id,
            },
        )
        return {"queued": True}
    try:
        connector = get_connector(bank, current_user.id, token)
    except ValueError:
        raise api_error(400, "Неизвестный банк", "UNKNOWN_BANK")

    transactions = await connector.fetch_transactions(start, end)
    if not transactions:
        raise api_error(400, "Не удалось получить операции", "BANK_FETCH_ERROR")
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
    current_user: User = Depends(get_current_user),
):
    """Импортировать операции, используя сохранённый токен банка."""
    token_obj = await crud.get_bank_token(session, bank, current_user.id)
    if not token_obj:
        raise api_error(404, "Токен не найден", "TOKEN_NOT_FOUND")
    if USE_KAFKA:
        await publish(
            KAFKA_TOPIC,
            {
                "bank": bank,
                "token": None,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "account_id": current_user.account_id,
                "user_id": current_user.id,
            },
        )
        return {"queued": True}
    try:
        connector = get_connector(bank, current_user.id)
    except ValueError:
        raise api_error(400, "Неизвестный банк", "UNKNOWN_BANK")
    transactions = await connector.fetch_transactions(start, end)
    if not transactions:
        raise api_error(400, "Не удалось получить операции", "BANK_FETCH_ERROR")
    await crud.create_transactions_bulk(
        session, transactions, current_user.account_id, current_user.id
    )
    return {"created": len(transactions)}
