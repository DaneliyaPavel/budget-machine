from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ... import currency, crud, database, schemas

router = APIRouter(prefix="/currencies", tags=["Валюты"])


@router.get("/", response_model=list[schemas.Currency])
async def list_currencies(session: AsyncSession = Depends(database.get_session)):
    """Список валют."""
    return await crud.get_currencies(session)


@router.get("/rates", response_model=dict[str, float])
async def read_rates(base: str = Query("RUB", description="Base currency")):
    """Вернуть текущие курсы валют."""
    return await currency.get_rates(base)


@router.get("/convert")
async def convert_amount(
    amount: float = Query(..., description="Amount"),
    source: str = Query(..., alias="from", description="Source currency"),
    target: str = Query("RUB", alias="to", description="Target currency"),
):
    """Конвертировать сумму из одной валюты в другую."""
    result = await currency.convert(amount, source, target)
    return {"result": result}
