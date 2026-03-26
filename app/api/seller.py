from flask import Blueprint

seller_bp = Blueprint('seller', __name__)

@seller_bp.route('/dashboard')
def dashboard():
    return "Seller Dashboard Stub"
