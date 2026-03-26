import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, DateTime, Enum, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..core.database import db

class AspectSentiment(db.Model):
    __tablename__ = "aspect_sentiments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    review_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
    
    aspect_category: Mapped[str] = mapped_column(String(100), nullable=False)
    aspect_term: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    polarity: Mapped[str] = mapped_column(
        Enum("positive", "negative", "neutral", name="sentiment_types"), 
        nullable=False
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    review: Mapped["Review"] = relationship(back_populates="aspect_sentiments")

    __table_args__ = (
        Index("ix_aspect_review_id", "review_id"),
        Index("ix_aspect_cat_polarity", "aspect_category", "polarity"),
        Index("ix_aspect_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<AspectSentiment {self.aspect_category}: {self.polarity} ({self.confidence:.2f})>"
