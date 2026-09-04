"""Case context / enrichment model."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin


class CaseContext(CreatedAtMixin, Base):
    """Enriched context for a revenue-at-risk case.

    Stores structured contextual information used by the AI diagnosis layer.
    JSONB is used for genuinely variable contextual data.
    """

    __tablename__ = "case_contexts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id"),
        index=True,
        nullable=False,
    )
    context_type: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="Type of context: payment_history, merchant_profile, etc.",
    )
    context_data: Mapped[dict] = mapped_column(
        JSONB, nullable=False,
        comment="Structured context payload",
    )
    source: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="Source of enrichment data",
    )

    # Relationships
    case: Mapped["Case"] = relationship(back_populates="contexts")

    def __repr__(self) -> str:
        return f"<CaseContext id={self.id} type={self.context_type!r}>"
