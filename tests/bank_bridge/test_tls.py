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

    ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ctx.load_cert_chain(certfile, keyfile=str(keyfile))
    ctx.load_verify_locations(cafile)
    ctx.verify_mode = ssl.CERT_REQUIRED

    config = Config(app=app, host="127.0.0.1", port=0)
    config.ssl = ctx
    server = Server(config)
    task = asyncio.create_task(server.serve())
    # wait for the server to start
    while not server.started:
        await asyncio.sleep(0.01)
    port = server.servers[0].sockets[0].getsockname()[1]

    try:
        async with httpx.AsyncClient(verify=str(cafile)) as client:
            with pytest.raises(ssl.SSLError):
                await client.get(f"https://127.0.0.1:{port}/health")
    finally:
        server.should_exit = True
        await task
