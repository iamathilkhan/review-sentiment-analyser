from __future__ import annotations
import uuid
from datetime import datetime
from ..core.database import db

class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    seller_id = db.Column(db.Uuid, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(1000), nullable=True)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # Relationships
    seller = db.relationship("User", back_populates="products")
    reviews = db.relationship("Review", back_populates="product", cascade="all, delete-orphan")
    complaints = db.relationship("Complaint", back_populates="product", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Product {self.name} ({self.category})>"
