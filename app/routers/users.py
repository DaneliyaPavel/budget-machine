"""Маршруты аутентификации пользователей."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from .. import crud, schemas, database, models, security
from ..security import verify_password, create_access_token
from jose import JWTError, jwt

router = APIRouter(prefix="/пользователи", tags=["Пользователи"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/пользователи/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(database.get_session),
) -> models.User:
    """Получить текущего пользователя по JWT-токену."""
    try:
        payload = jwt.decode(
            token, security.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        email: str = payload.get("sub")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный токен"
        )
    user = await crud.get_user_by_email(session, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден"
        )
    return user


@router.post("/", response_model=schemas.User)
async def create_user(
    user: schemas.UserCreate, session: AsyncSession = Depends(database.get_session)
):
    """Регистрация нового пользователя."""
    db_user = await crud.get_user_by_email(session, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await crud.create_user(session, user)


@router.post("/join", response_model=schemas.User)
async def join_account(
    data: schemas.JoinAccount,
    current_user: models.User = Depends(get_current_user),
    session: AsyncSession = Depends(database.get_session),
):
    """Присоединиться к существующему счёту."""
    user = await crud.join_account(session, current_user, data.account_id)
    if not user:
        raise HTTPException(status_code=404, detail="Счёт не найден")
    return user


@router.get("/участники", response_model=list[schemas.User])
async def account_members(
    current_user: models.User = Depends(get_current_user),
    session: AsyncSession = Depends(database.get_session),
):
    """Список участников текущего счёта."""
    return await crud.get_account_users(session, current_user.account_id)


@router.delete("/{user_id}", status_code=204)
async def remove_user(
    user_id: int,
    current_user: models.User = Depends(get_current_user),
    session: AsyncSession = Depends(database.get_session),
):
    """Удалить пользователя из счёта (только владелец)."""
    if current_user.role != "owner" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    ok = await crud.delete_user(session, user_id, current_user.account_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return None


@router.post("/token", response_model=schemas.Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(database.get_session),
):
    """Получение JWT-токена."""
    user = await crud.get_user_by_email(session, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token = create_access_token({"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    """Получить данные текущего пользователя."""
    return current_user


@router.patch("/me", response_model=schemas.User)
async def update_user_me(
    data: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_user),
    session: AsyncSession = Depends(database.get_session),
):
    """Обновить профиль пользователя."""
    user = await crud.update_user(session, current_user, data)
    return user
