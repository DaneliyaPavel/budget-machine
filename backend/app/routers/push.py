from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud, schemas, database, models
from .users import get_current_user

router = APIRouter(prefix="/push", tags=["Уведомления"])


@router.get("/", response_model=list[schemas.PushSubscription])
async def read_subscriptions(
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    return await crud.get_push_subscriptions(session, current_user.account_id)


@router.post("/", response_model=schemas.PushSubscription)
async def add_subscription(
    sub: schemas.PushSubscriptionCreate,
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    return await crud.add_push_subscription(
        session, sub, current_user.account_id, current_user.id
    )


@router.delete("/{sub_id}", status_code=204)
async def remove_subscription(
    sub_id: int,
    session: AsyncSession = Depends(database.get_session),
    current_user: models.User = Depends(get_current_user),
):
    await crud.delete_push_subscription(session, sub_id, current_user.account_id)
    return None
