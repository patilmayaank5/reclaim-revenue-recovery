"""Intervention candidate model.

All monetary values use integer minor units.

Expected Recovery Value (ERV) is deterministic:
    ERV = P(recovery) * Recoverable Amount - Intervention Cost - Risk Penalty

The actual calculation logic belongs to a later phase.
The LLM is NOT authoritative for ERV.
"""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin


class Intervention(CreatedAtMixin, Base):
    """A candidate intervention for a revenue-at-risk case.

    expected_recovery_value_minor is computed deterministically by the backend.
    estimated_recovery_probability is a calibrated probability, NOT raw AI confidence.
    """

    __tablename__ = "interventions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id"),
        index=True,
        nullable=False,
    )
    diagnosis_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_diagnoses.id"),
        nullable=True,
    )
    intervention_type: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="Intervention type: smart_retry, payment_link, dunning_email, etc.",
    )
    recoverable_amount_minor: Mapped[int] = mapped_column(
        BigInteger, nullable=False,
        comment="Recoverable amount in integer minor units",
    )
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, comment="ISO 4217 currency code",
    )
    estimated_recovery_probability_bps: Mapped[int] = mapped_column(
        Integer, nullable=False,
        comment="Calibrated recovery probability for ERV in basis points (0-10000)",
    )
    intervention_cost_minor: Mapped[int] = mapped_column(
        BigInteger, nullable=False,
        comment="Intervention cost in integer minor units",
    )
    risk_penalty_minor: Mapped[int] = mapped_column(
        BigInteger, nullable=False,
        comment="Risk penalty in integer minor units",
    )
    expected_recovery_value_minor: Mapped[int] = mapped_column(
        BigInteger, nullable=False,
        comment="Deterministic ERV in integer minor units. Computed by backend, NOT by LLM.",
    )
    rank: Mapped[int] = mapped_column(
        Integer, nullable=False,
        comment="Rank among intervention candidates for this case",
    )
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    case: Mapped["Case"] = relationship(back_populates="interventions")
    diagnosis: Mapped["AIDiagnosis | None"] = relationship(back_populates="interventions")
    actions: Mapped[list["Action"]] = relationship(back_populates="intervention")

    def __repr__(self) -> str:
        return f"<Intervention id={self.id} type={self.intervention_type!r} erv={self.expected_recovery_value_minor}>"
