from flask_sqlalchemy import SQLAlchemy
from contextlib import contextmanager

db = SQLAlchemy()

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
