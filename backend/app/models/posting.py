import uuid
from enum import Enum as PyEnum
from sqlalchemy import Column, Numeric, String, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..database import Base


class PostingSide(PyEnum):
    debit = "debit"
    credit = "credit"


class Posting(Base):
    __tablename__ = "postings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    amount = Column(Numeric(20, 6), nullable=False)
    side = Column(SAEnum(PostingSide), nullable=False)
    currency_code = Column(String(3), ForeignKey("currencies.code"), nullable=False)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"))
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"))

    transaction = relationship("Transaction", back_populates="postings")
    account = relationship("Account")
