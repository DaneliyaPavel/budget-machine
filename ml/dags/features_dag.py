from __future__ import annotations

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import json
import os
import pandas as pd
from clickhouse_connect import get_client
from aiokafka import AIOKafkaProducer
import asyncio

KAFKA_TOPIC = "features.txn"


def publish_features() -> None:
    client = get_client(
        host=os.getenv("CLICKHOUSE_HOST", "clickhouse"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
        username=os.getenv("CLICKHOUSE_USER", "default"),
        password=os.getenv("CLICKHOUSE_PASSWORD", ""),
    )
    df = client.query_df(
        "SELECT id, amount, description, category_id, created_at FROM transactions"
    )
    df["month"] = pd.to_datetime(df["created_at"]).dt.month
    features = df[["id", "amount", "month", "category_id"]].to_dict(orient="records")

    async def _send() -> None:
        producer = AIOKafkaProducer(
            bootstrap_servers=os.getenv("KAFKA_BROKER_URL", "kafka:9092")
        )
        await producer.start()
        for row in features:
            await producer.send_and_wait(KAFKA_TOPIC, json.dumps(row).encode())
        await producer.stop()

    asyncio.run(_send())


def _dummy() -> None:
    """Placeholder task for DAG initialization"""
    pass


with DAG(
    dag_id="collect_features",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False,
) as dag:
    run = PythonOperator(task_id="publish", python_callable=publish_features)
