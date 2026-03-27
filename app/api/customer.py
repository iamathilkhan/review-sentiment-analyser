from flask import Blueprint, render_template, request, abort, jsonify, current_app
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
                           pagination=pagination,
                           active_tab='reviews')

@customer_bp.route('/product/<uuid:product_id>/review')
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

    # Aggregate sentiment stats for the pie chart
    from sqlalchemy import func
    from ..core.database import db
    from ..models import AspectSentiment
    
    sentiment_data = db.session.query(
        Review.overall_sentiment,
        func.count(Review.id)
    ).filter_by(product_id=product_id, status="done").group_by(Review.overall_sentiment).all()
    sentiment_stats = {s[0]: s[1] for s in sentiment_data if s[0]}

    # Aspect stats logic
    aspect_data = db.session.query(
        AspectSentiment.aspect_category,
        AspectSentiment.polarity,
        func.count(AspectSentiment.id)
    ).join(Review).filter(Review.product_id == product_id).group_by(
        AspectSentiment.aspect_category, AspectSentiment.polarity
    ).all()
    
    aspect_stats = {}
    for cat, pol, count in aspect_data:
        if cat not in aspect_stats: aspect_stats[cat] = {"positive": 0, "negative": 0, "neutral": 0}
        aspect_stats[cat][pol] = count

    return render_template('customer/product_review.html', 
                            product=product,
                            reviews=pagination.items,
                            pagination=pagination,
                            sentiment_stats=sentiment_stats,
                            aspect_stats=aspect_stats)

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

@customer_bp.route('/reviews/<uuid:review_id>/result-partial', methods=['GET'])
@login_required
def get_review_result_partial(review_id):
    """
    Returns an HTML partial for the review analysis results.
    """
    review = Review.query.get(review_id)
    if not (review and review.status == "done"):
        return "", 204
        
@customer_bp.route('/predict_emotion', methods=['POST'])
@login_required
def predict_emotion():
    """Predicts emotions using NLP (DistilRoBERTa or VADER fallback). JWT-auth only."""
    data = request.get_json(silent=True)
    if not data or 'text' not in data:
        return jsonify({"emotions": []})

    text = data.get('text', '').strip()
    if len(text) < 5:
        return jsonify({"emotions": []})

    try:
        from ..ml.emotion_detector import predict_emotions
        results = predict_emotions(text, top_k=5)
        return jsonify({"emotions": results})
    except Exception as e:
        current_app.logger.error(f'Emotion prediction error: {e}')
        return jsonify({"emotions": [], "error": str(e)}), 500

@customer_bp.route('/reviews/<uuid:review_id>/complaint', methods=['GET'])
@login_required
@role_required("customer")
def review_complaint(review_id):
    """
    Renders the complaint form for a specific review.
    """
    review = Review.query.get_or_404(review_id)
    # Ensure the user has the right to complain (e.g. they didn't write it, or they did and want to report an error)
    # For now, any customer can report any review.
    
    return render_template('customer/raise_complaint.html', 
                           review=review,
                           user=current_user)

@customer_bp.route('/complaints', methods=['POST'])
@login_required
@role_required("customer")
def submit_complaint():
    """
    Handles the submission of a new complaint.
    """
    data = request.form
    review_id = data.get('review_id')
    product_id = data.get('product_id')
    severity = data.get('severity', 'medium')
    # In a real app we'd save more details, but the model has limited fields.
    # We can use admin_notes or a new field if we wanted more, but the model is strict.
    
    if not review_id or not product_id:
        abort(400, description="Missing required IDs")

    from ..models.complaint import Complaint
    from ..core.database import db
    import uuid

    # Check if a complaint already exists for this review
    existing = Complaint.query.filter_by(review_id=uuid.UUID(review_id)).first()
    if existing:
        return render_template('customer/complaint_success.html', message="A complaint for this review is already being processed.")

    complaint = Complaint(
        review_id=uuid.UUID(review_id),
        user_id=current_user.id,
        product_id=uuid.UUID(product_id),
        severity=severity,
        status='open',
        admin_notes=f"User Report: {data.get('description', 'No details provided.')}"
    )
    
    db.session.add(complaint)
    db.session.commit()
    
    return render_template('customer/complaint_success.html', message="Your complaint has been submitted successfully.")

@customer_bp.route('/my-complaints', methods=['GET'])
@login_required
@role_required("customer")
def list_complaints():
    """
    List all complaints submitted by the current customer.
    """
    from ..models.complaint import Complaint
    page = request.args.get('page', 1, type=int)
    pagination = Complaint.query.filter_by(user_id=current_user.id) \
        .order_by(Complaint.created_at.desc()) \
        .paginate(page=page, per_page=10, error_out=False)
        
    return render_template('customer/dashboard.html', 
                           complaints=pagination.items,
                           pagination=pagination,
                           active_tab='complaints')
