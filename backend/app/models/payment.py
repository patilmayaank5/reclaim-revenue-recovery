"""Payment model.

All monetary amounts use integer minor units (e.g. paise, cents).
Never use floating-point for authoritative financial values.
"""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import PaymentStatus


class Payment(TimestampMixin, Base):
    """Represents a payment transaction.

    amount_minor is stored as integer minor units (e.g. 10000 = INR 100.00).
    """

    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id"),
        index=True,
        nullable=False,
    )
    external_id: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False,
        comment="Provider payment identifier",
    )
    amount_minor: Mapped[int] = mapped_column(
        BigInteger, nullable=False,
        comment="Payment amount in integer minor units (e.g. paise)",
    )
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, comment="ISO 4217 currency code",
    )
    status: Mapped[PaymentStatus] = mapped_column(
        SQLAlchemyEnum(PaymentStatus, native_enum=False, length=50, values_callable=lambda x: [e.value for e in x]),
        nullable=False, index=True,
    )
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    failure_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    failure_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="Provider name: razorpay, simulator, demo",
    )
    external_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )

    # Relationships
    merchant: Mapped["Merchant"] = relationship(back_populates="payments")
    cases: Mapped[list["Case"]] = relationship(back_populates="payment")

    def __repr__(self) -> str:
        return f"<Payment id={self.id} amount_minor={self.amount_minor} status={self.status}>"
