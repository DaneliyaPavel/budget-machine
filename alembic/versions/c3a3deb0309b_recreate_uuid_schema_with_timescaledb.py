"""Recreate schema using UUID keys and enable TimescaleDB."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import MetaData, Table, inspect
from sqlalchemy.schema import DropTable

# revision identifiers, used by Alembic.
revision: str = "c3a3deb0309b"
down_revision: Union[str, Sequence[str], None] = "0d74380f2dbb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")

    # drop old tables if they exist
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = [
        "push_subscriptions",
        "bank_tokens",
        "recurring_payments",
        "goals",
        "postings",
        "transactions",
        "categories",
        "accounts",
        "currencies",
        "users",
    ]
    for tbl in tables:
        if inspector.has_table(tbl):
            op.execute(DropTable(Table(tbl, MetaData()), if_exists=True))

    # create base tables
    op.create_table(
        "currencies",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(3), nullable=False, unique=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("symbol", sa.String(), nullable=False),
        sa.Column("precision", sa.Integer(), server_default="2"),
    )

    op.create_table(
        "accounts",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("currency_code", sa.String(3), nullable=False),
        sa.Column("type", sa.String(), nullable=False, server_default="cash"),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("base_currency", sa.String(), nullable=False, server_default="RUB"),
        sa.ForeignKeyConstraint(["currency_code"], ["currencies.code"]),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(), nullable=False, unique=True, index=True),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("role", sa.String(), server_default="owner"),
        sa.Column(
            "account_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True
        ),
    )

    # add fk relations now that both tables exist
    op.create_foreign_key(None, "accounts", "users", ["user_id"], ["id"])
    op.create_foreign_key(None, "users", "accounts", ["account_id"], ["id"])

    op.create_table(
        "categories",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, index=True),
        sa.Column("monthly_limit", sa.Numeric(20, 6)),
        sa.Column("parent_id", sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.Column("account_id", sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.ForeignKeyConstraint(["parent_id"], ["categories.id"]),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )

    op.create_table(
        "transactions",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("amount", sa.Numeric(20, 6), nullable=False),
        sa.Column("currency", sa.String(), server_default="RUB"),
        sa.Column("amount_rub", sa.Numeric(20, 6), nullable=False),
        sa.Column("description", sa.String()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("category_id", sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.Column("account_id", sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )

    op.create_table(
        "postings",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("amount", sa.Numeric(20, 6), nullable=False),
        sa.Column("side", sa.String(), nullable=False),
        sa.Column("transaction_id", sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.Column("account_id", sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"]),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"]),
    )

    op.create_table(
        "goals",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("target_amount", sa.Numeric(20, 6), nullable=False),
        sa.Column("current_amount", sa.Numeric(20, 6), server_default="0"),
        sa.Column("due_date", sa.DateTime()),
        sa.Column("account_id", sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )

    op.create_table(
        "recurring_payments",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("amount", sa.Numeric(20, 6), nullable=False),
        sa.Column("currency", sa.String(), server_default="RUB"),
        sa.Column("day", sa.Integer(), nullable=False),
        sa.Column("description", sa.String()),
        sa.Column("category_id", sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.Column("account_id", sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true")),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )

    op.create_table(
        "bank_tokens",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("bank", sa.String(), nullable=False),
        sa.Column("token", sa.String(), nullable=False),
        sa.Column("account_id", sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.UniqueConstraint("account_id", "bank"),
    )

    op.create_table(
        "push_subscriptions",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("endpoint", sa.String(), nullable=False),
        sa.Column("p256dh", sa.String(), nullable=False),
        sa.Column("auth", sa.String(), nullable=False),
        sa.Column("account_id", sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.UniqueConstraint("account_id", "endpoint"),
    )

    # convert transactions to hypertable
    op.execute(
        "SELECT create_hypertable('transactions', 'created_at', if_not_exists => TRUE)"
    )

    # trigger to check postings balance
    op.execute(
        """
        CREATE OR REPLACE FUNCTION check_postings_balance()
        RETURNS TRIGGER AS $$
        DECLARE
            txid uuid;
            deb NUMERIC;
            cred NUMERIC;
        BEGIN
            IF TG_OP = 'DELETE' THEN
                txid := OLD.transaction_id;
            ELSE
                txid := NEW.transaction_id;
            END IF;
            SELECT COALESCE(SUM(amount) FILTER (WHERE side='debit'), 0),
                   COALESCE(SUM(amount) FILTER (WHERE side='credit'), 0)
            INTO deb, cred
            FROM postings WHERE transaction_id = txid;
            IF deb <> cred THEN
                RAISE EXCEPTION 'Debit and credit totals do not match for transaction %', txid;
            END IF;
            IF TG_OP = 'DELETE' THEN
                RETURN OLD;
            ELSE
                RETURN NEW;
            END IF;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE CONSTRAINT TRIGGER postings_balance_check
        AFTER INSERT OR UPDATE OR DELETE ON postings
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW EXECUTE FUNCTION check_postings_balance()
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = [
        "push_subscriptions",
        "bank_tokens",
        "recurring_payments",
        "goals",
        "postings",
        "transactions",
        "categories",
        "users",
        "accounts",
        "currencies",
    ]
    for tbl in tables:
        if inspector.has_table(tbl):
            op.execute(DropTable(Table(tbl, MetaData()), if_exists=True))
    op.execute("DROP FUNCTION IF EXISTS check_postings_balance")
    op.execute("DROP EXTENSION IF EXISTS timescaledb")
