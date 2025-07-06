"""add indexes

Revision ID: 7c6d5e37daf0
Revises: dda846dd5702
Create Date: 2025-07-06 01:38:06.290687

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "7c6d5e37daf0"
down_revision: Union[str, Sequence[str], None] = "dda846dd5702"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index("accounts_user_id_idx", "accounts", ["user_id"])
    op.create_index("categories_user_id_idx", "categories", ["user_id"])
    op.create_index(
        "transactions_user_posted_idx",
        "transactions",
        ["user_id", "posted_at"],
    )
    op.create_index("postings_txn_id_idx", "postings", ["transaction_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("postings_txn_id_idx", table_name="postings")
    op.drop_index("transactions_user_posted_idx", table_name="transactions")
    op.drop_index("categories_user_id_idx", table_name="categories")
    op.drop_index("accounts_user_id_idx", table_name="accounts")
