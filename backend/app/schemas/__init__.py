"""Pydantic-схемы для API."""

from .account import AccountBase, AccountCreate, AccountUpdate, Account

from .category import CategoryBase, CategoryCreate, CategoryUpdate, Category
from .transaction import (
    TransactionBase,
    TransactionCreate,
    TransactionUpdate,
    Transaction,
)
from .posting import PostingBase, PostingCreate, Posting
from .goal import GoalBase, GoalCreate, GoalUpdate, GoalDeposit, Goal
from .recurring_payment import (
    RecurringPaymentBase,
    RecurringPaymentCreate,
    RecurringPaymentUpdate,
    RecurringPayment,
)
from .bank_token import BankTokenBase, BankTokenCreate, BankToken
from .user import (
    UserBase,
    UserCreate,
    UserUpdate,
    JoinAccount,
    User,
    Token,
    TokenPair,
    TokenPayload,
    LoginRequest,
    RefreshRequest,
)
from .push_subscription import (
    PushSubscriptionBase,
    PushSubscriptionCreate,
    PushSubscription,
)
from .analytics import (
    CategorySummary,
    LimitExceed,
    ForecastItem,
    DailySummary,
    MonthlySummary,
    GoalProgress,
)

__all__ = [
    "AccountBase",
    "AccountCreate",
    "AccountUpdate",
    "Account",
    "CategoryBase",
    "CategoryCreate",
    "CategoryUpdate",
    "Category",
    "TransactionBase",
    "TransactionCreate",
    "TransactionUpdate",
    "Transaction",
    "PostingBase",
    "PostingCreate",
    "Posting",
    "GoalBase",
    "GoalCreate",
    "GoalUpdate",
    "GoalDeposit",
    "Goal",
    "RecurringPaymentBase",
    "RecurringPaymentCreate",
    "RecurringPaymentUpdate",
    "RecurringPayment",
    "BankTokenBase",
    "BankTokenCreate",
    "BankToken",
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "JoinAccount",
    "User",
    "Token",
    "TokenPair",
    "TokenPayload",
    "LoginRequest",
    "RefreshRequest",
    "PushSubscriptionBase",
    "PushSubscriptionCreate",
    "PushSubscription",
    "CategorySummary",
    "LimitExceed",
    "ForecastItem",
    "DailySummary",
    "MonthlySummary",
    "GoalProgress",
]
