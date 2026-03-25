"""add_cachings_table

Revision ID: 7618089fe8d1
Revises: g5b6c7d8e9f0
Create Date: 2026-03-24 00:54:17.239192

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7618089fe8d1"
down_revision: Union[str, Sequence[str], None] = "g5b6c7d8e9f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "cachings",
        sa.Column("hash_key", sa.String(64), primary_key=True),
        sa.Column("s3_key", sa.String(512), nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("cachings")
