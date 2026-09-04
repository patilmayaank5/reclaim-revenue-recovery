"""Audit event model.

CRITICAL: Audit events are APPEND-ONLY and IMMUTABLE.
- No updated_at column.
- ORM-level update and delete operations are rejected via event listeners.
- Application code must NEVER update or delete audit records.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, event, func, Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import AuditEventType


class AuditEvent(Base):
    """Immutable audit trail record.

    WARNING: This model intentionally has NO updated_at column.
    Update and delete operations are blocked by ORM event listeners.
    """

    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_type: Mapped[AuditEventType] = mapped_column(
        SQLAlchemyEnum(AuditEventType, native_enum=False, length=50, values_callable=lambda x: [e.value for e in x]),
        nullable=False, index=True,
    )
    entity_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="Entity type: case, action, payment, etc.",
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True,
        comment="ID of the referenced entity",
    )
    actor: Mapped[str] = mapped_column(
        String(255), nullable=False,
        comment="Actor: system, policy_engine, user:john, etc.",
    )
    correlation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True,
        comment="Request/correlation identifier for tracing",
    )
    event_data: Mapped[dict] = mapped_column(
        JSONB, nullable=False,
        comment="Structured event payload",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Immutable creation timestamp",
    )

    def __repr__(self) -> str:
        return f"<AuditEvent id={self.id} type={self.event_type} entity={self.entity_type}:{self.entity_id}>"


# --- ORM-level immutability guards (WARNING-01 fix) ---

@event.listens_for(AuditEvent, "before_update")
def _audit_event_before_update(mapper, connection, target):
    """Prevent updates to audit event records."""
    raise RuntimeError(
        "AuditEvent records are immutable. Updates are not allowed. "
        "Create a new AuditEvent instead."
    )


@event.listens_for(AuditEvent, "before_delete")
def _audit_event_before_delete(mapper, connection, target):
    """Prevent deletion of audit event records."""
    raise RuntimeError(
        "AuditEvent records are immutable. Deletion is not allowed. "
        "Audit trail must be preserved."
    )
