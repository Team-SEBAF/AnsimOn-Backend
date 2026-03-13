"""add_timeline_regeneration_flags

Revision ID: a1fa62cd79ae
Revises: 41bdeb05fe47
Create Date: 2026-03-13 19:49:17.231087

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1fa62cd79ae"
down_revision: Union[str, Sequence[str], None] = "41bdeb05fe47"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "timelines",
        sa.Column(
            "need_evidence_collection_regeneration",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
            comment="대조 증거 모음 재생성 필요 여부",
        ),
    )
    op.add_column(
        "timelines",
        sa.Column(
            "need_timeline_pdf_regeneration",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
            comment="타임라인 PDF 재생성 필요 여부",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("timelines", "need_timeline_pdf_regeneration")
    op.drop_column("timelines", "need_evidence_collection_regeneration")
