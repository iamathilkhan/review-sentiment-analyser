import os
import uuid
from wsgi import app
from app.core.database import db
from app.models import User, Product, Review, AspectSentiment, Complaint
from werkzeug.security import generate_password_hash
from datetime import datetime

def seed_db():
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        print("Creating all tables...")
        db.create_all()
        
        print("Seeding database...")
        
        # Use UUIDs explicitly to avoid any issues with auto-generation during commit if needed
        u_admin_id = uuid.uuid4()
        u_customer_id = uuid.uuid4()
        u_seller_id = uuid.uuid4()
        
        admin = User(id=u_admin_id, name="Admin User", email="admin@example.com", 
                     hashed_password=generate_password_hash("admin123"), 
                     role="admin", is_active=True)
        customer = User(id=u_customer_id, name="John Customer", email="customer@example.com", 
                        hashed_password=generate_password_hash("password123"), 
                        role="customer", is_active=True)
        seller = User(id=u_seller_id, name="Gadget Seller", email="seller@example.com", 
                      hashed_password=generate_password_hash("seller123"), 
                      role="seller", is_active=True)
        
        db.session.add_all([admin, customer, seller])
        db.session.commit()
        
        # Create Products
        p1_id = uuid.uuid4()
        p1 = Product(id=p1_id, name="SmartPhone X1", description="High-end smartphone with neural engine", 
                     category="Electronics", seller_id=u_seller_id)
        p2 = Product(name="EcoPods Pro", description="Wireless earbuds with noise cancellation", 
                     category="Audio", seller_id=u_seller_id)
        p3 = Product(name="VoltWatch", description="Smartwatch with 7-day battery life", 
                     category="Wearables", seller_id=u_seller_id)
        
        db.session.add_all([p1, p2, p3])
        db.session.commit()
        
        # Create a sample review
        r1 = Review(user_id=u_customer_id, product_id=p1_id, 
                    content="Amazing camera quality and really fast performance! Battery lasts all day.",
                    overall_sentiment="positive", status="done")
        db.session.add(r1)
        db.session.commit()
        
        # Add aspect sentiments
        a1 = AspectSentiment(review_id=r1.id, aspect_category="camera", aspect_term="camera quality", 
                            polarity="positive", confidence=0.95)
        a2 = AspectSentiment(review_id=r1.id, aspect_category="performance", aspect_term="fast performance", 
                            polarity="positive", confidence=0.92)
        a3 = AspectSentiment(review_id=r1.id, aspect_category="battery_life", aspect_term="battery", 
                            polarity="positive", confidence=0.88)
        
        db.session.add_all([a1, a2, a3])
        db.session.commit()
        
        print("Seeding complete.")

if __name__ == "__main__":
    seed_db()
