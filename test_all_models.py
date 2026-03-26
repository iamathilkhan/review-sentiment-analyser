from __future__ import annotations
import uuid
from datetime import datetime
from typing import List, Optional
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Boolean, DateTime, Enum, ForeignKey, func, Text, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

class User(db.Model):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(Enum("customer", "seller", "admin", name="user_roles"), nullable=False)
    products: Mapped[List["Product"]] = relationship(back_populates="seller")

class Product(db.Model):
    __tablename__ = "products"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    seller_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    seller: Mapped["User"] = relationship(back_populates="products")

with app.app_context():
    db.create_all()
    print("Success")
