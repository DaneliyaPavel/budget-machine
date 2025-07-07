import asyncio
import json
import os

from fastapi import FastAPI
from aiokafka import AIOKafkaConsumer

from . import normalizer, kafka

KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL", "localhost:9092")
RAW_TOPIC = os.getenv("BANK_RAW_TOPIC", "bank.raw")

app = FastAPI(title="Bank Bridge Consumer")

consumer: AIOKafkaConsumer | None = None


async def _consume_loop() -> None:
    assert consumer
    async for msg in consumer:
        data = json.loads(msg.value.decode())
        await normalizer.process(data)


@app.on_event("startup")
async def startup() -> None:
    global consumer
    consumer = AIOKafkaConsumer(
        RAW_TOPIC,
        bootstrap_servers=KAFKA_BROKER_URL,
        enable_auto_commit=True,
        group_id="bank-bridge",
    )
    await consumer.start()
    asyncio.create_task(_consume_loop())


@app.on_event("shutdown")
async def shutdown() -> None:
    if consumer:
        await consumer.stop()
    await kafka.close()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
