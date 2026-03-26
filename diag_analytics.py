import os
import sys
import uuid
from flask import Flask

# Add project root to sys.path
project_root = r"c:\Users\athin\review-sentiment-analyser"
if project_root not in sys.path:
    sys.path.append(project_root)

from app import create_app
from app.api.analytics import trend_analysis
from app.core.database import db
from app.models import Product, Review

app = create_app('development')
with app.app_context():
    p = Product.query.first()
    if p:
        print(f"Success: Found product {p.name}")
    else:
        print("No products found")
