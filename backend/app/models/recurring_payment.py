import uuid
from sqlalchemy import Column, String, Numeric, Integer, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..database import Base


class RecurringPayment(Base):
    __tablename__ = "recurring_payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    amount = Column(Numeric(20, 6), nullable=False)
    currency = Column(String, default="RUB")
    day = Column(Integer, nullable=False)
    description = Column(String, nullable=True)

    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"))
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    active = Column(Boolean, default=True)

    category = relationship("Category", back_populates="recurring_payments")
    account = relationship("Account", back_populates="recurring_payments")
    user = relationship("User", back_populates="recurring_payments")
