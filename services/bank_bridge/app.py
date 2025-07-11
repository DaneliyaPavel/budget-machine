from __future__ import annotations


import json
import logging
import sys
from datetime import date, timedelta
import asyncio
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Path, Request
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse
import re
from fastapi.responses import Response
from aiojobs import create_scheduler, Scheduler

from . import kafka, vault, schema_registry
import os
from .connectors import get_connector, TokenPair, CONNECTORS
from enum import Enum
from prometheus_client import (
    Histogram,
    Counter,
    CONTENT_TYPE_LATEST,
    generate_latest,
)

app = FastAPI(title="Bank Bridge")

scheduler: "Scheduler" | None = None

RAW_TOPIC = os.getenv("BANK_RAW_TOPIC", "bank.raw")


_USER_ID_PATTERN = r"^[0-9a-fA-F-]{36}$"
_USER_ID_RE = re.compile(_USER_ID_PATTERN)


def _validate_user_id(value: str) -> str:
    if not _USER_ID_RE.match(value):
        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "loc": ["query", "user_id"],
                    "msg": "invalid user_id",
                    "type": "value_error",
                }
            ],
        )
    return value


def _get_user_id(request: Request, user_id: str) -> str:
    """Validate that only a single user_id parameter is provided."""
    if len(request.query_params.getlist("user_id")) > 1:
        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "loc": ["query", "user_id"],
                    "msg": "duplicate user_id",
                    "type": "value_error",
                }
            ],
        )
    return _validate_user_id(user_id)


class TinkoffEvent(str, Enum):
    """Supported webhook events."""

    OPERATION = "operation"


class TinkoffWebhook(BaseModel):
    """Webhook payload for Tinkoff operations."""

    event: TinkoffEvent = Field(..., description="Event type")
    payload: dict[str, Any] = Field(default_factory=dict)


class HealthStatus(BaseModel):
    """Service health check response."""

    status: str


class BankName(str, Enum):
    """Supported bank connectors."""

    TINKOFF = "tinkoff"
    SBER = "sber"
    GAZPROM = "gazprom"
    ALFA = "alfa"
    VTB = "vtb"


async def _load_token(bank: BankName, user_id: str) -> TokenPair | None:
    try:
        data = await vault.get_vault_client().read(f"bank_tokens/{bank}/{user_id}")
    except Exception:  # pragma: no cover - network operations
        return None
    if not data:
        return None
    obj = json.loads(data)
    return TokenPair(
        access_token=obj.get("access_token", ""),
        refresh_token=obj.get("refresh_token"),
    )


async def _full_sync(bank: BankName, user_id: str) -> None:
    token = await _load_token(bank, user_id)
    if token is None:
        logger.error("missing token", extra={"bank": bank})
        return

    connector_cls = get_connector(bank)
    connector = connector_cls(user_id, token)

    try:
        accounts = await connector.fetch_accounts(token)
    except Exception:
        ERROR_TOTAL.inc()
        logger.error("accounts_error", extra={"bank": bank})
        await kafka.publish(
            "bank.err",
            user_id,
            "",
            {
                "user_id": user_id,
                "external_id": "",
                "bank_id": bank,
                "error_code": "CONNECTOR_ERROR",
                "stage": "connector",
                "payload": {"operation": "fetch_accounts"},
            },
        )
        return

    end = date.today()
    start = end - timedelta(days=30)
    for account in accounts:
        try:
            async for raw in connector.fetch_txns(token, account, start, end):
                msg = {
                    "user_id": user_id,
                    "bank_txn_id": str(
                        raw.data.get("id") or raw.data.get("bank_txn_id", "")
                    ),
                    "payload": dict(raw.data),
                }
                await kafka.publish(RAW_TOPIC, user_id, msg["bank_txn_id"], msg)
                TXN_COUNT.inc()
        except Exception:
            ERROR_TOTAL.inc()
            logger.error("sync_error", extra={"bank": bank})
            await kafka.publish(
                "bank.err",
                user_id,
                "",
                {
                    "user_id": user_id,
                    "external_id": "",
                    "bank_id": bank,
                    "error_code": "CONNECTOR_ERROR",
                    "stage": "connector",
                    "payload": {"operation": "fetch_txns", "account": account.id},
                },
            )


async def _refresh_tokens_once(user_id: str = "default") -> None:
    for bank in CONNECTORS:
        token = await _load_token(bank, user_id)
        if not token or not token.refresh_token:
            continue
        connector_cls = get_connector(bank)
        connector = connector_cls(user_id, token)
        try:
            await connector.refresh(token)
        except Exception:
            ERROR_TOTAL.inc()
            logger.error("refresh_error", extra={"bank": bank})
            await kafka.publish(
                "bank.err",
                user_id,
                "",
                {
                    "user_id": user_id,
                    "external_id": "",
                    "bank_id": bank,
                    "error_code": "CONNECTOR_ERROR",
                    "stage": "refresh",
                    "payload": {},
                },
            )


