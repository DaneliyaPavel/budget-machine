"""Refactor transactions table"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "84d4d5b5f9e2"
down_revision: Union[str, Sequence[str], None] = "3999786d4d84"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("transactions") as batch:
        batch.drop_column("amount")
        batch.drop_column("currency")
        batch.drop_column("amount_rub")
        batch.drop_column("description")
        batch.drop_column("created_at")
        batch.drop_column("account_id")
        batch.add_column(
            sa.Column(
                "posted_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            )
        )
        batch.add_column(sa.Column("payee", sa.String(), nullable=True))
        batch.add_column(sa.Column("note", sa.String(), nullable=True))
        batch.add_column(sa.Column("external_id", sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("transactions") as batch:
        batch.drop_column("external_id")
        batch.drop_column("note")
        batch.drop_column("payee")
        batch.drop_column("posted_at")
        batch.add_column(
            sa.Column("account_id", sa.dialects.postgresql.UUID(as_uuid=True))
        )
        batch.add_column(
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            )
        )
        batch.add_column(sa.Column("description", sa.String(), nullable=True))
        batch.add_column(sa.Column("amount_rub", sa.Numeric(20, 6), nullable=False))
        batch.add_column(sa.Column("currency", sa.String(), nullable=True))
        batch.add_column(sa.Column("amount", sa.Numeric(20, 6), nullable=False))
