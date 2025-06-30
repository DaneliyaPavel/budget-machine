from datetime import datetime
import asyncio

from ..celery_app import celery_app
from .. import notifications, banks, crud, database, schemas


@celery_app.task
def send_telegram(text: str) -> None:
    """Отправить сообщение в Telegram."""
    asyncio.run(notifications.send_message(text))


@celery_app.task
def import_transactions_task(
    bank: str,
    token: str,
    start: str,
    end: str,
    account_id: int,
    user_id: int,
) -> int:
    """Импортировать операции из банка."""

    async def _run() -> int:
        connector = banks.get_connector(bank, token)
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
def check_limits_task(account_id: int, year: int, month: int) -> int:
    """Проверить превышение лимитов и отправить уведомление."""

    async def _run() -> int:
        start = datetime(year, month, 1)
        end = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)
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
