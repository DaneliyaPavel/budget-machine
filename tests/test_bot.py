import sys
from pathlib import Path
import types


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import telegram_bot, crud, database


class DummyMsg:
    def __init__(self):
        self.text = None

    async def reply_text(self, text: str):
        self.text = text


class DummySession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def get(self, model, pk):
        return types.SimpleNamespace(account_id=1)


def test_summary_and_limits(monkeypatch):
    messages = []
    update = types.SimpleNamespace(message=DummyMsg())

    async def fake_summary(session, start, end, account_id):
        return [("Food", 100)]

    async def fake_limits(session, start, end, account_id):
        return [("Food", 50, 80)]

    monkeypatch.setattr(database, "async_session", lambda: DummySession())
    monkeypatch.setattr(crud, "transactions_summary_by_category", fake_summary)
    monkeypatch.setattr(crud, "categories_over_limit", fake_limits)

    import asyncio

    asyncio.run(telegram_bot.summary(update, None))
    messages.append(update.message.text)
    assert "Сводка" in messages[-1]

    update.message.text = None
    asyncio.run(telegram_bot.limits(update, None))
    messages.append(update.message.text)
    assert "Превышение" in messages[-1]
