from uuid import UUID
from pydantic import BaseModel, ConfigDict

STRICT = ConfigDict(strict=True)
ORM_STRICT = ConfigDict(from_attributes=True, strict=True)


class PushSubscriptionBase(BaseModel):
    endpoint: str
    p256dh: str
    auth: str

    model_config = STRICT


class PushSubscriptionCreate(PushSubscriptionBase):
    pass


class PushSubscription(PushSubscriptionBase):
    id: UUID

    model_config = ORM_STRICT
