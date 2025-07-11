import asyncio
import os
import re
from playwright.async_api import async_playwright
from services.bank_bridge.connectors.tinkoff import TinkoffConnector, TokenPair

LOGIN = os.getenv("TINKOFF_SANDBOX_LOGIN")
PASSWORD = os.getenv("TINKOFF_SANDBOX_PASSWORD")


async def main() -> None:
    if not LOGIN or not PASSWORD:
        print("Missing sandbox credentials, skipping")
        return
    connector = TinkoffConnector(user_id="sandbox-test", token=None)
    pair: TokenPair = await connector.auth(None)
    auth_url = pair.access_token
    redirect_uri = connector.redirect_uri

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(auth_url)
        await page.fill('input[type="text"]', LOGIN)
        await page.fill('input[type="password"]', PASSWORD)
        await page.click('button[type="submit"]')
        await page.wait_for_url(
            re.compile(re.escape(redirect_uri) + r".*"), timeout=15000
        )
        await browser.close()
        print("Sandbox authorization successful")


if __name__ == "__main__":
    asyncio.run(main())
