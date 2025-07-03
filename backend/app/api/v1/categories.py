from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ... import crud, schemas, database
from ...models import User
from .users import get_current_user

router = APIRouter(prefix="/categories", tags=["Категории"])


@router.get("/", response_model=list[schemas.Category])
async def read_categories(
    session: AsyncSession = Depends(database.get_session),
    current_user: User = Depends(get_current_user),
):
    """Вернуть список категорий пользователя."""
    return await crud.get_categories(session, current_user.account_id)


@router.post("/", response_model=schemas.Category)
async def create_category(
    category: schemas.CategoryCreate,
    session: AsyncSession = Depends(database.get_session),
    current_user: User = Depends(get_current_user),
):
    """Создать новую категорию."""
    if current_user.role == "readonly":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Forbidden", "code": "FORBIDDEN"},
        )
    return await crud.create_category(
        session, category, current_user.account_id, current_user.id
    )


@router.get("/{category_id}", response_model=schemas.Category)
async def read_category(
    category_id: UUID,
    session: AsyncSession = Depends(database.get_session),
    current_user: User = Depends(get_current_user),
):
    """Получить категорию по идентификатору."""
    category = await crud.get_category(session, category_id, current_user.account_id)
    if not category:
        raise HTTPException(
            status_code=404,
            detail={"detail": "Category not found", "code": "CATEGORY_NOT_FOUND"},
        )
    return category


@router.patch("/{category_id}", response_model=schemas.Category)
async def update_category(
    category_id: UUID,
    data: schemas.CategoryUpdate,
    session: AsyncSession = Depends(database.get_session),
    current_user: User = Depends(get_current_user),
):
    """Обновить категорию."""
    if current_user.role == "readonly":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Forbidden", "code": "FORBIDDEN"},
        )
    category = await crud.update_category(
        session, category_id, data, current_user.account_id
    )
    if not category:
        raise HTTPException(
            status_code=404,
            detail={"detail": "Category not found", "code": "CATEGORY_NOT_FOUND"},
        )
    return category


@router.delete("/{category_id}", status_code=204)
async def delete_category(
    category_id: UUID,
    session: AsyncSession = Depends(database.get_session),
    current_user: User = Depends(get_current_user),
):
    """Удалить категорию."""
    if current_user.role == "readonly":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Forbidden", "code": "FORBIDDEN"},
        )
    success = await crud.delete_category(session, category_id, current_user.account_id)
    if not success:
        raise HTTPException(
            status_code=409,
            detail={"detail": "Category has transactions", "code": "CATEGORY_IN_USE"},
        )
    return None
