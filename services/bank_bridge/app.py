from typing import Any

import aiohttp
import json
import logging
import sys
import time
from fastapi import FastAPI
from fastapi.responses import Response
from aiojobs import create_scheduler, Scheduler
from prometheus_client import (
    Histogram,
    Counter,
    CONTENT_TYPE_LATEST,
    generate_latest,
)

app = FastAPI(title="Bank Bridge")

scheduler: "Scheduler" | None = None


FETCH_LATENCY_MS = Histogram(
    "bankbridge_fetch_latency_ms", "Latency of external bank requests in ms"
)
TXN_COUNT = Counter(
    "bankbridge_txn_count", "Number of bank transactions processed"
)
ERROR_TOTAL = Counter(
    "bankbridge_error_total", "Total errors when calling bank APIs"
)
RATE_LIMITED = Counter(
    "bankbridge_rate_limited", "Count of rate limited responses"
)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        data = {"level": record.levelname}
        if hasattr(record, "bank"):
            data["bank"] = record.bank
        data["message"] = record.getMessage()
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


@app.on_event("shutdown")
async def shutdown() -> None:
    if scheduler:
        await scheduler.close()


@app.get("/healthz")
async def health() -> dict[str, str]:
    return {"status": "ok"}


async def external_request(bank: str, method: str, url: str, **kwargs: Any) -> Any:
    """Make HTTP request to external bank API with metrics and logging."""
    start = time.perf_counter()
    logger.info("request", extra={"bank": bank})
    async with aiohttp.ClientSession() as session:
        try:
            async with session.request(method, url, **kwargs) as resp:
                if resp.status == 429:
                    RATE_LIMITED.inc()
                resp.raise_for_status()
                data = await resp.json()
                if isinstance(data, list):
                    TXN_COUNT.inc(len(data))
                return data
        except Exception:
            ERROR_TOTAL.inc()
            logger.error("error", extra={"bank": bank})
            raise
        finally:
            FETCH_LATENCY_MS.observe((time.perf_counter() - start) * 1000)


@app.post("/connect/{bank}")
async def connect(bank: str) -> dict[str, str]:
    assert scheduler
    await scheduler.spawn(
        external_request(bank, "POST", f"https://api.example.com/{bank}/connect")
    )
    return {"status": "connecting"}


@app.get("/status/{bank}")
async def status(bank: str) -> dict[str, Any]:
    data = await external_request(bank, "GET", f"https://api.example.com/{bank}/status")
    return {"status": data}


@app.post("/sync/{bank}")
async def sync(bank: str) -> dict[str, str]:
    assert scheduler
    await scheduler.spawn(
        external_request(bank, "POST", f"https://api.example.com/{bank}/sync")
    )
    return {"status": "scheduled"}


@app.get("/metrics")
async def metrics() -> Response:
    """Expose Prometheus metrics."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
