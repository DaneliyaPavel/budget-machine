from __future__ import annotations

from datetime import datetime
from uuid import UUID

from grpclib.server import Server
from google.protobuf.timestamp_pb2 import Timestamp

from ..database import async_session
from .. import schemas
from ..services import ledger

from . import ledger_grpc, ledger_pb2


def _ts_to_dt(ts: Timestamp | None) -> datetime | None:
    if ts is None or (ts.seconds == 0 and ts.nanos == 0):
        return None
    return datetime.fromtimestamp(ts.seconds + ts.nanos / 1e9)


def _dt_to_ts(dt: datetime) -> Timestamp:
    ts = Timestamp()
    ts.FromDatetime(dt)
    return ts


class LedgerService(ledger_grpc.LedgerServiceBase):
    async def PostEntry(self, stream) -> None:
        request = await stream.recv_message()
        assert request is not None
        txn = schemas.TransactionCreate(
            amount=request.amount,
            currency=request.currency,
            description=request.description or None,
            category_id=UUID(request.category_id),
            created_at=_ts_to_dt(request.created_at),
        )
        postings = [
            schemas.PostingCreate(
                amount=p.amount,
                side=p.side,
                account_id=UUID(p.account_id),
            )
            for p in request.postings
        ]
        async with async_session() as session:
            tx = await ledger.post_entry(
                session, txn, postings, UUID(request.account_id), UUID(request.user_id)
            )
        response = ledger_pb2.TxnId(
            id=str(tx.id),
        )
        await stream.send_message(response)

    async def GetBalance(self, stream) -> None:
        request = await stream.recv_message()
        assert request is not None
        async with async_session() as session:
            amount = await ledger.get_balance(
                session,
                UUID(request.account_id),
                _ts_to_dt(request.at),
            )
        await stream.send_message(ledger_pb2.BalanceResponse(amount=amount))

    async def StreamTxns(self, stream) -> None:
        request = await stream.recv_message()
        assert request is not None
        async with async_session() as session:
            async for tx in ledger.stream_transactions(
                session,
                UUID(request.account_id),
                _ts_to_dt(request.start),
                _ts_to_dt(request.end),
            ):
                await stream.send_message(
                    ledger_pb2.Txn(
                        id=str(tx.id),
                        amount=tx.amount,
                        currency=tx.currency,
                        amount_rub=tx.amount_rub,
                        description=tx.description or "",
                        category_id=str(tx.category_id),
                        created_at=_dt_to_ts(tx.created_at),
                        account_id=str(tx.account_id),
                        user_id=str(tx.user_id),
                    )
                )


def serve(host: str = "0.0.0.0", port: int = 50051) -> Server:
    service = LedgerService()
    server = Server([service])
    return server


async def _main(host: str = "0.0.0.0", port: int = 50051) -> None:
    server = serve()
    await server.start(host, port)
    await server.wait_closed()


if __name__ == "__main__":
    import asyncio

    asyncio.run(_main())
