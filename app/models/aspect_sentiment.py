from __future__ import annotations
import uuid
from datetime import datetime
from ..core.database import db

class AspectSentiment(db.Model):
    __tablename__ = "aspect_sentiments"

    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    review_id = db.Column(db.Uuid, db.ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
    
    aspect_category = db.Column(db.String(100), nullable=False)
    aspect_term = db.Column(db.String(100), nullable=True)
    polarity = db.Column(
        db.Enum("positive", "negative", "neutral", name="aspect_sentiment_types"), 
        nullable=False
    )
    confidence = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # Relationships
    review = db.relationship("Review", back_populates="aspect_sentiments")

    __table_args__ = (
        db.Index("ix_aspect_review_id", "review_id"),
        db.Index("ix_aspect_cat_polarity", "aspect_category", "polarity"),
        db.Index("ix_aspect_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<AspectSentiment {self.aspect_category}: {self.polarity} ({self.confidence:.2f})>"
