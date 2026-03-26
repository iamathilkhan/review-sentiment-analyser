import json
import uuid
from flask import Blueprint, request, jsonify, g, abort, render_template
from ..models import Review, AspectSentiment, Product
from ..core.database import db
from ..core.extensions import redis_client
from ..core.auth_decorators import login_required, role_required, rate_limit
from ..workers.review_tasks import process_review_task

reviews_bp = Blueprint('reviews', __name__)

@reviews_bp.route('/')
def index():
    """Public products landing page."""
    products = Product.query.limit(10).all()
    return render_template('public/index.html', products=products)

@reviews_bp.route('/', methods=['POST'])
@login_required
@role_required("customer")
@rate_limit(limit=10, window=3600)
def submit_review():
    """
    Submit a review for analysis.
    Validates content length and enqueues a Celery task.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
        
    product_id = data.get('product_id')
    content = data.get('content')
    
    if not product_id or not content:
        return jsonify({"error": "Product ID and content are required"}), 400
        
    # Validation: 20-2000 chars
    if not (20 <= len(content) <= 2000):
        return jsonify({"error": "Content must be between 20 and 2000 characters"}), 422
        
    try:
        review = Review(
            product_id=uuid.UUID(product_id),
            user_id=g.current_user.id,
            content=content,
            status="pending"
        )
        db.session.add(review)
        db.session.commit()
        
        # Enqueue analysis task
        process_review_task.delay(str(review.id))
        
        return jsonify({
            "review_id": str(review.id),
            "status": "pending",
            "message": "Review queued for analysis"
        }), 202
        
    except ValueError:
        return jsonify({"error": "Invalid Product ID format"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@reviews_bp.route('/<review_id>/status', methods=['GET'])
@login_required
def get_review_status(review_id):
    """
    Poll the status of a review analysis.
    Checks Redis first for fast path, then DB.
    """
    # 1. Fast path: Redis
    redis_key = f"review:{review_id}:result"
    cached_result = redis_client.get(redis_key)
    
    if cached_result:
        result_data = json.loads(cached_result)
        return jsonify({
            "review_id": review_id,
            "status": result_data["status"],
            "overall_sentiment": result_data.get("overall_sentiment"),
            "aspects": result_data.get("aspects")
        })
        
    # 2. Slow path: DB
    review = Review.query.get(review_id)
    if not review:
        abort(404, description="Review not found")
        
    # Ownership check: Customer can only see their own
    if g.current_user.id != review.user_id and g.current_user.role != "admin":
        abort(403, description="You can only access your own reviews")
        
    return jsonify({
        "review_id": str(review.id),
        "status": review.status,
        "overall_sentiment": review.overall_sentiment,
        "aspects": [
            {
                "aspect_category": a.aspect_category,
                "polarity": a.polarity,
                "confidence": a.confidence,
                "aspect_term": a.aspect_term
            } for a in review.aspect_sentiments
        ] if review.status == "done" else None
    })

@reviews_bp.route('/product/<product_id>', methods=['GET'])
def get_product_reviews(product_id):
    """
    Get a list of reviews for a product with pagination.
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    pagination = Review.query.filter_by(product_id=product_id, status="done") \
        .order_by(Review.created_at.desc()) \
        .paginate(page=page, per_page=per_page)
        
    reviews_list = []
    for r in pagination.items:
        reviews_list.append({
            "id": str(r.id),
            "content": r.content,
            "overall_sentiment": r.overall_sentiment,
            "created_at": r.created_at.isoformat(),
            "aspects": [
                {
                    "category": a.aspect_category,
                    "polarity": a.polarity
                } for a in r.aspect_sentiments
            ]
        })
        
    return jsonify({
        "reviews": reviews_list,
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages
    })
