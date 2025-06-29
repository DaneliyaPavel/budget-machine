"""Маршруты для операций."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
import csv
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from .. import crud, schemas, database

router = APIRouter(prefix="/операции", tags=["Операции"])

@router.get("/", response_model=list[schemas.Transaction])
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
    await crud.create_transactions_bulk(session, created)
    return {"created": len(created)}


@router.get("/{tx_id}", response_model=schemas.Transaction)
async def read_transaction(tx_id: int, session: AsyncSession = Depends(database.get_session)):
    """Получить одну операцию."""
    tx = await crud.get_transaction(session, tx_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Операция не найдена")
    return tx


@router.patch("/{tx_id}", response_model=schemas.Transaction)
async def update_transaction(tx_id: int, data: schemas.TransactionUpdate, session: AsyncSession = Depends(database.get_session)):
    """Изменить операцию."""
    tx = await crud.update_transaction(session, tx_id, data)
    if not tx:
        raise HTTPException(status_code=404, detail="Операция не найдена")
    return tx


@router.delete("/{tx_id}", status_code=204)
async def delete_transaction(tx_id: int, session: AsyncSession = Depends(database.get_session)):
    """Удалить операцию."""
    await crud.delete_transaction(session, tx_id)
    return None
