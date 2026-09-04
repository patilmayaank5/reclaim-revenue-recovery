"""AI Diagnosis model.

IMPORTANT: ai_confidence and recovery_probability are deliberately separate.
- ai_confidence: Raw AI model output (0.0-1.0). NOT authoritative for ERV.
- recovery_probability: Calibrated/adjusted probability used in ERV calculation.
  Set separately from AI confidence. May be null until calibration.

Do NOT use ai_confidence as the authoritative recovery probability.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin


class AIDiagnosis(CreatedAtMixin, Base):
    """AI-generated diagnosis for a revenue-at-risk case.

    Stores the structured output of the AI diagnosis step.
    AI will be implemented in Phase 4 â€” this is the persistence model only.
    """

    __tablename__ = "ai_diagnoses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id"),
        index=True,
        nullable=False,
    )
    diagnosis_category: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="Diagnosed failure category",
    )
    evidence: Mapped[dict] = mapped_column(
        JSONB, nullable=False,
        comment="Structured evidence supporting the diagnosis",
    )
    ai_confidence: Mapped[float] = mapped_column(
        Float, nullable=False,
        comment="Raw AI confidence score (0.0-1.0). NOT recovery probability.",
    )
    recovery_probability: Mapped[float | None] = mapped_column(
        Float, nullable=True,
        comment="Calibrated recovery probability â€” separate from ai_confidence.",
    )
    model_provider: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="AI provider: anthropic",
    )
    model_name: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="Model identifier",
    )
    prompt_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    raw_response_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    case: Mapped["Case"] = relationship(back_populates="diagnoses")
    interventions: Mapped[list["Intervention"]] = relationship(back_populates="diagnosis")

    def __repr__(self) -> str:
        return f"<AIDiagnosis id={self.id} category={self.diagnosis_category!r}>"
