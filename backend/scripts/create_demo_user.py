import asyncio

from backend.app import crud, schemas, database


async def main() -> None:
    async with database.async_session() as session:
        existing = await crud.get_user_by_email(session, "demo@fintrack.dev")
        if existing:
            print("User already exists: demo@fintrack.dev")
            return
        user = schemas.UserCreate(email="demo@fintrack.dev", password="ChangeMe!123")
        await crud.create_user(session, user)
        print("Demo user created: demo@fintrack.dev / ChangeMe!123")


if __name__ == "__main__":
    asyncio.run(main())
