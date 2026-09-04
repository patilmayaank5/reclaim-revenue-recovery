"""Approval model for human-in-the-loop decisions."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin
from app.models.enums import ApprovalStatus


class Approval(CreatedAtMixin, Base):
    """Represents a human approval decision for an action."""

    __tablename__ = "approvals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    action_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("actions.id"),
        index=True,
        nullable=False,
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id"),
        index=True,
        nullable=False,
    )
    status: Mapped[ApprovalStatus] = mapped_column(
        SQLAlchemyEnum(ApprovalStatus, native_enum=False, length=50, values_callable=lambda x: [e.value for e in x]),
        nullable=False, index=True,
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    approver_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True,
        comment="Approver reference (user ID or system identifier)",
    )
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    action: Mapped["Action"] = relationship(back_populates="approvals")
    case: Mapped["Case"] = relationship(back_populates="approvals")

    def __repr__(self) -> str:
        return f"<Approval id={self.id} status={self.status}>"
