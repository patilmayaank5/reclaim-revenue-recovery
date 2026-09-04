"""Revenue-at-risk case model."""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import AssignmentGroup, CaseStatus


class Case(TimestampMixin, Base):
    """Represents a detected revenue-at-risk case.

    amount_at_risk_minor is stored as integer minor units.
    assignment_group is set deterministically BEFORE AI processing.
    """

    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id"),
        index=True,
        nullable=False,
    )
    payment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payments.id"),
        index=True,
        nullable=False,
    )
    status: Mapped[CaseStatus] = mapped_column(
        SQLAlchemyEnum(CaseStatus, native_enum=False, length=50, values_callable=lambda x: [e.value for e in x]),
        nullable=False, index=True,
    )
    amount_at_risk_minor: Mapped[int] = mapped_column(
        BigInteger, nullable=False,
        comment="Amount at risk in integer minor units",
    )
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, comment="ISO 4217 currency code",
    )
    failure_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    assignment_group: Mapped[AssignmentGroup| None] = mapped_column(
        SQLAlchemyEnum(AssignmentGroup, native_enum=False, length=50, values_callable=lambda x: [e.value for e in x]),
        nullable=True, index=True,
        comment="Treatment/holdout — set deterministically before AI processing",
    )
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    # Relationships
    merchant: Mapped["Merchant"] = relationship(back_populates="cases")
    payment: Mapped["Payment"] = relationship(back_populates="cases")
    contexts: Mapped[list["CaseContext"]] = relationship(back_populates="case")
    diagnoses: Mapped[list["AIDiagnosis"]] = relationship(back_populates="case")
    interventions: Mapped[list["Intervention"]] = relationship(back_populates="case")
    actions: Mapped[list["Action"]] = relationship(back_populates="case")
    approvals: Mapped[list["Approval"]] = relationship(back_populates="case")
    verifications: Mapped[list["Verification"]] = relationship(back_populates="case")
    experiment_assignments: Mapped[list["ExperimentAssignment"]] = relationship(
        back_populates="case"
    )

    def __repr__(self) -> str:
        return f"<Case id={self.id} status={self.status}>"
