import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    posted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    payee = Column(String, nullable=True)
    note = Column(String, nullable=True)
    external_id = Column(String, nullable=True)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    user = relationship("User", back_populates="transactions")
    postings = relationship("Posting", back_populates="transaction")
