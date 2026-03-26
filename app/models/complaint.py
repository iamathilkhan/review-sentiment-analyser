import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, Enum, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..core.database import db

class Complaint(db.Model):
    __tablename__ = "complaints"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    review_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("reviews.id", ondelete="CASCADE"), unique=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    
    severity: Mapped[str] = mapped_column(
        Enum("low", "medium", "high", "critical", name="severity_levels"), 
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        Enum("open", "in_progress", "resolved", "closed", name="complaint_status"), 
        default="open"
    )
    admin_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    review: Mapped["Review"] = relationship(back_populates="complaint")
    user: Mapped["User"] = relationship(back_populates="complaints")
    product: Mapped["Product"] = relationship(back_populates="complaints")

    __table_args__ = (
        Index("ix_complaints_product_status", "product_id", "status"),
        Index("ix_complaints_severity", "severity"),
    )

    def __repr__(self) -> str:
        return f"<Complaint {self.id[:8]}... ({self.severity}/{self.status})>"
