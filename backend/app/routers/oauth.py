from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from .. import database, crud, security, oauth
from .. import schemas

router = APIRouter(prefix="/oauth", tags=["OAuth"])


@router.get("/tinkoff/url", response_model=dict)
async def tinkoff_url() -> dict:
    """Получить URL для авторизации через Тинькофф ID."""
    return {"url": oauth.build_auth_url()}


@router.get("/tinkoff/callback", response_model=schemas.Token)
async def tinkoff_callback(
    code: str = Query(..., description="Authorization code"),
    session: AsyncSession = Depends(database.get_session),
):
    """Обработать код авторизации Тинькофф и выдать JWT."""
    try:
        email = await oauth.exchange_code(code)
    except Exception as exc:  # pragma: no cover - network errors
        raise HTTPException(status_code=400, detail="OAuth error") from exc
    user = await crud.get_user_by_email(session, email)
    if not user:
        user = await crud.create_user_oauth(session, email)
    token = security.create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}
