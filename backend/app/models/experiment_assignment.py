"""Experiment assignment model.

Holdout assignment happens deterministically BEFORE AI processing.
A case may only be assigned once per experiment.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin
from app.models.enums import AssignmentGroup


class ExperimentAssignment(CreatedAtMixin, Base):
    """Represents the assignment of a case to an experiment group.

    Uses a composite unique constraint on (experiment_id, case_id)
    to prevent duplicate assignments.
    """

    __tablename__ = "experiment_assignments"
    __table_args__ = (
        UniqueConstraint(
            "experiment_id", "case_id",
            name="uq_experiment_assignment_experiment_case",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id"),
        index=True,
        nullable=False,
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id"),
        index=True,
        nullable=False,
    )
    group: Mapped[AssignmentGroup] = mapped_column(
        SQLAlchemyEnum(AssignmentGroup, native_enum=False, length=50, values_callable=lambda x: [e.value for e in x]),
        nullable=False, index=True,
        comment="Treatment or holdout group",
    )
    assignment_hash: Mapped[str] = mapped_column(
        String(255), nullable=False,
        comment="Deterministic hash used for assignment",
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )

    # Relationships
    experiment: Mapped["Experiment"] = relationship(back_populates="assignments")
    case: Mapped["Case"] = relationship(back_populates="experiment_assignments")

    def __repr__(self) -> str:
        return f"<ExperimentAssignment id={self.id} group={self.group}>"
