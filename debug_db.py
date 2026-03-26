from wsgi import app
from app.core.database import db
from app.models import User, Product, Review, AspectSentiment, Complaint

with app.app_context():
    print("Base metadata tables:", db.metadata.tables.keys())
    try:
        db.create_all()
        print("Success: tables created")
    except Exception as e:
        import traceback
        traceback.print_exc()
