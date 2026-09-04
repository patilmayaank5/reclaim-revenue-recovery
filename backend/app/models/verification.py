"""Verification model.

Verification is a separate domain step.
HTTP 200 alone is NOT sufficient to declare money recovered.
Recovery must be verified through payment status/event mechanisms.
"""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, UniqueConstraint, Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin
from app.models.enums import VerificationStatus


class Verification(CreatedAtMixin, Base):
    """Represents outcome verification for a recovery action.

    recovered_amount_minor uses integer minor units.
    """

    __tablename__ = "verifications"
    __table_args__ = (
        UniqueConstraint("action_id", name="uq_verifications_action_id"),
    )

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
    payment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payments.id"),
        nullable=False,
    )
    status: Mapped[VerificationStatus] = mapped_column(
        SQLAlchemyEnum(VerificationStatus, native_enum=False, length=50, values_callable=lambda x: [e.value for e in x]),
        nullable=False, index=True,
    )
    observed_payment_status: Mapped[str | None] = mapped_column(
        String(50), nullable=True,
        comment="Observed payment status from provider",
    )
    recovered_amount_minor: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True,
        comment="Verified recovered amount in integer minor units",
    )
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    provider_event_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True,
        comment="Provider event/webhook reference",
    )
    provider_event_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    # Relationships
    action: Mapped["Action"] = relationship(back_populates="verifications")
    case: Mapped["Case"] = relationship(back_populates="verifications")

    def __repr__(self) -> str:
        return f"<Verification id={self.id} status={self.status}>"
