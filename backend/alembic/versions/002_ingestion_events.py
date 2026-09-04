"""Ingestion events table

Revision ID: 002
Revises: 001
Create Date: 2026-09-03

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ingestion_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_id", sa.String(255), nullable=False, unique=True),
        sa.Column("payment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("payments.id"), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_ingestion_events_event_id", "ingestion_events", ["event_id"])
    op.create_index("ix_ingestion_events_payment_id", "ingestion_events", ["payment_id"])


def downgrade() -> None:
    op.drop_index("ix_ingestion_events_payment_id", table_name="ingestion_events")
    op.drop_index("ix_ingestion_events_event_id", table_name="ingestion_events")
    op.drop_table("ingestion_events")
