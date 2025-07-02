"""Маршруты для работы с категориями."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from .. import crud, schemas, database
from ..models import User
from .users import get_current_user

router = APIRouter(prefix="/категории", tags=["Категории"])


@router.get("/", response_model=list[schemas.Category])
async def read_categories(
    session: AsyncSession = Depends(database.get_session),
    current_user: User = Depends(get_current_user),
):
    """Получить все категории пользователя."""
    return await crud.get_categories(session, current_user.account_id)


@router.post("/", response_model=schemas.Category)
async def create_category(
    category: schemas.CategoryCreate,
    session: AsyncSession = Depends(database.get_session),
    current_user: User = Depends(get_current_user),
):
    """Создать новую категорию."""
    return await crud.create_category(
        session, category, current_user.account_id, current_user.id
    )


@router.get("/{category_id}", response_model=schemas.Category)
async def read_category(
    category_id: uuid.UUID,
    session: AsyncSession = Depends(database.get_session),
    current_user: User = Depends(get_current_user),
):
    """Получить категорию по ID."""
    category = await crud.get_category(session, category_id, current_user.account_id)
    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    return category


@router.patch("/{category_id}", response_model=schemas.Category)
async def update_category(
    category_id: uuid.UUID,
    data: schemas.CategoryUpdate,
    session: AsyncSession = Depends(database.get_session),
    current_user: User = Depends(get_current_user),
):
    """Обновить категорию."""
    category = await crud.update_category(
        session, category_id, data, current_user.account_id
    )
    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    return category


@router.delete("/{category_id}", status_code=204)
async def delete_category(
    category_id: uuid.UUID,
    session: AsyncSession = Depends(database.get_session),
    current_user: User = Depends(get_current_user),
):
    """Удалить категорию."""
    await crud.delete_category(session, category_id, current_user.account_id)
    return None
