import uuid
import random
from datetime import datetime, timedelta
from app import create_app
from app.core.database import db
from app.models.user import User
from app.models.product import Product
from app.models.review import Review
from app.models.aspect_sentiment import AspectSentiment
from app.models.complaint import Complaint

def seed_data():
    app = create_app("development")
    with app.app_context():
        print("Cleaning up database...")
        db.drop_all()
        db.create_all()

        print("Seeding users...")
        # 1 Admin
        admin = User(
            email="admin@example.com",
            hashed_password="pbkdf2:sha256:260000$admin_pass", # Placeholder
            name="Admin User",
            role="admin"
        )
        db.session.add(admin)

        # 2 Sellers
        sellers = []
        for i in range(1, 3):
            seller = User(
                email=f"seller{i}@example.com",
                hashed_password=f"pbkdf2:sha256:260000$seller{i}_pass",
                name=f"Seller {i}",
                role="seller"
            )
            sellers.append(seller)
            db.session.add(seller)

        # 5 Customers
        customers = []
        for i in range(1, 6):
            customer = User(
                email=f"customer{i}@example.com",
                hashed_password=f"pbkdf2:sha256:260000$customer{i}_pass",
                name=f"Customer {i}",
                role="customer"
            )
            customers.append(customer)
            db.session.add(customer)

        db.session.commit()

        print("Seeding products...")
        products = []
        categories = ["Electronics", "Home & Kitchen", "Fashion"]
        for seller in sellers:
            for i in range(1, 4):
                product = Product(
                    seller_id=seller.id,
                    name=f"{seller.name} Product {i}",
                    category=random.choice(categories),
                    description="High quality product for premium users."
                )
                products.append(product)
                db.session.add(product)
        
        db.session.commit()

        print("Seeding reviews and aspect sentiments...")
        aspect_categories = ["quality", "price", "delivery", "design", "battery"]
        polarities = ["positive", "negative", "neutral"]
        
        for i in range(20):
            customer = random.choice(customers)
            product = random.choice(products)
            
            review = Review(
                product_id=product.id,
                user_id=customer.id,
                content=f"This is a sample review number {i+1} for {product.name}. The quality is quite interesting and it works as expected for most parts.",
                status="done",
                overall_sentiment=random.choice(polarities)
            )
            db.session.add(review)
            db.session.flush() # Get review ID

            # Add 2-3 aspects per review
            for _ in range(random.randint(2, 3)):
                aspect = AspectSentiment(
                    review_id=review.id,
                    aspect_category=random.choice(aspect_categories),
                    aspect_term="sample term",
                    polarity=random.choice(polarities),
                    confidence=random.uniform(0.7, 0.99)
                )
                db.session.add(aspect)

            # Randomly add complaints for negative reviews
            if review.overall_sentiment == "negative" and random.random() > 0.5:
                complaint = Complaint(
                    review_id=review.id,
                    user_id=customer.id,
                    product_id=product.id,
                    severity=random.choice(["low", "medium", "high", "critical"]),
                    status="open",
                    admin_notes="Sample admin note."
                )
                db.session.add(complaint)

        db.session.commit()
        print("Database seeded successfully!")

if __name__ == "__main__":
    seed_data()
