"""add created_at, updated_at to timelines

Revision ID: c3e4f5a6b7c8
Revises: 2dd6a24f6735
Create Date: 2026-04-25 23:18:00

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3e4f5a6b7c8"
down_revision: Union[str, Sequence[str], None] = "2dd6a24f6735"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "timelines",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column(
        "timelines",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("timelines", "updated_at")
    op.drop_column("timelines", "created_at")
