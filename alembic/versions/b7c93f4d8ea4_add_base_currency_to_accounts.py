"""add base currency to accounts

Revision ID: b7c93f4d8ea4
Revises: c3cf30754da7
Create Date: 2025-06-30 13:00:00

"""

from typing import Sequence, Union

from alembic import op  # type: ignore[attr-defined]
import sqlalchemy as sa

revision: str = "b7c93f4d8ea4"
down_revision: Union[str, Sequence[str], None] = "c3cf30754da7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "accounts",
        sa.Column("base_currency", sa.String(), nullable=False, server_default="RUB"),
    )


def downgrade() -> None:
    op.drop_column("accounts", "base_currency")
