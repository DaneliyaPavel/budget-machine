import os
import ssl
import uvicorn


if __name__ == "__main__":
    from .app import app

    certfile = os.getenv("BANK_BRIDGE_CERTFILE")
    keyfile = os.getenv("BANK_BRIDGE_KEYFILE")
    cafile = os.getenv("BANK_BRIDGE_CA")
    host = os.getenv("BANK_BRIDGE_HOST", "0.0.0.0")
    port = int(os.getenv("BANK_BRIDGE_PORT", "8080"))

    if certfile and keyfile and cafile:
        config = uvicorn.Config(
            app,
            host=host,
            port=port,
            ssl_keyfile=keyfile,
            ssl_certfile=certfile,
            ssl_ca_certs=cafile,
            ssl_cert_reqs=ssl.CERT_REQUIRED,
        )
    else:
        config = uvicorn.Config(app, host=host, port=port)
    server = uvicorn.Server(config)
    server.run()
