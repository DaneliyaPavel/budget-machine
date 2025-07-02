from datetime import datetime, timezone
import asyncio
import os

from ..celery_app import celery_app
from .. import notifications, banks, crud, database, schemas
from clickhouse_connect import get_client


@celery_app.task
def send_telegram(text: str) -> None:
    """Отправить сообщение в Telegram."""
    asyncio.run(notifications.send_message(text))


@celery_app.task
def import_transactions_task(
    bank: str,
    token: str | None,
    start: str,
    end: str,
    account_id: int,
    user_id: int,
) -> int:
    """Импортировать операции из банка."""

    async def _run() -> int:
        connector = banks.get_connector(bank, user_id, token)
        txs = await connector.fetch_transactions(
            datetime.fromisoformat(start),
            datetime.fromisoformat(end),
        )
        async with database.async_session() as session:
            created = await crud.create_transactions_bulk(
                session, txs, account_id, user_id
            )
        return len(created)

    return asyncio.run(_run())


@celery_app.task
def export_summary_task(account_id: int, year: int, month: int) -> int:
    """Выгрузить помесячную сводку в ClickHouse."""

    async def _run() -> int:
        start = datetime(year, month, 1, tzinfo=timezone.utc)
        end = (
            datetime(year + 1, 1, 1, tzinfo=timezone.utc)
            if month == 12
            else datetime(year, month + 1, 1, tzinfo=timezone.utc)
        )
        async with database.async_session() as session:
            rows = await crud.transactions_summary_by_category(
                session, start, end, account_id
            )

        client = get_client(
            host=os.getenv("CLICKHOUSE_HOST", "clickhouse"),
            port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
            username=os.getenv("CLICKHOUSE_USER", "default"),
            password=os.getenv("CLICKHOUSE_PASSWORD", ""),
        )
        client.command(
            """
            CREATE TABLE IF NOT EXISTS summary_by_category (
                account_id UInt32,
                year UInt16,
                month UInt8,
                category String,
                total Float64
            ) ENGINE = MergeTree()
            ORDER BY (account_id, year, month, category)
            """
        )
        data = [
            {
                "account_id": account_id,
                "year": year,
                "month": month,
                "category": r[0],
                "total": float(r[1] or 0),
            }
            for r in rows
        ]
        if data:
            client.insert(
                "summary_by_category",
                data,
                column_names=["account_id", "year", "month", "category", "total"],
            )
        return len(data)

    return asyncio.run(_run())


@celery_app.task
def check_limits_task(account_id: int, year: int, month: int) -> int:
    """Проверить превышение лимитов и отправить уведомление."""

    async def _run() -> int:
        start = datetime(year, month, 1, tzinfo=timezone.utc)
        end = (
            datetime(year + 1, 1, 1, tzinfo=timezone.utc)
            if month == 12
            else datetime(year, month + 1, 1, tzinfo=timezone.utc)
        )
        async with database.async_session() as session:
            rows = await crud.categories_over_limit(session, start, end, account_id)
        if not rows:
            return 0
        lines = ["Превышение лимитов:"] + [
            f"{r[0]}: {float(r[2])} из {float(r[1])}" for r in rows
        ]
        message = "\n".join(lines)
        await notifications.send_message(message, account_id)
        return len(rows)

    return asyncio.run(_run())


@celery_app.task
def process_recurring_task(date: str) -> int:
    """Создать операции по регулярным платежам за указанный день."""

    async def _run() -> int:
        day = datetime.fromisoformat(date).day
        async with database.async_session() as session:
            payments = await crud.get_recurring_by_day(session, day)
            created = 0
            for p in payments:
                tx = schemas.TransactionCreate(
                    amount=float(p.amount),
                    currency=p.currency,
                    description=p.description or p.name,
                    category_id=p.category_id,
                    created_at=datetime.fromisoformat(date),
                )
                await crud.create_transaction(session, tx, p.account_id, p.user_id)
                created += 1
            return created

    return asyncio.run(_run())
