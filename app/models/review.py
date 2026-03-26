from __future__ import annotations
import uuid
from datetime import datetime
from ..core.database import db

class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    product_id = db.Column(db.Uuid, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Uuid, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    content = db.Column(db.Text, nullable=False)
    overall_sentiment = db.Column(
        db.Enum("positive", "negative", "neutral", name="sentiment_types"), 
        nullable=True
    )
    status = db.Column(
        db.Enum("pending", "processing", "done", "failed", name="processing_status"), 
        default="pending"
    )
    processing_error = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # Relationships
    product = db.relationship("Product", back_populates="reviews")
    user = db.relationship("User", back_populates="reviews")
    aspect_sentiments = db.relationship(
        "AspectSentiment", back_populates="review", cascade="all, delete-orphan"
    )
    complaint = db.relationship("Complaint", back_populates="review", uselist=False)

    __table_args__ = (
        db.Index("ix_reviews_product_status", "product_id", "status"),
        db.Index("ix_reviews_user_id", "user_id"),
        db.Index("ix_reviews_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Review {str(self.id)[:8]}... ({self.status})>"
