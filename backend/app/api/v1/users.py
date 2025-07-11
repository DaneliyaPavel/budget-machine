from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from ... import crud, schemas, database, security
from ...models import User
from ..utils import api_error

router = APIRouter(prefix="/users", tags=["Пользователи"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(database.get_session),
) -> User:
    """Вернуть текущего пользователя по JWT."""
    try:
        payload = jwt.decode(
            token, security.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        email: str = payload.get("sub")
    except JWTError:
        raise api_error(status.HTTP_401_UNAUTHORIZED, "Invalid token", "INVALID_TOKEN")
    user = await crud.get_user_by_email(session, email)
    if not user:
        raise api_error(
            status.HTTP_401_UNAUTHORIZED, "User not found", "USER_NOT_FOUND"
        )
    return user


@router.post("/", response_model=schemas.User)
async def create_user(
    user: schemas.UserCreate, session: AsyncSession = Depends(database.get_session)
):
    """Зарегистрировать нового пользователя."""
    try:
        security.validate_password(user.password)
    except ValueError as exc:
        raise api_error(400, str(exc), "INVALID_PASSWORD") from exc
    db_user = await crud.get_user_by_email(session, user.email)
    if db_user:
        raise api_error(400, "Email already registered", "EMAIL_EXISTS")
    return await crud.create_user(session, user)


@router.post("/join", response_model=schemas.User)
async def join_account(
    data: schemas.JoinAccount,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(database.get_session),
):
    """Присоединиться к существующему счёту."""
    user = await crud.join_account(session, current_user, data.account_id)
    if not user:
        raise api_error(404, "Account not found", "ACCOUNT_NOT_FOUND")
    return user


@router.get("/members", response_model=list[schemas.User])
async def account_members(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(database.get_session),
):
    """Список участников счёта."""
    return await crud.get_account_users(session, current_user.account_id)


@router.delete("/{user_id}", status_code=204)
async def remove_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(database.get_session),
):
    """Удалить пользователя из счёта."""
    if current_user.role != "owner" and current_user.id != user_id:
        raise api_error(403, "Forbidden", "FORBIDDEN")
    ok = await crud.delete_user(session, user_id, current_user.account_id)
    if not ok:
        raise api_error(404, "User not found", "USER_NOT_FOUND")
    return None


@router.post("/token", response_model=schemas.Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(database.get_session),
):
    """Выдать JWT-токен."""
    user = await crud.get_user_by_email(session, form_data.username)
    if not user or not security.verify_password(
        form_data.password, user.hashed_password
    ):
        raise api_error(
            status.HTTP_401_UNAUTHORIZED,
            "Incorrect username or password",
            "INVALID_CREDENTIALS",
        )
    access_token = security.create_access_token({"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Вернуть текущего пользователя."""
    return current_user


@router.patch("/me", response_model=schemas.User)
async def update_user_me(
    data: schemas.UserUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(database.get_session),
):
    """Обновить профиль пользователя."""
    user = await crud.update_user(session, current_user, data)
    return user
