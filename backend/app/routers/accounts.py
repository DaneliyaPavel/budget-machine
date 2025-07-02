"""Маршруты для управления счётом пользователя."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud, database, schemas
from ..models import User
from .users import get_current_user

router = APIRouter(prefix="/счёт", tags=["Счёт"])


@router.get("/", response_model=schemas.Account)
async def read_account(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(database.get_session),
):
    """Получить информацию о текущем счёте."""
    account = await crud.get_account(session, current_user.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Счёт не найден")
    return account


@router.patch("/", response_model=schemas.Account)
async def update_account(
    data: schemas.Account,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(database.get_session),
):
    """Изменить параметры счёта."""
    account = await crud.update_account(
        session,
        current_user.account_id,
        name=data.name,
        currency_code=data.currency_code,
    )
    if not account:
        raise HTTPException(status_code=404, detail="Счёт не найден")
    return account
