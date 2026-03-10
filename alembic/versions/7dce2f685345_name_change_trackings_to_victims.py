"""name change trackings to victims

Revision ID: 7dce2f685345
Revises: f2ca0f295cbe
Create Date: 2026-03-08 18:24:29.418246

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7dce2f685345"
down_revision: Union[str, Sequence[str], None] = "f2ca0f295cbe"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema. rename_table + alter_column으로 데이터 유지."""
    op.rename_table("evidence_trackings", "evidence_victims")
    op.alter_column(
        "evidence_victims",
        "tracking_id",
        new_column_name="victim_id",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "evidence_victims",
        "victim_id",
        new_column_name="tracking_id",
    )
    op.rename_table("evidence_victims", "evidence_trackings")
