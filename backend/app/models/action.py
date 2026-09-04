"""Action model.

CRITICAL: idempotency_key has a real database-level UNIQUE constraint.
Application-level checks alone are NOT sufficient.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import ActionStatus


class Action(TimestampMixin, Base):
    """Represents an attempted or planned intervention action.

    idempotency_key is enforced as UNIQUE at the database level.
    This is a frozen architecture requirement.
    """

    __tablename__ = "actions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id"),
        index=True,
        nullable=False,
    )
    intervention_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interventions.id"),
        nullable=False,
    )
    status: Mapped[ActionStatus] = mapped_column(
        SQLAlchemyEnum(ActionStatus, native_enum=False, length=50, values_callable=lambda x: [e.value for e in x]),
        nullable=False, index=True,
    )
    provider: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="Execution provider: razorpay, simulator, demo",
    )
    idempotency_key: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False,
        comment="UNIQUE at database level — frozen architecture requirement",
    )
    execution_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    executed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    # Relationships
    case: Mapped["Case"] = relationship(back_populates="actions")
    intervention: Mapped["Intervention"] = relationship(back_populates="actions")
    approvals: Mapped[list["Approval"]] = relationship(back_populates="action")
    verifications: Mapped[list["Verification"]] = relationship(back_populates="action")

    def __repr__(self) -> str:
        return f"<Action id={self.id} status={self.status} key={self.idempotency_key!r}>"
