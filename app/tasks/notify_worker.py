import asyncio
import os
import redis.asyncio as redis

from .. import notifications, crud, database

REDIS_URL = os.getenv("REDIS_URL", os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"))


async def main() -> None:
    r = redis.from_url(REDIS_URL, decode_responses=True)
    last_id = "0-0"
    while True:
        streams = await r.xread({"notifications": last_id}, block=0, count=1)
        if not streams:
            continue
        _, messages = streams[0]
        for msg_id, data in messages:
            last_id = msg_id
            text = data.get("text", "")
            account_id = data.get("account_id")
            await notifications.send_telegram(text)
            if account_id:
                async with database.async_session() as session:
                    subs = await crud.get_push_subscriptions(session, int(account_id))
                for s in subs:
                    notifications.send_push(s.endpoint, s.p256dh, s.auth, text)


if __name__ == "__main__":
    asyncio.run(main())
