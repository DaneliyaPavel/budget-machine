import uuid
from enum import Enum as PyEnum
from sqlalchemy import Column, String, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates

from ..database import Base


class AccountType(PyEnum):
    cash = "cash"
    bank = "bank"
    card = "card"
    crypto = "crypto"


class Account(Base):
    """User account."""

    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    currency_code = Column(String(3), ForeignKey("currencies.code"), nullable=False)
    type = Column(SAEnum(AccountType), default=AccountType.cash)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    owner = relationship("User", foreign_keys=[user_id])
    users = relationship(
        "User", back_populates="account", foreign_keys="User.account_id"
    )
    categories = relationship("Category", back_populates="account")
    goals = relationship("Goal", back_populates="account")
    recurring_payments = relationship("RecurringPayment", back_populates="account")
    tokens = relationship("BankToken", back_populates="account")
    push_subscriptions = relationship("PushSubscription", back_populates="account")

    @validates("currency_code")
    def _lock_currency(self, key, value):
        if getattr(self, key) is not None:
            raise ValueError("currency_code is immutable")
        return value
