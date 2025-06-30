"""migrate to timescaledb

Revision ID: 0d74380f2dbb
Revises: ef92c9828b2b
Create Date: 2025-07-01 00:00:00
"""

from typing import Sequence, Union

from alembic import op  # type: ignore[attr-defined]

revision: str = "0d74380f2dbb"
down_revision: Union[str, Sequence[str], None] = "ef92c9828b2b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")
    op.execute(
        "SELECT create_hypertable('transactions', 'created_at', if_not_exists => TRUE)"
    )


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS timescaledb")
