# backend/app/models/transaction.py

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    # ── составной PK: ставим primary_key=True и на id, и на posted_at ──
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # posted_at участвует в PK → обязательно primary_key=True и nullable=False
    # Используем server_default=func.now() чтобы БД сама ставила значение,
    # + default для Python на случай создания в памяти.
    posted_at = Column(
        DateTime(timezone=True),
        primary_key=True,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)

    payee = Column(String, nullable=True)
    note = Column(String, nullable=True)
    external_id = Column(String, nullable=True)

    # ── relationships ──
    user = relationship("User", back_populates="transactions")
    category = relationship("Category")

    # postings будет ссылаться на composite FK (transaction_id, transaction_posted_at)
    postings = relationship(
        "Posting",
        back_populates="transaction",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
