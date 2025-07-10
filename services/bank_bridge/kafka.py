from __future__ import annotations

import json
import os
from typing import Any

from aiokafka import AIOKafkaProducer
import asyncio
import logging

KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL", "localhost:9092")
TRANSACTIONAL_ID = os.getenv("KAFKA_TRANSACTIONAL_ID", "bank-bridge")

logger = logging.getLogger(__name__)

_producer: AIOKafkaProducer | None = None


async def get_producer() -> AIOKafkaProducer:
    """Return a global Kafka producer with exactly-once guarantees."""
    global _producer
    if _producer is None:
        _producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BROKER_URL,
            enable_idempotence=True,
            transactional_id=TRANSACTIONAL_ID,
        )
        try:
            await asyncio.wait_for(_producer.start(), timeout=2)
            await asyncio.wait_for(_producer.init_transactions(), timeout=2)
        except Exception:
            await _producer.stop()
            _producer = None
            raise
    return _producer


async def publish(
    topic: str, user_id: str, bank_txn_id: str, data: dict[str, Any]
) -> None:
    """Send data to Kafka using `user_id:bank_txn_id` as key."""
    try:
        producer = await asyncio.wait_for(get_producer(), timeout=2)
    except Exception:  # pragma: no cover - network operations
        logger.warning("kafka unavailable")
        return

    key = f"{user_id}:{bank_txn_id}".encode()
    payload = json.dumps(data).encode()

    await producer.begin_transaction()
    try:
        await producer.send_and_wait(topic, payload, key=key)
        await producer.commit_transaction()
    except Exception:  # pragma: no cover - network operations
        logger.warning("publish failed")
        await producer.abort_transaction()


async def close() -> None:
    """Stop the producer if it was started."""
    global _producer
    if _producer is not None:
        await _producer.stop()
        _producer = None
