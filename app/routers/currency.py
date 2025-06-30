from fastapi import APIRouter, Query

from .. import currency

router = APIRouter(prefix="/валюты", tags=["Валюты"])


@router.get("/", response_model=dict[str, float])
async def read_rates(base: str = Query("RUB", description="Базовая валюта")):
    """Текущие курсы валют."""
    return await currency.get_rates(base)


@router.get("/конвертировать")
async def convert_amount(
    amount: float = Query(..., description="Сумма"),
    source: str = Query(..., alias="from", description="Исходная валюта"),
    target: str = Query("RUB", alias="to", description="Целевая валюта"),
):
    """Конвертировать сумму из одной валюты в другую."""
    result = await currency.convert(amount, source, target)
    return {"result": result}
