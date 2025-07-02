import uuid
from sqlalchemy import Column, String, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..database import Base


class PushSubscription(Base):
    __tablename__ = "push_subscriptions"
    __table_args__ = (UniqueConstraint("account_id", "endpoint"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    endpoint = Column(String, nullable=False)
    p256dh = Column(String, nullable=False)
    auth = Column(String, nullable=False)

    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    account = relationship("Account", back_populates="push_subscriptions")
    user = relationship("User", back_populates="push_subscriptions")
