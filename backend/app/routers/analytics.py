"""Маршруты аналитики расходов и целей."""

from datetime import datetime, date, timezone

from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud, database, schemas, models, notifications
from .users import get_current_user

router = APIRouter(prefix="/аналитика", tags=["Аналитика"])


@router.get("/категории", response_model=list[schemas.CategorySummary])
async def summary_by_category(
    year: int = Query(
        default_factory=lambda: datetime.now(timezone.utc).year,
        description="Год",
    ),
    month: int = Query(
        default_factory=lambda: datetime.now(timezone.utc).month,
        description="Месяц (1-12)",
    ),
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Сумма операций по категориям за месяц."""
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    end = (
        datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        if month == 12
        else datetime(year, month + 1, 1, tzinfo=timezone.utc)
    )
    rows = await crud.transactions_summary_by_category(
        session, start, end, current_user.account_id
    )
    return [
        schemas.CategorySummary(category=r[0], total=float(r[1] or 0)) for r in rows
    ]


@router.get("/лимиты", response_model=list[schemas.LimitExceed])
async def limits_check(
    background_tasks: BackgroundTasks,
    year: int = Query(
        default_factory=lambda: datetime.now(timezone.utc).year,
        description="Год",
    ),
    month: int = Query(
        default_factory=lambda: datetime.now(timezone.utc).month,
        description="Месяц (1-12)",
    ),
    notify: bool = Query(False, description="Отправить уведомление"),
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Категории, где траты превысили лимит."""
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    end = (
        datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        if month == 12
        else datetime(year, month + 1, 1, tzinfo=timezone.utc)
    )
    rows = await crud.categories_over_limit(
        session, start, end, current_user.account_id
    )
    result = [
        schemas.LimitExceed(category=r[0], limit=float(r[1]), spent=float(r[2]))
        for r in rows
    ]
    if notify and result:
        lines = ["Превышение лимитов:"] + [
            f"{r.category}: {r.spent} из {r.limit}" for r in result
        ]
        background_tasks.add_task(
            notifications.send_message,
            "\n".join(lines),
            current_user.account_id,
        )
    return result


@router.get("/прогноз", response_model=list[schemas.ForecastItem])
async def forecast(
    year: int = Query(
        default_factory=lambda: datetime.now(timezone.utc).year,
        description="Год",
    ),
    month: int = Query(
        default_factory=lambda: datetime.now(timezone.utc).month,
        description="Месяц (1-12)",
    ),
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Прогноз расходов по категориям."""
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    end = (
        datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        if month == 12
        else datetime(year, month + 1, 1, tzinfo=timezone.utc)
    )
    rows = await crud.forecast_by_category(session, start, end, current_user.account_id)
    return [
        schemas.ForecastItem(category=r[0], spent=float(r[1]), forecast=float(r[2]))
        for r in rows
    ]


@router.get("/дни", response_model=list[schemas.DailySummary])
async def summary_by_day(
    year: int = Query(
        default_factory=lambda: datetime.now(timezone.utc).year,
        description="Год",
    ),
    month: int = Query(
        default_factory=lambda: datetime.now(timezone.utc).month,
        description="Месяц (1-12)",
    ),
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Траты по дням за месяц."""
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    end = (
        datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        if month == 12
        else datetime(year, month + 1, 1, tzinfo=timezone.utc)
    )
    rows = await crud.daily_expenses(session, start, end, current_user.account_id)
    result: list[schemas.DailySummary] = []
    for r in rows:
        day = r[0]
        if isinstance(day, str):
            day = date.fromisoformat(day)
        elif isinstance(day, datetime):
            day = day.date()
        result.append(schemas.DailySummary(date=day, total=float(r[1] or 0)))
    return result


@router.get("/баланс", response_model=schemas.MonthlySummary)
async def balance_overview(
    year: int = Query(
        default_factory=lambda: datetime.now(timezone.utc).year,
        description="Год",
    ),
    month: int = Query(
        default_factory=lambda: datetime.now(timezone.utc).month,
        description="Месяц (1-12)",
    ),
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Сколько уже потрачено и прогноз расходов."""
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    end = (
        datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        if month == 12
        else datetime(year, month + 1, 1, tzinfo=timezone.utc)
    )
    spent, forecast_val = await crud.monthly_overview(
        session, start, end, current_user.account_id
    )
    return schemas.MonthlySummary(spent=spent, forecast=forecast_val)


@router.get("/цели", response_model=list[schemas.GoalProgress])
async def goals_progress(
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Прогресс по накопительным целям."""
    goals = await crud.get_goals(session, current_user.account_id)
    result: list[schemas.GoalProgress] = []
    for g in goals:
        progress = (
            float(g.current_amount) / float(g.target_amount) * 100
            if g.target_amount
            else 0
        )
        result.append(
            schemas.GoalProgress(
                id=g.id,
                name=g.name,
                target_amount=float(g.target_amount),
                current_amount=float(g.current_amount),
                due_date=g.due_date,
                progress=progress,
            )
        )
    return result
