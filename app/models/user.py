import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Boolean, DateTime, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from flask_login import UserMixin
from ..core.database import db

class User(db.Model, UserMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(Enum("customer", "seller", "admin", name="user_roles"), nullable=False)
    
    # Encrypted fields
    phone_encrypted: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    address_encrypted: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    products: Mapped[List["Product"]] = relationship(back_populates="seller", cascade="all, delete-orphan")
    reviews: Mapped[List["Review"]] = relationship(back_populates="user")
    complaints: Mapped[List["Complaint"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"
