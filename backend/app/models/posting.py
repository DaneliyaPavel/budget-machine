# backend/app/models/posting.py

import uuid
from sqlalchemy import (
    Column,
    ForeignKey,
    ForeignKeyConstraint,
    Numeric,
    Enum,
    String,
    DateTime,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from ..database import Base
import enum


class PostingSide(enum.Enum):
    debit = "debit"
    credit = "credit"


class Posting(Base):
    __tablename__ = "postings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    amount = Column(Numeric(precision=20, scale=6), nullable=False)
    side = Column(Enum(PostingSide, name="postingside"), nullable=False)

    currency_code = Column(String(3), ForeignKey("currencies.code"), nullable=False)

    # Ссылка на Transaction (composite FK)
    transaction_id = Column(UUID(as_uuid=True), nullable=False)
    transaction_posted_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["transaction_id", "transaction_posted_at"],
            ["transactions.id", "transactions.posted_at"],
            name="postings_transaction_fk",
            ondelete="CASCADE",
        ),
    )

    transaction = relationship("Transaction", back_populates="postings")
