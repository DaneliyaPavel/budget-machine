"""Маршруты аналитики расходов."""

from datetime import datetime
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud, database, schemas, models, notifications
from .users import get_current_user

router = APIRouter(prefix="/аналитика", tags=["Аналитика"])


@router.get("/категории", response_model=list[schemas.CategorySummary])
async def summary_by_category(
    year: int = Query(datetime.utcnow().year, description="Год, за который строится отчёт"),
    month: int = Query(datetime.utcnow().month, description="Месяц (1-12)"),
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Вернуть сумму операций по категориям за выбранный месяц."""
    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, month + 1, 1)

    rows = await crud.transactions_summary_by_category(
        session, start, end, current_user.account_id
    )
    rows = await crud.transactions_summary_by_category(session, start, end, current_user.id)
    rows = await crud.transactions_summary_by_category(session, start, end)
    return [schemas.CategorySummary(category=row[0], total=float(row[1] or 0)) for row in rows]


@router.get("/лимиты", response_model=list[schemas.LimitExceed])
async def limits_check(
    background_tasks: BackgroundTasks,
    year: int = Query(datetime.utcnow().year, description="Год"),
    month: int = Query(datetime.utcnow().month, description="Месяц (1-12)"),
    notify: bool = Query(False, description="Отправить уведомление в Telegram"),
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Показать категории, где траты превысили установленный лимит."""
    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, month + 1, 1)
    rows = await crud.categories_over_limit(
        session, start, end, current_user.account_id
    )
    rows = await crud.categories_over_limit(session, start, end, current_user.id)
    result = [
        schemas.LimitExceed(category=r[0], limit=float(r[1]), spent=float(r[2]))
        for r in rows
    ]
    if notify and result and background_tasks is not None:
        text_lines = [
            "Превышение лимитов:",
            *[
                f"{item.category}: {item.spent} из {item.limit}"
                for item in result
            ],
        ]
        background_tasks.add_task(
            notifications.send_message,
            "\n".join(text_lines),
        )
    return result


@router.get("/прогноз", response_model=list[schemas.ForecastItem])
async def forecast(
    year: int = Query(datetime.utcnow().year, description="Год"),
    month: int = Query(datetime.utcnow().month, description="Месяц (1-12)"),
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Сделать прогноз трат по категориям до конца месяца."""
    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, month + 1, 1)
    rows = await crud.forecast_by_category(
        session, start, end, current_user.account_id
    )
    rows = await crud.forecast_by_category(session, start, end, current_user.id)
    return [
        schemas.ForecastItem(category=r[0], spent=float(r[1]), forecast=float(r[2]))
        for r in rows
    ]


@router.get("/дни", response_model=list[schemas.DailySummary])
async def summary_by_day(
    year: int = Query(datetime.utcnow().year, description="Год"),
    month: int = Query(datetime.utcnow().month, description="Месяц (1-12)"),
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Вернуть траты по дням за выбранный месяц."""

    start = datetime(year, month, 1)
    end = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)
    rows = await crud.daily_expenses(
        session, start, end, current_user.account_id
    )
    rows = await crud.daily_expenses(session, start, end, current_user.id)
    return [
        schemas.DailySummary(date=row[0], total=float(row[1] or 0))
        for row in rows
    ]


@router.get("/баланс", response_model=schemas.MonthlySummary)
async def balance_overview(
    year: int = Query(datetime.utcnow().year, description="Год"),
    month: int = Query(datetime.utcnow().month, description="Месяц (1-12)"),
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Текущая сумма расходов и прогноз на месяц."""

    start = datetime(year, month, 1)
    end = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)
    spent, forecast = await crud.monthly_overview(
        session, start, end, current_user.account_id
    )
    spent, forecast = await crud.monthly_overview(session, start, end, current_user.id)
    return schemas.MonthlySummary(spent=spent, forecast=forecast)


@router.get("/цели", response_model=list[schemas.GoalProgress])
async def goals_progress(
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Показать прогресс по всем целям пользователя."""

    goals = await crud.get_goals(session, current_user.account_id)
    goals = await crud.get_goals(session, current_user.id)
    result: list[schemas.GoalProgress] = []
    for g in goals:
        progress = float(g.current_amount) / float(g.target_amount) * 100 if g.target_amount else 0
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
    rows = await crud.categories_over_limit(session, start, end)
    return [
        schemas.LimitExceed(category=r[0], limit=float(r[1]), spent=float(r[2]))
        for r in rows
    ]
