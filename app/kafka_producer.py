"""Kafka producer for publishing bank import requests."""

import json
import os
from typing import Any

from aiokafka import AIOKafkaProducer

KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL")

_producer: AIOKafkaProducer | None = None


async def get_producer() -> AIOKafkaProducer | None:
    """Initialize and return global producer if Kafka configured."""
    global _producer
    if KAFKA_BROKER_URL is None:
        return None
    if _producer is None:
        _producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BROKER_URL)
        await _producer.start()
    return _producer


async def publish(topic: str, data: dict[str, Any]) -> None:
    """Publish JSON data to Kafka topic if broker configured."""
    producer = await get_producer()
    if producer is None:
        return
    await producer.send_and_wait(topic, json.dumps(data).encode())


async def close() -> None:
    """Close the producer."""
    global _producer
    if _producer is not None:
        await _producer.stop()
        _producer = None
