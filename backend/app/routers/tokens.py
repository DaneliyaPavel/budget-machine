from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud, database, schemas
from ..models import User
from ..api.v1.users import get_current_user

router = APIRouter(prefix="/токены", tags=["Токены"])


@router.get("/", response_model=list[schemas.BankToken])
async def read_tokens(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(database.get_session),
):
    """Список сохранённых токенов банков."""
    return await crud.get_bank_tokens(session, current_user.id)


@router.post("/", response_model=schemas.BankToken)
async def set_token(
    data: schemas.BankTokenCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(database.get_session),
):
    """Сохранить или обновить токен банка."""
    return await crud.set_bank_token(session, data.bank, data.token, current_user.id)


@router.delete("/{bank}", status_code=204)
async def delete_token(
    bank: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(database.get_session),
):
    """Удалить токен банка."""
    await crud.delete_bank_token(session, bank, current_user.id)
    return None
