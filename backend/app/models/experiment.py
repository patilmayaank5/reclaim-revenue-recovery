"""Experiment model."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import ExperimentStatus


class Experiment(TimestampMixin, Base):
    """Represents a treatment/holdout experiment."""

    __tablename__ = "experiments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    segment_filter: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
        comment="Segment criteria for experiment targeting",
    )
    intervention_strategy: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="Intervention strategy being tested",
    )
    status: Mapped[ExperimentStatus] = mapped_column(
        SQLAlchemyEnum(ExperimentStatus, native_enum=False, length=50, values_callable=lambda x: [e.value for e in x]),
        nullable=False, index=True,
    )
    holdout_percentage: Mapped[int] = mapped_column(
        Integer, nullable=False,
        comment="Holdout percentage (0-100)",
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    # Relationships
    assignments: Mapped[list["ExperimentAssignment"]] = relationship(
        back_populates="experiment"
    )

    def __repr__(self) -> str:
        return f"<Experiment id={self.id} name={self.name!r} status={self.status}>"
