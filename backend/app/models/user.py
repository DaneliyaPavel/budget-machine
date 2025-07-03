import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..database import Base


class UserRole(PyEnum):
    owner = "owner"
    member = "member"
    readonly = "readonly"


class User(Base):
    """User of the system."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)
    role = Column(SAEnum(UserRole), default=UserRole.owner)

    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    account = relationship("Account", back_populates="users", foreign_keys=[account_id])
    accounts_owned = relationship("Account", foreign_keys="Account.user_id")

    categories = relationship("Category", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")
    goals = relationship("Goal", back_populates="user")
    recurring_payments = relationship("RecurringPayment", back_populates="user")
    tokens = relationship("BankToken", back_populates="user")
    push_subscriptions = relationship("PushSubscription", back_populates="user")
