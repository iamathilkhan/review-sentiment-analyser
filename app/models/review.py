import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Text, DateTime, Enum, ForeignKey, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..core.database import db

class Review(db.Model):
    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    content: Mapped[str] = mapped_column(Text, nullable=False)
    overall_sentiment: Mapped[Optional[str]] = mapped_column(
        Enum("positive", "negative", "neutral", name="sentiment_types"), 
        nullable=True
    )
    status: Mapped[str] = mapped_column(
        Enum("pending", "processing", "done", "failed", name="processing_status"), 
        default="pending"
    )
    processing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    product: Mapped["Product"] = relationship(back_populates="reviews")
    user: Mapped[Optional["User"]] = relationship(back_populates="reviews")
    aspect_sentiments: Mapped[List["AspectSentiment"]] = relationship(
        back_populates="review", cascade="all, delete-orphan"
    )
    complaint: Mapped[Optional["Complaint"]] = relationship(back_populates="review", uselist=False)

    __table_args__ = (
        Index("ix_reviews_product_status", "product_id", "status"),
        Index("ix_reviews_user_id", "user_id"),
        Index("ix_reviews_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Review {self.id[:8]}... ({self.status})>"
