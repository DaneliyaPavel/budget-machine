from __future__ import annotations

from datetime import datetime
from uuid import UUID

from grpclib.server import Server
from google.protobuf.timestamp_pb2 import Timestamp

from ..database import async_session
from .. import schemas, crud
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
            payee=request.payee or None,
            note=request.note or None,
            external_id=request.external_id or None,
            category_id=UUID(request.category_id),
            posted_at=_ts_to_dt(request.posted_at),
        )
        async with async_session() as session:
            postings = []
            for p in request.postings:
                acc = await crud.get_account(session, UUID(p.account_id))
                currency_code = acc.currency_code if acc else "RUB"
                postings.append(
                    schemas.PostingCreate(
                        amount=p.amount,
                        side=p.side,
                        account_id=UUID(p.account_id),
                        currency_code=currency_code,
                    )
                )
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
                        posted_at=_dt_to_ts(tx.posted_at),
                        payee=tx.payee or "",
                        note=tx.note or "",
                        external_id=tx.external_id or "",
                        category_id=str(tx.category_id) if tx.category_id else "",
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
