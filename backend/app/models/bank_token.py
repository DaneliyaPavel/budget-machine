import uuid
from sqlalchemy import Column, String, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..database import Base


class BankToken(Base):
    __tablename__ = "bank_tokens"
    __table_args__ = (UniqueConstraint("account_id", "bank"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bank = Column(String, nullable=False)
    token = Column(String, nullable=False)

    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    account = relationship("Account", back_populates="tokens")
    user = relationship("User", back_populates="tokens")
