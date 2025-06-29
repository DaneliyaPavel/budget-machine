"""Маршруты для целей накоплений."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from .. import crud, schemas, database, models
from .users import get_current_user

router = APIRouter(prefix="/цели", tags=["Цели"])

@router.get("/", response_model=list[schemas.Goal])
async def read_goals(
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Получить список целей."""
    return await crud.get_goals(session, current_user.id)

@router.post("/", response_model=schemas.Goal)
async def create_goal(
    goal: schemas.GoalCreate,
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Создать новую цель."""
    return await crud.create_goal(session, goal, current_user.id)


@router.get("/{goal_id}", response_model=schemas.Goal)
async def read_goal(
    goal_id: int,
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Получить цель по ID."""
    goal = await crud.get_goal(session, goal_id, current_user.id)
    if not goal:
        raise HTTPException(status_code=404, detail="Цель не найдена")
    return goal


@router.patch("/{goal_id}", response_model=schemas.Goal)
async def update_goal(
    goal_id: int,
    data: schemas.GoalUpdate,
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Изменить цель."""
    goal = await crud.update_goal(session, goal_id, data, current_user.id)
    if not goal:
        raise HTTPException(status_code=404, detail="Цель не найдена")
    return goal


@router.delete("/{goal_id}", status_code=204)
async def delete_goal(
    goal_id: int,
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Удалить цель."""
    await crud.delete_goal(session, goal_id, current_user.id)
    return None
