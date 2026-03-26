from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from contextlib import contextmanager

class Base(DeclarativeBase):
    """Base class for SQLAlchemy 2.0 style models."""
    pass

db = SQLAlchemy(model_class=Base)

@contextmanager
def get_db():
    """Provides a transactional scope around a series of operations."""
    try:
        yield db.session
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    finally:
        db.session.remove()
