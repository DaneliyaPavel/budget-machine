"""Маршруты аналитики расходов."""

from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud, database, schemas

router = APIRouter(prefix="/аналитика", tags=["Аналитика"])


@router.get("/категории", response_model=list[schemas.CategorySummary])
async def summary_by_category(
    year: int = Query(datetime.utcnow().year,
                      description="Год, за который строится отчёт"),
    month: int = Query(datetime.utcnow().month,
                       description="Месяц (1-12)"),
    session: AsyncSession = Depends(database.get_session),
):
    """Вернуть сумму операций по категориям за выбранный месяц."""
    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, month + 1, 1)

    rows = await crud.transactions_summary_by_category(session, start, end)
    return [schemas.CategorySummary(category=row[0], total=float(row[1] or 0)) for row in rows]


@router.get("/лимиты", response_model=list[schemas.LimitExceed])
async def limits_check(
    year: int = Query(datetime.utcnow().year, description="Год"),
    month: int = Query(datetime.utcnow().month, description="Месяц (1-12)"),
    session: AsyncSession = Depends(database.get_session),
):
    """Показать категории, где траты превысили установленный лимит."""
    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, month + 1, 1)
    rows = await crud.categories_over_limit(session, start, end)
    return [
        schemas.LimitExceed(category=r[0], limit=float(r[1]), spent=float(r[2]))
        for r in rows
    ]
