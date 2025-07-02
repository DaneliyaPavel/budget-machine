import uuid
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..database import Base


class Goal(Base):
    __tablename__ = "goals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    target_amount = Column(Numeric(20, 6), nullable=False)
    current_amount = Column(Numeric(20, 6), default=0)
    due_date = Column(DateTime, nullable=True)

    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    account = relationship("Account", back_populates="goals")
    user = relationship("User", back_populates="goals")
