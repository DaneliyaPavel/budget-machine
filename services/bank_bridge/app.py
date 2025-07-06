from typing import Any

import aiohttp
from fastapi import FastAPI
from asyncio_jobs import Job, JobScheduler

app = FastAPI(title="Bank Bridge")

scheduler: JobScheduler | None = None


@app.on_event("startup")
async def startup() -> None:
    global scheduler
    scheduler = JobScheduler()
    scheduler.start()


@app.on_event("shutdown")
async def shutdown() -> None:
    if scheduler:
        await scheduler.close()


@app.get("/healthz")
async def health() -> dict[str, str]:
    return {"status": "ok"}


async def external_request(method: str, url: str, **kwargs: Any) -> Any:
    async with aiohttp.ClientSession() as session:
        async with session.request(method, url, **kwargs) as resp:
            resp.raise_for_status()
            return await resp.json()


@app.post("/connect/{bank}")
async def connect(bank: str) -> dict[str, str]:
    job = Job(coro=external_request("POST", f"https://api.example.com/{bank}/connect"))
    assert scheduler
    scheduler.spawn(job)
    return {"status": "connecting"}


@app.get("/status/{bank}")
async def status(bank: str) -> dict[str, Any]:
    data = await external_request("GET", f"https://api.example.com/{bank}/status")
    return {"status": data}


@app.post("/sync/{bank}")
async def sync(bank: str) -> dict[str, str]:
    job = Job(coro=external_request("POST", f"https://api.example.com/{bank}/sync"))
    assert scheduler
    scheduler.spawn(job)
    return {"status": "scheduled"}
