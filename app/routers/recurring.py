"""Маршруты для регулярных платежей."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud, schemas, database, models
from .users import get_current_user

router = APIRouter(prefix="/регулярные", tags=["Регулярные платежи"])


@router.get("/", response_model=list[schemas.RecurringPayment])
async def read_recurring_payments(
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Получить все регулярные платежи пользователя."""
    return await crud.get_recurring_payments(session, current_user.account_id)


@router.post("/", response_model=schemas.RecurringPayment)
async def create_recurring_payment(
    item: schemas.RecurringPaymentCreate,
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Создать регулярный платеж."""
    return await crud.create_recurring_payment(
        session, item, current_user.account_id, current_user.id
    )


@router.get("/{rp_id}", response_model=schemas.RecurringPayment)
async def read_recurring_payment(
    rp_id: int,
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Получить регулярный платеж по ID."""
    rp = await crud.get_recurring_payment(session, rp_id, current_user.account_id)
    if not rp:
        raise HTTPException(status_code=404, detail="Платёж не найден")
    return rp


@router.patch("/{rp_id}", response_model=schemas.RecurringPayment)
async def update_recurring_payment(
    rp_id: int,
    data: schemas.RecurringPaymentUpdate,
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Обновить регулярный платеж."""
    rp = await crud.update_recurring_payment(
        session, rp_id, data, current_user.account_id
    )
    if not rp:
        raise HTTPException(status_code=404, detail="Платёж не найден")
    return rp


@router.delete("/{rp_id}", status_code=204)
async def delete_recurring_payment(
    rp_id: int,
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Удалить регулярный платеж."""
    await crud.delete_recurring_payment(session, rp_id, current_user.account_id)
    return None
