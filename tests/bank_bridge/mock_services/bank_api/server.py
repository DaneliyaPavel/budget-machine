import json
import os
from fastapi import FastAPI
import uvicorn

app = FastAPI()
BASE_DIR = os.getenv("STUB_DATA", "/data")


@app.get("/accounts")
async def accounts():
    path = os.path.join(BASE_DIR, "accounts.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/transactions")
async def transactions():
    path = os.path.join(BASE_DIR, "transactions.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
