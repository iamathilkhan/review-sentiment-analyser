from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import List

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
db.init_app(app)

class User(db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    products: Mapped[List["Product"]] = relationship(back_populates="seller")

class Product(db.Model):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    seller_id: Mapped[int] = mapped_column(db.ForeignKey("users.id"))
    seller: Mapped["User"] = relationship(back_populates="products")

with app.app_context():
    db.create_all()
    print("Test Success")
