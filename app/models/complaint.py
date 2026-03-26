from __future__ import annotations
import uuid
from datetime import datetime
from ..core.database import db

class Complaint(db.Model):
    __tablename__ = "complaints"

    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    review_id = db.Column(db.Uuid, db.ForeignKey("reviews.id", ondelete="CASCADE"), unique=True, nullable=False)
    user_id = db.Column(db.Uuid, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id = db.Column(db.Uuid, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    
    severity = db.Column(
        db.Enum("low", "medium", "high", "critical", name="severity_levels"), 
        nullable=False
    )
    status = db.Column(
        db.Enum("open", "in_progress", "resolved", "closed", name="complaint_status"), 
        default="open"
    )
    admin_notes = db.Column(db.Text, nullable=True)
    severity_override = db.Column(
        db.Enum("low", "medium", "high", "critical", name="severity_levels"), 
        nullable=True
    )
    
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    resolved_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    review = db.relationship("Review", back_populates="complaint")
    user = db.relationship("User", back_populates="complaints")
    product = db.relationship("Product", back_populates="complaints")

    __table_args__ = (
        db.Index("ix_complaints_product_status", "product_id", "status"),
        db.Index("ix_complaints_severity", "severity"),
    )

    def __repr__(self) -> str:
        return f"<Complaint {str(self.id)[:8]}... ({self.severity}/{self.status})>"
