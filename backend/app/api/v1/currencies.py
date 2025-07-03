from fastapi import APIRouter, Query

from ... import currency

router = APIRouter(prefix="/currencies", tags=["Валюты"])


@router.get("/", response_model=dict[str, float])
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
