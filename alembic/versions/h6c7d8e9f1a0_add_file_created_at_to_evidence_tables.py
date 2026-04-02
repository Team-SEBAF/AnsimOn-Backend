"""add file_created_at to evidence file tables

Revision ID: h6c7d8e9f1a0
Revises: 99dd649d0076
Create Date: 2026-04-02

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "h6c7d8e9f1a0"
down_revision: Union[str, Sequence[str], None] = "99dd649d0076"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES_WITH_ROW_CREATED_AT = (
    "evidence_messages",
    "evidence_victims",
    "evidence_voices",
    "evidence_report_records",
)


def upgrade() -> None:
    for table in _TABLES_WITH_ROW_CREATED_AT:
        op.add_column(
            table,
            sa.Column("file_created_at", sa.DateTime(timezone=True), nullable=True),
        )
    op.add_column(
        "evidence_incident_log_files",
        sa.Column("file_created_at", sa.DateTime(timezone=True), nullable=True),
    )

    for table in _TABLES_WITH_ROW_CREATED_AT:
        op.execute(
            sa.text(
                f"UPDATE {table} SET file_created_at = created_at " "WHERE file_created_at IS NULL"
            )
        )

    op.execute(
        sa.text(
            """
            UPDATE evidence_incident_log_files AS f
            SET file_created_at = l.created_at
            FROM evidence_incident_logs AS l
            WHERE f.incident_log_id = l.incident_log_id
              AND f.file_created_at IS NULL
            """
        )
    )

    for table in _TABLES_WITH_ROW_CREATED_AT + ("evidence_incident_log_files",):
        op.alter_column(table, "file_created_at", nullable=False)


def downgrade() -> None:
    for table in _TABLES_WITH_ROW_CREATED_AT + ("evidence_incident_log_files",):
        op.drop_column(table, "file_created_at")
