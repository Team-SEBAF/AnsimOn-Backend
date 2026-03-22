"""add processed_evidence_count, total_evidence_count to task

Revision ID: e3f4a5b6c7d8
Revises: bc2bdec77496
Create Date: 2026-03-19

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e3f4a5b6c7d8"
down_revision: Union[str, Sequence[str], None] = "bc2bdec77496"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "tasks",
        sa.Column("processed_evidence_count", sa.Integer(), nullable=True, comment="처리된 증거수"),
    )
    op.add_column(
        "tasks",
        sa.Column("total_evidence_count", sa.Integer(), nullable=True, comment="총 증거수"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("tasks", "total_evidence_count")
    op.drop_column("tasks", "processed_evidence_count")
