import os
from datetime import date

import pandas as pd
import mlflow
import mlflow.pyfunc
from fastapi import FastAPI, Query

app = FastAPI(title="Predictor Service")

cat_model: mlflow.pyfunc.PyFuncModel | None = None
prophet_model: mlflow.pyfunc.PyFuncModel | None = None


@app.on_event("startup")
async def startup() -> None:
    global cat_model, prophet_model
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000"))
    cat_model = mlflow.pyfunc.load_model("models:/catboost/latest")
    prophet_model = mlflow.pyfunc.load_model("models:/prophet/latest")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/predict/category")
async def predict_category(
    amount: float = Query(...), month: int = Query(...)
) -> dict[str, int]:
    assert cat_model is not None
    df = pd.DataFrame({"amount": [amount], "month": [month]})
    pred = cat_model.predict(df)[0]
    return {"category_id": int(pred)}


@app.post("/predict/balance")
async def predict_balance(target_date: date = Query(...)) -> dict[str, float]:
    assert prophet_model is not None
    df = pd.DataFrame({"ds": [pd.to_datetime(target_date)]})
    forecast = prophet_model.predict(df)["yhat"].iloc[0]
    return {"balance": float(forecast)}
