"""initial schema timescale

Revision ID: b103c71929de
Revises     :
Create Date : 2025‑07‑18 08:28:23.275287
"""

from alembic import op
import sqlalchemy as sa
from typing import Sequence, Union


# ─────────────────── метки Alembic ───────────────────
revision: str = "b103c71929de"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
# ──────────────────────────────────────────────────────


# =====================================================
# ↑↑  Upgrade  ↑↑
# =====================================================
def upgrade() -> None:
    """Создать начальную схему + Timescale‑гипертаблицу."""
    bind = op.get_bind()

    # ---------- базовые таблицы без циклов ----------
    op.create_table(
        "currencies",
        sa.Column("code", sa.String(3), primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("symbol", sa.String, nullable=False),
        sa.Column("precision", sa.Integer),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.UUID, primary_key=True),
        sa.Column("email", sa.String, nullable=False),
        sa.Column("hashed_password", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime),
        sa.Column("is_active", sa.Boolean),
        sa.Column(
            "role",
            sa.Enum("owner", "member", "readonly", name="userrole"),
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ---------- accounts (FK → users, currencies) ----------
    op.create_table(
        "accounts",
        sa.Column("id", sa.UUID, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("currency_code", sa.String(3), sa.ForeignKey("currencies.code")),
        sa.Column(
            "type",
            sa.Enum("cash", "bank", "card", "crypto", name="accounttype"),
        ),
        sa.Column("user_id", sa.UUID, sa.ForeignKey("users.id")),
    )
    op.create_index("accounts_user_id_idx", "accounts", ["user_id"])

    # ---------- остальные таблицы ----------
    op.create_table(
        "bank_tokens",
        sa.Column("id", sa.UUID, primary_key=True),
        sa.Column("bank", sa.String, nullable=False),
        sa.Column("token", sa.String, nullable=False),
        sa.Column("account_id", sa.UUID, sa.ForeignKey("accounts.id")),
        sa.Column("user_id", sa.UUID, sa.ForeignKey("users.id")),
        sa.UniqueConstraint("account_id", "bank"),
    )

    op.create_table(
        "categories",
        sa.Column("id", sa.UUID, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("monthly_limit", sa.Numeric(20, 6)),
        sa.Column("icon", sa.String),
        sa.Column("parent_id", sa.UUID),
        sa.Column("account_id", sa.UUID, sa.ForeignKey("accounts.id")),
        sa.Column("user_id", sa.UUID, sa.ForeignKey("users.id")),
        sa.ForeignKeyConstraint(["parent_id"], ["categories.id"]),
    )
    op.create_index("ix_categories_name", "categories", ["name"])
    op.create_index("categories_user_id_idx", "categories", ["user_id"])

    op.create_table(
        "goals",
        sa.Column("id", sa.UUID, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("target_amount", sa.Numeric(20, 6), nullable=False),
        sa.Column("current_amount", sa.Numeric(20, 6)),
        sa.Column("due_date", sa.DateTime),
        sa.Column("account_id", sa.UUID, sa.ForeignKey("accounts.id")),
        sa.Column("user_id", sa.UUID, sa.ForeignKey("users.id")),
    )

    op.create_table(
        "push_subscriptions",
        sa.Column("id", sa.UUID, primary_key=True),
        sa.Column("endpoint", sa.String, nullable=False),
        sa.Column("p256dh", sa.String, nullable=False),
        sa.Column("auth", sa.String, nullable=False),
        sa.Column("account_id", sa.UUID, sa.ForeignKey("accounts.id")),
        sa.Column("user_id", sa.UUID, sa.ForeignKey("users.id")),
        sa.UniqueConstraint("account_id", "endpoint"),
    )

    op.create_table(
        "recurring_payments",
        sa.Column("id", sa.UUID, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("amount", sa.Numeric(20, 6), nullable=False),
        sa.Column("currency", sa.String(3)),
        sa.Column("day", sa.Integer, nullable=False),
        sa.Column("description", sa.String),
        sa.Column("category_id", sa.UUID, sa.ForeignKey("categories.id")),
        sa.Column("account_id", sa.UUID, sa.ForeignKey("accounts.id")),
        sa.Column("user_id", sa.UUID, sa.ForeignKey("users.id")),
        sa.Column("active", sa.Boolean),
    )

    # ---------- transactions (PK = id + posted_at) ----------
    op.create_table(
        "transactions",
        sa.Column("id", sa.UUID, primary_key=True),
        sa.Column(
            "posted_at",
            sa.DateTime(timezone=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("user_id", sa.UUID, sa.ForeignKey("users.id")),
        sa.Column("category_id", sa.UUID, sa.ForeignKey("categories.id")),
        sa.Column("payee", sa.String),
        sa.Column("note", sa.String),
        sa.Column("external_id", sa.String),
    )
    op.create_index(
        "transactions_user_posted_idx",
        "transactions",
        ["user_id", "posted_at"],
    )

    # ---------- postings (композитный FK) ----------
    op.create_table(
        "postings",
        sa.Column("id", sa.UUID, primary_key=True),
        sa.Column("amount", sa.Numeric(20, 6), nullable=False),
        sa.Column(
            "side",
            sa.Enum("debit", "credit", name="postingside"),
            nullable=False,
        ),
        sa.Column("currency_code", sa.String(3), sa.ForeignKey("currencies.code")),
        sa.Column("transaction_id", sa.UUID, nullable=False),
        sa.Column("transaction_posted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("account_id", sa.UUID, sa.ForeignKey("accounts.id")),
        sa.ForeignKeyConstraint(
            ["transaction_id", "transaction_posted_at"],
            ["transactions.id", "transactions.posted_at"],
            name="postings_transaction_fk",
            ondelete="CASCADE",
        ),
    )
    op.create_index("postings_txn_id_idx", "postings", ["transaction_id"])

    # ---------- Timescale включение ----------
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")
        op.execute(
            """
            SELECT create_hypertable(
                'transactions',
                'posted_at',
                if_not_exists         => TRUE,
                create_default_indexes => TRUE
            );
            """
        )


# =====================================================
# ↓↓  Downgrade  ↓↓
# =====================================================
def downgrade() -> None:
    """Откат схемы."""
    op.drop_table("postings")
    op.drop_table("transactions")
    op.drop_table("recurring_payments")
    op.drop_table("push_subscriptions")
    op.drop_table("goals")
    op.drop_index("ix_categories_name", table_name="categories")
    op.drop_index("categories_user_id_idx", table_name="categories")
    op.drop_table("categories")
    op.drop_table("bank_tokens")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.drop_table("currencies")
    op.drop_table("accounts")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP EXTENSION IF EXISTS timescaledb")
