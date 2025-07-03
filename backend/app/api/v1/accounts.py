from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from ... import crud, database, schemas
from ...models import User
from ...services import ledger
from ..utils import api_error
from .users import get_current_user

router = APIRouter(prefix="/accounts", tags=["Счёт"])


@router.post("/", response_model=schemas.Account)
async def create_account(
    data: schemas.AccountCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(database.get_session),
):
    """Создать счёт."""
    if current_user.role == "readonly":
        raise api_error(status.HTTP_403_FORBIDDEN, "Forbidden", "FORBIDDEN")
    if data.user_id is None:
        data.user_id = current_user.id
    account = await crud.create_account(session, data)
    return account


@router.get("/", response_model=list[schemas.Account])
async def list_accounts(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(database.get_session),
):
    """Список счетов."""
    return await crud.get_accounts(session)


@router.get("/me", response_model=schemas.Account)
async def read_account(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(database.get_session),
):
    """Вернуть информацию о текущем счёте."""
    account = await crud.get_account(session, current_user.account_id)
    if not account:
        raise api_error(404, "Account not found", "ACCOUNT_NOT_FOUND")
    return account


@router.patch("/me", response_model=schemas.Account)
async def update_account(
    data: schemas.AccountUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(database.get_session),
):
    """Изменить параметры текущего счёта."""
    if data.currency_code is not None:
        existing = await crud.get_account(session, current_user.account_id)
        if existing and existing.currency_code != data.currency_code:
            raise api_error(400, "Account currency immutable", "CURRENCY_IMMUTABLE")

    account = await crud.update_account(
        session,
        current_user.account_id,
        **data.model_dump(exclude_unset=True),
    )
    if not account:
        raise api_error(404, "Account not found", "ACCOUNT_NOT_FOUND")
    return account


@router.get("/{account_id}", response_model=schemas.Account)
async def read_one_account(
    account_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(database.get_session),
):
    """Получить счёт по идентификатору."""
    account = await crud.get_account(session, account_id)
    if not account:
        raise api_error(404, "Account not found", "ACCOUNT_NOT_FOUND")
    return account


@router.put("/{account_id}", response_model=schemas.Account)
async def update_one_account(
    account_id: UUID,
    data: schemas.AccountUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(database.get_session),
):
    """Обновить счёт."""
    if current_user.role == "readonly":
        raise api_error(status.HTTP_403_FORBIDDEN, "Forbidden", "FORBIDDEN")
    if data.currency_code is not None:
        existing = await crud.get_account(session, account_id)
        if existing and existing.currency_code != data.currency_code:
            raise api_error(400, "Account currency immutable", "CURRENCY_IMMUTABLE")

    account = await crud.update_account(
        session, account_id, **data.model_dump(exclude_unset=True)
    )
    if not account:
        raise api_error(404, "Account not found", "ACCOUNT_NOT_FOUND")
    return account


@router.delete("/{account_id}", status_code=204)
async def delete_account(
    account_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(database.get_session),
):
    """Удалить счёт."""
    if current_user.role in {"readonly", "member"}:
        raise api_error(status.HTTP_403_FORBIDDEN, "Forbidden", "FORBIDDEN")
    ok = await crud.delete_account(session, account_id)
    if not ok:
        raise api_error(404, "Account not found", "ACCOUNT_NOT_FOUND")
    return None


@router.get("/{account_id}/balance")
async def account_balance(
    account_id: UUID,
    session: AsyncSession = Depends(database.get_session),
):
    """Текущий баланс указанного счёта."""
    balance = await ledger.get_balance(session, account_id)
    return {"balance": balance}
