from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from ... import crud, database, schemas
from ...models import User
from ...services import ledger
from .users import get_current_user

router = APIRouter(prefix="/accounts", tags=["Счёт"])


@router.get("/me", response_model=schemas.Account)
async def read_account(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(database.get_session),
):
    """Вернуть информацию о текущем счёте."""
    account = await crud.get_account(session, current_user.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.patch("/me", response_model=schemas.Account)
async def update_account(
    data: schemas.Account,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(database.get_session),
):
    """Изменить параметры текущего счёта."""
    account = await crud.update_account(
        session,
        current_user.account_id,
        name=data.name,
        currency_code=data.currency_code,
    )
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.get("/{account_id}/balance")
async def account_balance(
    account_id: UUID,
    session: AsyncSession = Depends(database.get_session),
):
    """Текущий баланс указанного счёта."""
    balance = await ledger.get_balance(session, account_id)
    return {"balance": balance}
