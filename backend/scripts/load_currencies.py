import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app import crud, database, schemas

BASE_CURRENCIES = [
    schemas.CurrencyCreate(
        code="RUB", name="Российский рубль", symbol="₽", precision=2
    ),
    schemas.CurrencyCreate(code="USD", name="Доллар США", symbol="$", precision=2),
    schemas.CurrencyCreate(code="EUR", name="Евро", symbol="€", precision=2),
    schemas.CurrencyCreate(code="GBP", name="Британский фунт", symbol="£", precision=2),
    schemas.CurrencyCreate(code="JPY", name="Иена", symbol="¥", precision=0),
    schemas.CurrencyCreate(code="CNY", name="Китайский юань", symbol="¥", precision=2),
    schemas.CurrencyCreate(
        code="CHF", name="Швейцарский франк", symbol="CHF", precision=2
    ),
    schemas.CurrencyCreate(
        code="KZT", name="Казахстанский тенге", symbol="₸", precision=2
    ),
]


async def load_currencies(session: AsyncSession | None = None) -> None:
    if session is None:
        async with database.async_session() as session:
            await load_currencies(session)
            return
    for cur in BASE_CURRENCIES:
        await crud.add_currency(session, cur)


async def main() -> None:
    async with database.async_session() as session:
        await load_currencies(session)
        print("Currencies loaded")


if __name__ == "__main__":
    asyncio.run(main())
