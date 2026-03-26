import uuid
from flask import Flask
from config import config_by_name
from app.core.database import db
# Import only models needed
from app.models.user import User
from app.models.product import Product
from app.models.review import Review
from app.models.aspect_sentiment import AspectSentiment
from app.models.complaint import Complaint
from app.core.security import hash_password
from datetime import datetime, timedelta

def seed_demo_data():
    # Manual app setup for seeding to avoid blueprint loading
    app = Flask(__name__)
    app.config.from_object(config_by_name['development'])
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        # Clean existing test data if any for these emails
        seller_email = "seller@gmail.com"
        # 1. Create Seller
        seller = User.query.filter_by(email=seller_email).first()
        if not seller:
            seller = User(
                id=uuid.uuid4(),
                email=seller_email,
                hashed_password=hash_password("seller123"),
                name="Elite Gadget Co.",
                role="seller"
            )
            db.session.add(seller)
            db.session.commit()
            print(f"Created seller: {seller_email}")

        # 1.1 Create Admin
        admin_email = "admin@gmail.com"
        admin = User.query.filter_by(email=admin_email).first()
        if not admin:
            admin = User(
                id=uuid.uuid4(),
                email=admin_email,
                hashed_password=hash_password("admin123"),
                name="Head Moderator",
                role="admin"
            )
            db.session.add(admin)
            db.session.commit()
            print(f"Created admin: {admin_email}")

        # 1.2 Create Customer
        customer_email = "khan@gmail.com"
        customer = User.query.filter_by(email=customer_email).first()
        if not customer:
            customer = User(
                id=uuid.uuid4(),
                email=customer_email,
                hashed_password=hash_password("khan123"),
                name="Khan",
                role="customer"
            )
            db.session.add(customer)
            db.session.commit()
            print(f"Created customer: {customer_email}")
        
        # 2. Create Products
        p1 = Product(id=uuid.uuid4(), seller_id=seller.id, name="Pro Headphones X", category="Audio")
        p2 = Product(id=uuid.uuid4(), seller_id=seller.id, name="Smart Watch Ultra", category="Wearables")
        db.session.add_all([p1, p2])
        db.session.commit()
        print("Created products")

        # 3. Create Reviews & Aspects
        for i in range(5):
            r = Review(
                product_id=p1.id,
                content=f"Quality is amazing. {i}",
                overall_sentiment="positive",
                status="done"
            )
            db.session.add(r)
            db.session.flush()
            db.session.add(AspectSentiment(review_id=r.id, aspect_category="Sound", polarity="positive", confidence=0.9))
            
        for i in range(3):
            r = Review(
                product_id=p2.id,
                content=f"Bad battery. {i}",
                overall_sentiment="negative",
                status="done"
            )
            db.session.add(r)
            db.session.flush()
            db.session.add(AspectSentiment(review_id=r.id, aspect_category="Battery", polarity="negative", confidence=0.88))
            
            if i == 0:
                db.session.add(Complaint(
                    review_id=r.id,
                    user_id=seller.id,
                    product_id=p2.id,
                    severity="high",
                    status="open"
                ))

        db.session.commit()
        print("Seeded reviews and complaints successfully.")

if __name__ == "__main__":
    seed_demo_data()
