from flask import Blueprint, render_template, request, abort, jsonify
from flask_login import login_required, current_user
from ..models import Review, Product
from ..core.auth_decorators import role_required
from sqlalchemy import func

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/')
@login_required
@role_required("customer")
def dashboard():
    """
    Main customer dashboard view with paginated reviews and status summaries.
    """
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    pagination = Review.query.filter_by(user_id=current_user.id) \
        .order_by(Review.created_at.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)
        
    return render_template('customer/dashboard.html', 
                           reviews=pagination.items, 
                           pagination=pagination)

@customer_bp.route('/product/<product_id>/review')
@login_required
@role_required("customer")
def product_review(product_id):
    """
    Product-specific review page with existing reviews and aggregate breakdown.
    """
    product = Product.query.get_or_404(product_id)
    
    # Existing reviews for this product
    page = request.args.get('page', 1, type=int)
    pagination = Review.query.filter_by(product_id=product_id, status="done") \
        .order_by(Review.created_at.desc()) \
        .paginate(page=page, per_page=10, error_out=False)
        
    # Aggregate counts for the aspect breakdown
    # We want counts of positive/negative per category
    # aspects = db.session.query(AspectSentiment.aspect_category, AspectSentiment.polarity, func.count(AspectSentiment.id)) ...
    # Simplified aggregate logic: we'll compute it from product.reviews if not too many
    # or just show overall counts. Let's do a basic one.
    
    return render_template('customer/product_review.html', 
                           product=product,
                           reviews=pagination.items,
                           pagination=pagination)

@customer_bp.route('/reviews')
@login_required
@role_required("customer")
def my_reviews():
    """
    Full view of all customer's reviews.
    """
    page = request.args.get('page', 1, type=int)
    pagination = Review.query.filter_by(user_id=current_user.id) \
        .order_by(Review.created_at.desc()) \
        .paginate(page=page, per_page=20, error_out=False)
        
    return render_template('customer/my_reviews.html', 
                           reviews=pagination.items,
                           pagination=pagination)

@customer_bp.route('/reviews/<review_id>/result-partial', methods=['GET'])
@login_required
def get_review_result_partial(review_id):
    """
    Returns an HTML partial for the review analysis results.
    """
    review = Review.query.get(review_id)
    if not (review and review.status == "done"):
        return "", 204
        
    return render_template('components/aspect_result_card.html', review=review)
