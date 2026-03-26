from flask import Blueprint, render_template
from ..models.review import Review

reviews_bp = Blueprint('reviews', __name__)

@reviews_bp.route('/')
def index():
    """List all reviews."""
    reviews = Review.query.all()
    return render_template('customer/reviews.html', reviews=reviews)
