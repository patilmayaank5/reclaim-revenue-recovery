"""Merchant model."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Merchant(TimestampMixin, Base):
    """Represents a merchant in the Reclaim system."""

    __tablename__ = "merchants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    external_id: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False,
        comment="Provider merchant identifier (e.g. Razorpay merchant ID)",
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    business_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata", JSONB, nullable=True, comment="Flexible merchant metadata",
    )

    # Relationships
    payments: Mapped[list["Payment"]] = relationship(back_populates="merchant")
    cases: Mapped[list["Case"]] = relationship(back_populates="merchant")

    def __repr__(self) -> str:
        return f"<Merchant id={self.id} name={self.name!r}>"
