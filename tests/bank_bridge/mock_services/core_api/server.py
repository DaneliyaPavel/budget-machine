import json
from fastapi import FastAPI
import uvicorn

app = FastAPI()
TOKEN = json.dumps({"access_token": "x"})


@app.get("/v1/secret/bank_tokens/{bank}/{user_id}")
async def read_token(bank: str, user_id: str):
    return {"data": {"value": TOKEN}}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8200)
