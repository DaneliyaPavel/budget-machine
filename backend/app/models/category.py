import uuid
from sqlalchemy import Column, String, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True, nullable=False)
    monthly_limit = Column(Numeric(20, 6), nullable=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)

    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    account = relationship("Account", back_populates="categories")
    user = relationship("User", back_populates="categories")
    transactions = relationship("Transaction", back_populates="category")
    recurring_payments = relationship("RecurringPayment", back_populates="category")
    parent = relationship("Category", remote_side=[id], back_populates="children")
    children = relationship("Category", back_populates="parent")
