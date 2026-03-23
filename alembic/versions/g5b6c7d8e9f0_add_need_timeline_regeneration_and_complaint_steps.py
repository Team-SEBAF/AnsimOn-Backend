"""add need_timeline_regeneration and complaint steps

Revision ID: g5b6c7d8e9f0
Revises: f4a5b6c7d8e9
Create Date: 2026-03-19

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "g5b6c7d8e9f0"
down_revision: Union[str, Sequence[str], None] = "f4a5b6c7d8e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # need_timeline_regeneration: need_evidence_collection_regeneration 앞에 추가
    op.add_column(
        "timelines",
        sa.Column(
            "need_timeline_regeneration",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
            comment="타임라인 JSON 재생성 필요 여부",
        ),
    )
    # complaints.step 컬럼에 TIMELINE_GENERATING, DOCUMENT_GENERATING 값 허용 (varchar 20자)
    op.alter_column(
        "complaints",
        "step",
        type_=sa.String(25),
        existing_type=sa.String(20),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "complaints",
        "step",
        type_=sa.String(20),
        existing_type=sa.String(25),
    )
    op.drop_column("timelines", "need_timeline_regeneration")
