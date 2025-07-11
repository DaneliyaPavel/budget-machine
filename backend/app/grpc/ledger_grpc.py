# Generated by the Protocol Buffers compiler. DO NOT EDIT!
# source: proto/ledger.proto
# plugin: grpclib.plugin.main
import abc
import typing

import grpclib.const
import grpclib.client

if typing.TYPE_CHECKING:
    import grpclib.server

from . import ledger_pb2


class LedgerServiceBase(abc.ABC):

    @abc.abstractmethod
    async def PostEntry(
        self,
        stream: "grpclib.server.Stream[ledger_pb2.PostEntryRequest, ledger_pb2.TxnId]",
    ) -> None:
        pass

    @abc.abstractmethod
    async def GetBalance(
        self,
        stream: "grpclib.server.Stream[ledger_pb2.BalanceRequest, ledger_pb2.BalanceResponse]",
    ) -> None:
        pass

    @abc.abstractmethod
    async def StreamTxns(
        self, stream: "grpclib.server.Stream[ledger_pb2.StreamRequest, ledger_pb2.Txn]"
    ) -> None:
        pass

    def __mapping__(self) -> typing.Dict[str, grpclib.const.Handler]:
        return {
            "/ledger.LedgerService/PostEntry": grpclib.const.Handler(
                self.PostEntry,
                grpclib.const.Cardinality.UNARY_UNARY,
                ledger_pb2.PostEntryRequest,
                ledger_pb2.TxnId,
            ),
            "/ledger.LedgerService/GetBalance": grpclib.const.Handler(
                self.GetBalance,
                grpclib.const.Cardinality.UNARY_UNARY,
                ledger_pb2.BalanceRequest,
                ledger_pb2.BalanceResponse,
            ),
            "/ledger.LedgerService/StreamTxns": grpclib.const.Handler(
                self.StreamTxns,
                grpclib.const.Cardinality.UNARY_STREAM,
                ledger_pb2.StreamRequest,
                ledger_pb2.Txn,
            ),
        }


class LedgerServiceStub:

    def __init__(self, channel: grpclib.client.Channel) -> None:
        self.PostEntry = grpclib.client.UnaryUnaryMethod(
            channel,
            "/ledger.LedgerService/PostEntry",
            ledger_pb2.PostEntryRequest,
            ledger_pb2.TxnId,
        )
        self.GetBalance = grpclib.client.UnaryUnaryMethod(
            channel,
            "/ledger.LedgerService/GetBalance",
            ledger_pb2.BalanceRequest,
            ledger_pb2.BalanceResponse,
        )
        self.StreamTxns = grpclib.client.UnaryStreamMethod(
            channel,
            "/ledger.LedgerService/StreamTxns",
            ledger_pb2.StreamRequest,
            ledger_pb2.Txn,
        )
