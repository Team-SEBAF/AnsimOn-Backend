"""modify pk name

Revision ID: 66f4096f9ae9
Revises: 912e99eb69cb
Create Date: 2026-02-04 17:53:03.919825

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "66f4096f9ae9"
down_revision: Union[str, Sequence[str], None] = "912e99eb69cb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema. id 컬럼명을 message_id로 변경 (기존 데이터 유지)."""
    op.alter_column(
        "evidence_messages",
        "id",
        new_column_name="message_id",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "evidence_messages",
        "message_id",
        new_column_name="id",
    )
