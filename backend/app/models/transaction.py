import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    amount = Column(Numeric(20, 6), nullable=False)
    currency = Column(String, default="RUB")
    amount_rub = Column(Numeric(20, 6), nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"))
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    category = relationship("Category", back_populates="transactions")
    account = relationship("Account", back_populates="transactions")
    user = relationship("User", back_populates="transactions")
    postings = relationship("Posting", back_populates="transaction")
