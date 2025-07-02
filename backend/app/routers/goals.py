"""Маршруты для целей накоплений."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud, schemas, database
from ..models import User
from .users import get_current_user

router = APIRouter(prefix="/цели", tags=["Цели"])


@router.get("/", response_model=list[schemas.Goal])
async def read_goals(
    session: AsyncSession = Depends(database.get_session),
    current_user: User = Depends(get_current_user),
):
    """Получить список целей пользователя."""
    return await crud.get_goals(session, current_user.account_id)


@router.post("/", response_model=schemas.Goal)
async def create_goal(
    goal: schemas.GoalCreate,
    session: AsyncSession = Depends(database.get_session),
    current_user: User = Depends(get_current_user),
):
    """Создать новую цель."""
    return await crud.create_goal(
        session, goal, current_user.account_id, current_user.id
    )


@router.get("/{goal_id}", response_model=schemas.Goal)
async def read_goal(
    goal_id: str,
    session: AsyncSession = Depends(database.get_session),
    current_user: User = Depends(get_current_user),
):
    """Получить цель по ID."""
    goal = await crud.get_goal(session, goal_id, current_user.account_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Цель не найдена")
    return goal


@router.patch("/{goal_id}", response_model=schemas.Goal)
async def update_goal(
    goal_id: str,
    data: schemas.GoalUpdate,
    session: AsyncSession = Depends(database.get_session),
    current_user: User = Depends(get_current_user),
):
    """Изменить параметры цели."""
    goal = await crud.update_goal(session, goal_id, data, current_user.account_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Цель не найдена")
    return goal


@router.post("/{goal_id}/пополнить", response_model=schemas.Goal)
async def deposit_goal(
    goal_id: str,
    data: schemas.GoalDeposit,
    session: AsyncSession = Depends(database.get_session),
    current_user: User = Depends(get_current_user),
):
    """Пополнить текущую цель на заданную сумму."""
    goal = await crud.add_to_goal(
        session, goal_id, data.amount, current_user.account_id
    )
    if not goal:
        raise HTTPException(status_code=404, detail="Цель не найдена")
    return goal


@router.delete("/{goal_id}", status_code=204)
async def delete_goal(
    goal_id: str,
    session: AsyncSession = Depends(database.get_session),
    current_user: User = Depends(get_current_user),
):
    """Удалить цель."""
    await crud.delete_goal(session, goal_id, current_user.account_id)
    return None
