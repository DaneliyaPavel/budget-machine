from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .. import tasks, database, crud
from ..models import User
from ..api.v1.users import get_current_user

router = APIRouter(prefix="/задания", tags=["Задания"])


@router.post("/импорт", response_model=dict)
async def import_transactions_job(
    bank: str = Query(..., description="Название банка"),
    token: str | None = Query(None, description="OAuth-токен"),
    start: datetime = Query(..., description="Начало периода"),
    end: datetime = Query(..., description="Конец периода"),
    session: AsyncSession = Depends(database.get_session),
    current_user: User = Depends(get_current_user),
):
    """Запустить импорт операций в фоне."""
    if token is None:
        token_obj = await crud.get_bank_token(session, bank, current_user.id)
        if not token_obj:
            raise HTTPException(status_code=404, detail="Токен не найден")
    result = tasks.import_transactions_task.delay(
        bank,
        token,
        start.isoformat(),
        end.isoformat(),
        current_user.account_id,
        current_user.id,
    )
    return {"task_id": result.id}


@router.post("/лимиты", response_model=dict)
async def check_limits_job(
    year: int = Query(datetime.now(timezone.utc).year, description="Год"),
    month: int = Query(datetime.now(timezone.utc).month, description="Месяц"),
    current_user: User = Depends(get_current_user),
):
    """Проверить лимиты в фоне и прислать уведомление."""
    result = tasks.check_limits_task.delay(current_user.account_id, year, month)
    return {"task_id": result.id}


@router.post("/регулярные", response_model=dict)
async def process_recurring_job(
    date: datetime = Query(..., description="Дата выполнения"),
    current_user: User = Depends(get_current_user),
):
    """Создать операции по регулярным платежам в фоне."""
    result = tasks.process_recurring_task.delay(date.isoformat())
    return {"task_id": result.id}


@router.get("/{task_id}", response_model=dict)
async def get_job_status(task_id: str):
    """Получить статус фоновой задачи."""
    result = tasks.celery_app.AsyncResult(task_id)
    data = {
        "task_id": task_id,
        "status": result.status,
    }
    if result.ready():
        data["result"] = result.result
    return data
