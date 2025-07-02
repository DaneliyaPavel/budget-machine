import os
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from . import crud, database, models

BOT_USER_ID = int(os.getenv("BOT_USER_ID", "1"))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправить приветственное сообщение."""
    await update.message.reply_text("Привет! Доступные команды: /summary и /limits")


async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать расходы по категориям за текущий месяц."""
    async with database.async_session() as session:
        user = await session.get(models.User, BOT_USER_ID)
        if not user:
            await update.message.reply_text("Пользователь не найден")
            return
        now = datetime.now(timezone.utc)
        start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        end = (
            datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)
            if now.month == 12
            else datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc)
        )
        rows = await crud.transactions_summary_by_category(
            session, start, end, user.account_id
        )
        if rows:
            lines = [f"{r[0]}: {float(r[1] or 0)}" for r in rows]
            text = "Сводка за месяц:\n" + "\n".join(lines)
        else:
            text = "Операций нет"
        await update.message.reply_text(text)


async def limits(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать категории с превышением лимитов."""
    async with database.async_session() as session:
        user = await session.get(models.User, BOT_USER_ID)
        if not user:
            await update.message.reply_text("Пользователь не найден")
            return
        now = datetime.now(timezone.utc)
        start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        end = (
            datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)
            if now.month == 12
            else datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc)
        )
        rows = await crud.categories_over_limit(session, start, end, user.account_id)
        if rows:
            lines = [f"{r[0]}: {float(r[2])} из {float(r[1])}" for r in rows]
            text = "Превышение лимитов:\n" + "\n".join(lines)
        else:
            text = "Лимиты не превышены"
        await update.message.reply_text(text)


def main() -> None:
    """Запустить Telegram-бота."""
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_TOKEN не задан")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(CommandHandler("limits", limits))
    app.run_polling()


if __name__ == "__main__":
    main()
