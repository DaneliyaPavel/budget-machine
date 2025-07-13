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

    config = uvicorn.Config(app, host=host, port=port)
    if certfile and keyfile and cafile:
        ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ctx.load_cert_chain(certfile, keyfile)
        ctx.load_verify_locations(cafile)
        ctx.verify_mode = ssl.CERT_REQUIRED
        config.ssl = ctx
    server = uvicorn.Server(config)
    server.run()
