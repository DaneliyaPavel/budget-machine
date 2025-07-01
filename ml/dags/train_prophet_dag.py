from __future__ import annotations

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import os
from clickhouse_connect import get_client
from prophet import Prophet
import mlflow


def train_prophet() -> None:
    client = get_client(
        host=os.getenv("CLICKHOUSE_HOST", "clickhouse"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
        username=os.getenv("CLICKHOUSE_USER", "default"),
        password=os.getenv("CLICKHOUSE_PASSWORD", ""),
    )
    df = client.query_df("SELECT created_at, balance FROM daily_balance")
    df.rename(columns={"created_at": "ds", "balance": "y"}, inplace=True)

    model = Prophet()
    model.fit(df)

    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000"))
    with mlflow.start_run(run_name="prophet"):
        mlflow.prophet.log_model(model, "model")


with DAG(
    dag_id="train_prophet",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
) as dag:
    train = PythonOperator(task_id="train", python_callable=train_prophet)
