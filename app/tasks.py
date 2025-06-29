from datetime import datetime
import asyncio

from .celery_app import celery_app
from . import notifications, banks, crud, database


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
        await notifications.send_message("\n".join(lines))
        return len(rows)

    return asyncio.run(_run())
