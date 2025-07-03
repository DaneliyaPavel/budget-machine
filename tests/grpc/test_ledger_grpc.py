import sys
from pathlib import Path
import pytest
from grpclib.testing import ChannelFor
from google.protobuf.timestamp_pb2 import Timestamp

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend" / "app" / "grpc"))

from backend.app import models, schemas, crud, currency
from backend.app.grpc import ledger_grpc, ledger_pb2, server


@pytest.mark.asyncio
async def test_grpc_post_entry(session, monkeypatch):
    user = await crud.create_user(session, schemas.UserCreate(email="g@e.com", password="Pwd123$"))
    category = await crud.create_category(session, schemas.CategoryCreate(name="Food"), user.account_id, user.id)

    async def fake_rate(code: str) -> float:
        return 1.0

    monkeypatch.setattr(currency, "get_rate", fake_rate)

    service = server.LedgerService()
    async with ChannelFor([service]) as channel:
        stub = ledger_grpc.LedgerServiceStub(channel)
        req = ledger_pb2.PostEntryRequest(
            amount=50,
            currency="RUB",
            description="test",
            category_id=str(category.id),
            account_id=str(user.account_id),
            user_id=str(user.id),
            postings=[],
        )
        resp = await stub.PostEntry(req)
        assert resp.id

        bal = await stub.GetBalance(ledger_pb2.BalanceRequest(account_id=str(user.account_id)))
        assert bal.amount == 0

        txns = await stub.StreamTxns(
            ledger_pb2.StreamRequest(account_id=str(user.account_id))
        )
        assert len(txns) == 1
        assert txns[0].id == resp.id

