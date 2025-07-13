import asyncio
import ssl
from pathlib import Path

import pytest
import httpx
from uvicorn import Config, Server
from services.bank_bridge.app import app


@pytest.mark.asyncio
async def test_client_cert_required(tmp_path):
    cert_dir = Path(__file__).with_name("tls")
    certfile = cert_dir / "server.crt"
    keyfile = cert_dir / "server.key"
    cafile = cert_dir / "ca.crt"

    config = Config(
        app=app,
        host="127.0.0.1",
        port=0,
        ssl_keyfile=str(keyfile),
        ssl_certfile=str(certfile),
        ssl_ca_certs=str(cafile),
        ssl_cert_reqs=ssl.CERT_REQUIRED,
    )
    server = Server(config)
    task = asyncio.create_task(server.serve())
    # wait for the server to start
    while not server.started:
        await asyncio.sleep(0.01)
    port = server.servers[0].sockets[0].getsockname()[1]

    try:
        async with httpx.AsyncClient(verify=str(cafile)) as client:
            with pytest.raises((ssl.SSLError, httpx.ReadError)):
                await client.get(f"https://localhost:{port}/health")
    finally:
        server.should_exit = True
        await task
