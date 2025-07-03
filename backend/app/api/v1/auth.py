from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ... import crud, schemas, database
from ...core import security

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup", response_model=schemas.User)
async def signup(
    user: schemas.UserCreate, session: AsyncSession = Depends(database.get_session)
):
    """Регистрация нового пользователя."""
    try:
        security.validate_password(user.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    existing = await crud.get_user_by_email(session, user.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await crud.create_user(session, user)


@router.post("/login", response_model=schemas.TokenPair)
async def login(
    data: schemas.LoginRequest, session: AsyncSession = Depends(database.get_session)
):
    """Аутентифицировать пользователя и вернуть токены."""
    user = await crud.get_user_by_email(session, data.email)
    if not user or not security.verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    access = security.create_access_token({"sub": user.email})
    refresh = security.create_refresh_token({"sub": user.email})
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=schemas.TokenPair)
async def refresh(
    data: schemas.RefreshRequest, session: AsyncSession = Depends(database.get_session)
):
    """Обновить access-токен по refresh JWT."""
    try:
        payload = security.decode_token(data.refresh_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    email = payload.get("sub")
    user = await crud.get_user_by_email(session, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    access = security.create_access_token({"sub": email})
    refresh = security.create_refresh_token({"sub": email})
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}


MOCK_EMAIL = "mock@tinkoff.dev"


@router.get("/tinkoff/mock", response_model=schemas.Token)
async def tinkoff_mock(session: AsyncSession = Depends(database.get_session)) -> dict:
    """Выдать JWT для фиктивного пользователя Тинькофф."""
    email = MOCK_EMAIL
    user = await crud.get_user_by_email(session, email)
    if not user:
        user = await crud.create_user_oauth(session, email)
    token = security.create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}
