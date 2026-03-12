"""rename timeline_manual_evidences to timeline_referenced_manual_evidences

Revision ID: a1b2c3d4e5f6
Revises: 6f57a2aeb16d
Create Date: 2026-03-12

"""
from typing import Sequence, Union

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "6f57a2aeb16d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table(
        "timeline_manual_evidences",
        "timeline_referenced_manual_evidences",
    )


def downgrade() -> None:
    op.rename_table(
        "timeline_referenced_manual_evidences",
        "timeline_manual_evidences",
    )
