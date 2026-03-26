import os
import sys
import uuid
from flask import Flask

# Add project root to sys.path
project_root = r"c:\Users\athin\review-sentiment-analyser"
if project_root not in sys.path:
    sys.path.append(project_root)

from app import create_app
from app.core.database import db
from app.models import Product

app = create_app('development')
with app.app_context():
    p = Product.query.first()
    if p:
        pid = p.id
        print(f"Testing with Product ID: {pid}")
        
        with app.test_client() as client:
            # Login first (mocking login if needed)
            from flask_login import login_user
            from app.models.user import User
            admin = User.query.filter_by(role='admin').first()
            
            # Since we use @login_required, we need a session
            with client.session_transaction() as sess:
                # We need to mock the user loading because test_client 
                # doesn't handle flask_login automatically without setup
                pass

            # Alternative: use the app context and call the function directly
            from app.api.analytics import trend_analysis
            from flask import request
            
            # Mock request
            with app.test_request_context(f'/analytics/product/{pid}/trends?window=30d&granularity=day'):
                try:
                    # We need to satisfy @role_required and @login_required
                    from flask import g
                    from flask_login import login_user
                    user = User.query.filter_by(role='admin').first()
                    login_user(user)
                    
                    res = trend_analysis(pid)
                    print("Response:", res.get_json())
                except Exception as e:
                    import traceback
                    traceback.print_exc()
    else:
        print("No products found")
