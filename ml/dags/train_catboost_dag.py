from __future__ import annotations

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import os
from clickhouse_connect import get_client
from catboost import CatBoostClassifier
import mlflow


def train_model() -> None:
    client = get_client(
        host=os.getenv("CLICKHOUSE_HOST", "clickhouse"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
        username=os.getenv("CLICKHOUSE_USER", "default"),
        password=os.getenv("CLICKHOUSE_PASSWORD", ""),
    )
    df = client.query_df("SELECT amount, month, category_id FROM features")
    X = df[["amount", "month"]]
    y = df["category_id"]

    model = CatBoostClassifier(iterations=100, verbose=False)
    model.fit(X, y)

    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000"))
    with mlflow.start_run(run_name="catboost"):
        mlflow.catboost.log_model(model, "model")


with DAG(
    dag_id="train_catboost",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
) as dag:
    task = PythonOperator(task_id="train", python_callable=train_model)
