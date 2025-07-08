from __future__ import annotations


import json
import logging
import sys
from datetime import date, timedelta

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response
from aiojobs import create_scheduler, Scheduler

from . import kafka, vault, schema_registry
import os
from .connectors import get_connector, TokenPair
from prometheus_client import (
    Histogram,
    Counter,
    CONTENT_TYPE_LATEST,
    generate_latest,
)

app = FastAPI(title="Bank Bridge")

scheduler: "Scheduler" | None = None

RAW_TOPIC = os.getenv("BANK_RAW_TOPIC", "bank.raw")


async def _load_token(bank: str, user_id: str) -> TokenPair | None:
    data = await vault.get_vault_client().read(f"bank_tokens/{bank}/{user_id}")
    if not data:
        return None
    obj = json.loads(data)
    return TokenPair(
        access_token=obj.get("access_token", ""),
        refresh_token=obj.get("refresh_token"),
    )


async def _full_sync(bank: str, user_id: str) -> None:
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
    await schema_registry.register_all()


@app.on_event("shutdown")
async def shutdown() -> None:
    if scheduler:
        await scheduler.close()
    await kafka.close()


@app.get("/healthz")
async def health() -> dict[str, str]:
    """Return service health status."""
    try:
        await kafka.get_producer()
    except Exception:  # pragma: no cover - network operations
        raise HTTPException(status_code=503, detail="kafka")

    try:
        await vault.get_vault_client().read("health-check")
    except Exception:  # pragma: no cover - network operations
        raise HTTPException(status_code=503, detail="vault")

    return {"status": "ok"}


@app.post("/connect/{bank}")
async def connect(bank: str, user_id: str = "default") -> dict[str, str]:
    """Return authorization URL for the requested bank."""
    connector_cls = get_connector(bank)
    connector = connector_cls(user_id)
    pair = await connector.auth(None)
    return {"url": pair.access_token}


@app.get("/status/{bank}")
async def status(bank: str, user_id: str = "default") -> dict[str, str]:
    """Check connection status for the bank."""
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
async def sync(bank: str, user_id: str = "default") -> dict[str, str]:
    """Schedule full data synchronization with bank."""
    assert scheduler
    await scheduler.spawn(_full_sync(bank, user_id))
    return {"status": "scheduled"}


@app.post("/webhook/tinkoff/{user_id}")
async def tinkoff_webhook(user_id: str, request: Request) -> dict[str, str]:
    """Handle Tinkoff sandbox operation webhook."""
    data = await request.json()
    if data.get("event") != "operation":
        return {"status": "ignored"}
    payload = data.get("payload", {})
    bank_txn_id = str(payload.get("id") or payload.get("bank_txn_id", ""))
    msg = {"user_id": user_id, "bank_txn_id": bank_txn_id, "payload": payload}
    await kafka.publish(RAW_TOPIC, user_id, bank_txn_id, msg)
    return {"status": "ok"}


@app.get("/metrics")
async def metrics() -> Response:
    """Expose Prometheus metrics."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
