"""Маршруты для операций."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Query

from sqlalchemy.ext.asyncio import AsyncSession
import csv
from datetime import datetime
from .. import crud, schemas, database, models
from .users import get_current_user


router = APIRouter(prefix="/операции", tags=["Операции"])

@router.get("/", response_model=list[schemas.Transaction])
async def read_transactions(
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Получить список операций."""
    return await crud.get_transactions(session, current_user.account_id)
    start: datetime | None = Query(None, description="Начало периода"),
    end: datetime | None = Query(None, description="Конец периода"),
    category_id: int | None = Query(None, description="Категория"),
):
    """Получить список операций с фильтрами по дате и категории."""
    return await crud.get_transactions(
        session,
        current_user.id,
        start=start,
        end=end,
        category_id=category_id,
    )
):
    """Получить список операций."""
    return await crud.get_transactions(session, current_user.id)

@router.post("/", response_model=schemas.Transaction)
async def create_transaction(
    tx: schemas.TransactionCreate,
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Создать новую операцию."""
    return await crud.create_transaction(
        session,
        tx,
        current_user.account_id,
        current_user.id,
    )
    return await crud.create_transaction(session, tx, current_user.id)
async def read_transactions(session: AsyncSession = Depends(database.get_session)):
    """Получить список операций."""
    return await crud.get_transactions(session)

@router.post("/", response_model=schemas.Transaction)
async def create_transaction(tx: schemas.TransactionCreate, session: AsyncSession = Depends(database.get_session)):
    """Создать новую операцию."""
    return await crud.create_transaction(session, tx)


@router.post("/импорт", status_code=status.HTTP_201_CREATED)
async def import_transactions(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Импортировать операции из CSV-файла."""
    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(text.splitlines())
    created = []
    for row in reader:
        try:
            created_at = (
                datetime.fromisoformat(row["created_at"])
                if row.get("created_at")
                else None
            )
        except ValueError:
            created_at = None
        tx = schemas.TransactionCreate(
            amount=float(row["amount"]),
            currency=row.get("currency", "RUB"),
            description=row.get("description"),
            category_id=int(row["category_id"]),
            created_at=created_at,
        )
        created.append(tx)
    await crud.create_transactions_bulk(
        session, created, current_user.account_id, current_user.id
    )
    await crud.create_transactions_bulk(session, created, current_user.id)
    await crud.create_transactions_bulk(session, created)
    return {"created": len(created)}


@router.get("/{tx_id}", response_model=schemas.Transaction)
async def read_transaction(
    tx_id: int,
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Получить одну операцию."""
    tx = await crud.get_transaction(session, tx_id, current_user.account_id)
async def read_transaction(tx_id: int, session: AsyncSession = Depends(database.get_session)):
    if not tx:
        raise HTTPException(status_code=404, detail="Операция не найдена")
    return tx


@router.patch("/{tx_id}", response_model=schemas.Transaction)
async def update_transaction(
    tx_id: int,
    data: schemas.TransactionUpdate,
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Изменить операцию."""
    tx = await crud.update_transaction(
        session, tx_id, data, current_user.account_id, current_user.id
    )
    if not tx:
        raise HTTPException(status_code=404, detail="Операция не найдена")
    return tx


@router.delete("/{tx_id}", status_code=204)
async def delete_transaction(
    tx_id: int,
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Удалить операцию."""
    await crud.delete_transaction(session, tx_id, current_user.account_id)
    return None
