"""Маршруты для целей накоплений."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from .. import crud, schemas, database

router = APIRouter(prefix="/цели", tags=["Цели"])

@router.get("/", response_model=list[schemas.Goal])
async def read_goals(session: AsyncSession = Depends(database.get_session)):
    """Получить список целей."""
    return await crud.get_goals(session)

@router.post("/", response_model=schemas.Goal)
async def create_goal(goal: schemas.GoalCreate, session: AsyncSession = Depends(database.get_session)):
    """Создать новую цель."""
    return await crud.create_goal(session, goal)


@router.get("/{goal_id}", response_model=schemas.Goal)
async def read_goal(goal_id: int, session: AsyncSession = Depends(database.get_session)):
    """Получить цель по ID."""
    goal = await crud.get_goal(session, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Цель не найдена")
    return goal


@router.patch("/{goal_id}", response_model=schemas.Goal)
async def update_goal(goal_id: int, data: schemas.GoalUpdate, session: AsyncSession = Depends(database.get_session)):
    """Изменить цель."""
    goal = await crud.update_goal(session, goal_id, data)
    if not goal:
        raise HTTPException(status_code=404, detail="Цель не найдена")
    return goal


@router.delete("/{goal_id}", status_code=204)
async def delete_goal(goal_id: int, session: AsyncSession = Depends(database.get_session)):
    """Удалить цель."""
    await crud.delete_goal(session, goal_id)
    return None
