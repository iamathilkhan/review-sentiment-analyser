import uuid
from app import create_app
from app.core.database import db
from app.models.user import User
from app.models.product import Product
from app.models.review import Review
from app.models.aspect_sentiment import AspectSentiment
from app.models.complaint import Complaint
from app.core.security import hash_password
from datetime import datetime, timedelta

def seed_demo_data():
    app = create_app('development')
    with app.app_context():
        # 1. Create Seller if not exists
        seller_email = "seller@demo.com"
        seller = User.query.filter_by(email=seller_email).first()
        if not seller:
            seller = User(
                id=uuid.uuid4(),
                email=seller_email,
                hashed_password=hash_password("password123"),
                name="Elite Gadget Co.",
                role="seller"
            )
            db.session.add(seller)
            db.session.commit()
            print(f"Created seller: {seller_email}")
        
        # 2. Create Products
        p1 = Product.query.filter_by(name="Pro Headphones X").first()
        if not p1:
            p1 = Product(id=uuid.uuid4(), seller_id=seller.id, name="Pro Headphones X", category="Audio")
            db.session.add(p1)
        
        p2 = Product.query.filter_by(name="Smart Watch Ultra").first()
        if not p2:
            p2 = Product(id=uuid.uuid4(), seller_id=seller.id, name="Smart Watch Ultra", category="Wearables")
            db.session.add(p2)
            
        db.session.commit()
        print("Created products")

        # 3. Create Reviews & Aspects
        # Pro Headphones - Good Reviews
        for i in range(5):
            r = Review(
                product_id=p1.id,
                content=f"Great audio quality and very comfortable headphones! {i}",
                overall_sentiment="positive",
                status="done"
            )
            db.session.add(r)
            db.session.flush()
            
            db.session.add(AspectSentiment(review_id=r.id, aspect_category="Sound Quality", aspect_term="audio", polarity="positive", confidence=0.95))
            db.session.add(AspectSentiment(review_id=r.id, aspect_category="Comfort", aspect_term="comfort", polarity="positive", confidence=0.9))
            
        # Smart Watch - Mixed Reviews
        for i in range(3):
            r = Review(
                product_id=p2.id,
                content=f"Battery life is terrible, but the display is nice. {i}",
                overall_sentiment="neutral",
                status="done"
            )
            db.session.add(r)
            db.session.flush()
            
            db.session.add(AspectSentiment(review_id=r.id, aspect_category="Battery", aspect_term="battery life", polarity="negative", confidence=0.98))
            db.session.add(AspectSentiment(review_id=r.id, aspect_category="Display", aspect_term="display", polarity="positive", confidence=0.92))
            
            if i == 0:
                # Add a complaint for the first negative battery mention
                db.session.add(Complaint(
                    review_id=r.id,
                    user_id=seller.id, # Should be a customer ID but for shell testing seller is fine
                    product_id=p2.id,
                    severity="high",
                    status="open"
                ))

        db.session.commit()
        print("Seeded reviews and complaints")

if __name__ == "__main__":
    seed_demo_data()