async def _refresh_tokens_loop() -> None:
    while True:
        try:
            await _refresh_tokens_once()
        except Exception:  # pragma: no cover - network operations
            logger.warning("refresh_loop_error")
        await asyncio.sleep(24 * 60 * 60)


FETCH_LATENCY_MS = Histogram(
    "bankbridge_fetch_latency_ms", "Latency of external bank requests in ms"
)
TXN_COUNT = Counter("bankbridge_txn_count", "Number of bank transactions processed")
ERROR_TOTAL = Counter("bankbridge_error_total", "Total errors when calling bank APIs")
RATE_LIMITED = Counter("bankbridge_rate_limited", "Count of rate limited responses")


class JsonFormatter(logging.Formatter):
    """Format log records as JSON for Loki."""

    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        data = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname.lower(),
            "message": record.getMessage(),
        }
        if hasattr(record, "bank"):
            data["bank"] = record.bank
        return json.dumps(data)


handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
logger = logging.getLogger("bank_bridge")
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.propagate = False


@app.on_event("startup")
async def startup() -> None:
    global scheduler
    scheduler = await create_scheduler()
    await scheduler.spawn(_refresh_tokens_loop())
    await schema_registry.register_all()


@app.on_event("shutdown")
async def shutdown() -> None:
    if scheduler:
        await scheduler.close()
    await kafka.close()


@app.get(
    "/healthz",
    response_model=HealthStatus,
)
async def health() -> JSONResponse:
    """Return service health status."""
    degraded = False
    try:
        await kafka.get_producer()
    except Exception:  # pragma: no cover - network operations
        degraded = True

    try:
        await vault.get_vault_client().read("health-check")
    except Exception:  # pragma: no cover - network operations
        degraded = True

    payload = {"status": "ok" if not degraded else "degraded"}
    return JSONResponse(content=payload, status_code=200)


@app.post("/connect/{bank}")
async def connect(
    request: Request,
    bank: BankName,
    user_id: str = Query(
        "00000000-0000-0000-0000-000000000001",
        min_length=1,
        pattern=_USER_ID_PATTERN,
    ),
) -> dict[str, str]:
    """Return authorization URL for the requested bank."""
    user_id = _get_user_id(request, user_id)
    connector_cls = get_connector(bank)
    connector = connector_cls(user_id)
    pair = await connector.auth(None)
    return {"url": pair.access_token}


@app.get("/status/{bank}")
async def status(
    request: Request,
    bank: BankName,
    user_id: str = Query(
        "00000000-0000-0000-0000-000000000001",
        min_length=1,
        pattern=_USER_ID_PATTERN,
    ),
) -> dict[str, str]:
    """Check connection status for the bank."""
    user_id = _get_user_id(request, user_id)
    token = await _load_token(bank, user_id)
    if token is None:
        return {"status": "DISCONNECTED"}

    connector_cls = get_connector(bank)
    connector = connector_cls(user_id, token)
    try:
        await connector.fetch_accounts(token)
    except Exception:
        ERROR_TOTAL.inc()
        logger.error("status_error", extra={"bank": bank})
        return {"status": "ERROR"}

    return {"status": "CONNECTED"}


@app.post("/sync/{bank}")
async def sync(
    request: Request,
    bank: BankName,
    user_id: str = Query(
        "00000000-0000-0000-0000-000000000001",
        min_length=1,
        pattern=_USER_ID_PATTERN,
    ),
) -> dict[str, str]:
    """Schedule full data synchronization with bank."""
    user_id = _get_user_id(request, user_id)
    assert scheduler
    await scheduler.spawn(_full_sync(bank, user_id))
    return {"status": "scheduled"}


@app.post("/webhook/tinkoff/{user_id}")
async def tinkoff_webhook(
    body: "TinkoffWebhook",
    user_id: str = Path(..., pattern=_USER_ID_PATTERN),
) -> dict[str, str]:
    """Handle Tinkoff sandbox operation webhook."""
    payload = body.payload
    bank_txn_id = str(payload.get("id") or payload.get("bank_txn_id", ""))
    msg = {"user_id": user_id, "bank_txn_id": bank_txn_id, "payload": payload}
    asyncio.create_task(kafka.publish(RAW_TOPIC, user_id, bank_txn_id, msg))
    return {"status": "ok"}


@app.get(
    "/metrics",
    responses={200: {"content": {"text/plain": {}}}},
)
async def metrics() -> Response:
    """Expose Prometheus metrics."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
