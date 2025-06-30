"""Описание моделей базы данных."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, Boolean
from sqlalchemy.orm import relationship

from .database import Base


class Account(Base):
    """Общий счёт для нескольких пользователей."""

    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    users = relationship("User", back_populates="account")
    categories = relationship("Category", back_populates="account")
    transactions = relationship("Transaction", back_populates="account")
    goals = relationship("Goal", back_populates="account")
    recurring_payments = relationship(
        "RecurringPayment", back_populates="account"
    )


class User(Base):
    """Пользователь системы."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="owner")

    account_id = Column(Integer, ForeignKey("accounts.id"))
    account = relationship("Account", back_populates="users")

    categories = relationship("Category", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")
    goals = relationship("Goal", back_populates="user")
    recurring_payments = relationship(
        "RecurringPayment", back_populates="user"
    )


class Category(Base):
    """Категория доходов или расходов."""

    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    monthly_limit = Column(Numeric(10, 2), nullable=True)

    account_id = Column(Integer, ForeignKey("accounts.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    account = relationship("Account", back_populates="categories")
    user = relationship("User", back_populates="categories")
    transactions = relationship("Transaction", back_populates="category")
    recurring_payments = relationship(
        "RecurringPayment", back_populates="category"
    )


class Transaction(Base):
    """Финансовая операция."""

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="RUB")
    amount_rub = Column(Numeric(10, 2), nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    category_id = Column(Integer, ForeignKey("categories.id"))
    account_id = Column(Integer, ForeignKey("accounts.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    category = relationship("Category", back_populates="transactions")
    account = relationship("Account", back_populates="transactions")
    user = relationship("User", back_populates="transactions")


class Goal(Base):
    """Цель накоплений."""

    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    target_amount = Column(Numeric(10, 2), nullable=False)
    current_amount = Column(Numeric(10, 2), default=0)
    due_date = Column(DateTime, nullable=True)

    account_id = Column(Integer, ForeignKey("accounts.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    account = relationship("Account", back_populates="goals")
    user = relationship("User", back_populates="goals")


class RecurringPayment(Base):
    """Регулярный ежемесячный платеж."""

    __tablename__ = "recurring_payments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="RUB")
    day = Column(Integer, nullable=False)
    description = Column(String, nullable=True)

    category_id = Column(Integer, ForeignKey("categories.id"))
    account_id = Column(Integer, ForeignKey("accounts.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    active = Column(Boolean, default=True)

    category = relationship("Category", back_populates="recurring_payments")
    account = relationship("Account", back_populates="recurring_payments")
    user = relationship("User", back_populates="recurring_payments")
