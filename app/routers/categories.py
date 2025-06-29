"""Маршруты для работы с категориями."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from .. import crud, schemas, database, models
from .users import get_current_user
from .. import crud, schemas, database

router = APIRouter(prefix="/категории", tags=["Категории"])

@router.get("/", response_model=list[schemas.Category])
async def read_categories(
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Получить все категории."""
    return await crud.get_categories(session, current_user.id)

@router.post("/", response_model=schemas.Category)
async def create_category(
    category: schemas.CategoryCreate,
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Создать категорию."""
    return await crud.create_category(session, category, current_user.id)


@router.get("/{category_id}", response_model=schemas.Category)
async def read_category(
    category_id: int,
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Получить категорию по ID."""
    category = await crud.get_category(session, category_id, current_user.id)
async def read_categories(session: AsyncSession = Depends(database.get_session)):
    """Получить все категории."""
    return await crud.get_categories(session)

@router.post("/", response_model=schemas.Category)
async def create_category(category: schemas.CategoryCreate, session: AsyncSession = Depends(database.get_session)):
    """Создать категорию."""
    return await crud.create_category(session, category)


@router.get("/{category_id}", response_model=schemas.Category)
async def read_category(category_id: int, session: AsyncSession = Depends(database.get_session)):
    """Получить категорию по ID."""
    category = await crud.get_category(session, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    return category


@router.patch("/{category_id}", response_model=schemas.Category)
async def update_category(
    category_id: int,
    data: schemas.CategoryUpdate,
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Обновить выбранную категорию."""
    category = await crud.update_category(session, category_id, data, current_user.id)
async def update_category(category_id: int, data: schemas.CategoryUpdate, session: AsyncSession = Depends(database.get_session)):
    """Обновить выбранную категорию."""
    category = await crud.update_category(session, category_id, data)
    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    return category


@router.delete("/{category_id}", status_code=204)
async def delete_category(
    category_id: int,
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Удалить категорию."""
    await crud.delete_category(session, category_id, current_user.id)
async def delete_category(category_id: int, session: AsyncSession = Depends(database.get_session)):
    """Удалить категорию."""
    await crud.delete_category(session, category_id)
    return None
