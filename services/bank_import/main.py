import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from aiokafka import AIOKafkaConsumer

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR))  # noqa: E402

from app import banks, crud, database  # noqa: E402

KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL", "localhost:9092")
TOPIC = os.getenv("BANK_TOPIC", "bank.raw")

app = FastAPI(title="Bank Import Service")

consumer: AIOKafkaConsumer | None = None


async def process_message(data: dict) -> None:
    connector = banks.get_connector(data["bank"], data["token"])
    txs = await connector.fetch_transactions(
        datetime.fromisoformat(data["start"]),
        datetime.fromisoformat(data["end"]),
    )
    async with database.async_session() as session:
        await crud.create_transactions_bulk(
            session, txs, data["account_id"], data["user_id"]
        )


async def consume_loop() -> None:
    assert consumer
    async for msg in consumer:
        data = json.loads(msg.value.decode())
        await process_message(data)


@app.on_event("startup")
async def startup() -> None:
    async with database.engine.begin() as conn:
        await conn.run_sync(database.Base.metadata.create_all)
    global consumer
    consumer = AIOKafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BROKER_URL,
        group_id="bank-import",
        enable_auto_commit=True,
    )
    await consumer.start()
    asyncio.create_task(consume_loop())


@app.on_event("shutdown")
async def shutdown() -> None:
    if consumer:
        await consumer.stop()


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
