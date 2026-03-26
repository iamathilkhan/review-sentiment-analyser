from __future__ import annotations
import uuid
from datetime import datetime
from flask_login import UserMixin
from ..core.database import db

class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(255), unique=True, nullable=False)
    hashed_password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("customer", "seller", "admin", name="user_roles"), nullable=False)
    
    phone_encrypted = db.Column(db.String(500), nullable=True)
    address_encrypted = db.Column(db.String(1000), nullable=True)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    # Relationships
    products = db.relationship("Product", back_populates="seller", cascade="all, delete-orphan")
    reviews = db.relationship("Review", back_populates="user")
    complaints = db.relationship("Complaint", back_populates="user")

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"
