"""Ingestion event model for idempotency."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class IngestionEvent(Base):
    """Tracks processed provider events to ensure idempotency.

    event_id is the unique identifier of the event from the provider.
    """

    __tablename__ = "ingestion_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_id: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False,
        comment="Provider event identifier for idempotency",
    )
    payment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payments.id"),
        index=True,
        nullable=False,
    )
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )

    # Relationships
    payment: Mapped["Payment"] = relationship()
