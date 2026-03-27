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
    Submit a review, run sentiment analysis synchronously via ABSA pipeline,
    and persist confirmed_emotions for model retraining.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
        
    product_id = data.get('product_id')
    content = data.get('content')
    confirmed_emotions_raw = data.get('confirmed_emotions', [])  # List of label strings from frontend
    
    if not product_id or not content:
        return jsonify({"error": "Product ID and content are required"}), 400
        
    # Validation: 20-2000 chars
    if not (20 <= len(content) <= 2000):
        return jsonify({"error": "Content must be between 20 and 2000 characters"}), 422
    
    # Validate confirmed_emotions is a list of strings
    if not isinstance(confirmed_emotions_raw, list):
        confirmed_emotions_raw = []
    confirmed_emotions_clean = [str(e) for e in confirmed_emotions_raw if isinstance(e, (str, dict))]

    try:
        # Parse product_id
        try:
            pid = uuid.UUID(str(product_id))
        except ValueError:
            return jsonify({"error": "Invalid Product ID"}), 400

        # Ensure product exists
        product = Product.query.get(pid)
        if not product:
            return jsonify({"error": "Product not found"}), 404

        # Create review
        review = Review(
            product_id=pid,
            user_id=g.current_user.id,
            content=content,
            status="processing",
            confirmed_emotions=json.dumps(confirmed_emotions_clean) if confirmed_emotions_clean else None
        )
        db.session.add(review)
        db.session.flush()  # Get review.id without committing

        # Run ABSA pipeline synchronously (avoids Celery/Redis dependency in dev)
        try:
            from ..ml.model_loader import get_pipeline
            from ..models.aspect_sentiment import AspectSentiment
            pipeline = get_pipeline()
            result = pipeline.process_review(content)

            for aspect in result.aspects:
                db.session.add(AspectSentiment(
                    review_id=review.id,
                    aspect_category=aspect.aspect_category,
                    aspect_term=aspect.aspect_term,
                    polarity=aspect.polarity,
                    confidence=aspect.confidence
                ))

            review.overall_sentiment = result.overall_sentiment
            review.status = "done"

        except Exception as pipeline_err:
            # If ML fails entirely, try to infer from confirmed emotions
            neg_emotions = {'Angry', 'Disappointed', 'Disgusted', 'Fearful'}
            pos_emotions = {'Happy', 'Excited', 'Satisfied'}
            
            # Simple voting if confirmed emotions exist
            if confirmed_emotions_clean:
                if any(e in neg_emotions for e in confirmed_emotions_clean):
                    review.overall_sentiment = "negative"
                elif any(e in pos_emotions for e in confirmed_emotions_clean):
                    review.overall_sentiment = "positive"
                else:
                    review.overall_sentiment = "neutral"
            else:
                review.overall_sentiment = "neutral"
                
            review.status = "done"
            review.processing_error = str(pipeline_err)

        db.session.commit()

        # Automatic Complaint Trigger
        if review.overall_sentiment == "negative":
            try:
                from ..models.complaint import Complaint
                from ..ml.complaint_generator import generate_complaint_text
                
                # Check for existing complaint
                if not Complaint.query.filter_by(review_id=review.id).first():
                    # Fallback if AI generation is too slow or fails
                    try:
                        complaint_desc = generate_complaint_text(content)
                    except Exception as gen_err:
                        print(f"AI Generation failed: {gen_err}")
                        complaint_desc = f"Negative feedback reported: {content[:100]}..."

                    auto_complaint = Complaint(
                        review_id=review.id,
                        user_id=g.current_user.id,
                        product_id=pid,
                        severity="high",
                        status="open",
                        admin_notes=f"SYSTEM_AUTO_FLAG: {complaint_desc}"
                    )
                    db.session.add(auto_complaint)
                    db.session.commit()
                    print(f"SUCCESS: AUTOMATIC COMPLAINT CREATED for review {review.id}")
            except Exception as outer_err:
                db.session.rollback()
                print(f"CRITICAL: Auto-complaint creation failed: {outer_err}")
                # We don't abort the review submission if auto-complaint fails, 
                # but we log it heavily.

        return jsonify({
            "review_id": str(review.id),
            "status": review.status,
            "overall_sentiment": review.overall_sentiment,
            "confirmed_emotions": confirmed_emotions_clean,
            "message": "Review submitted and analysed successfully!"
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@reviews_bp.route('/<uuid:review_id>/status', methods=['GET'])
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

@reviews_bp.route('/product/<uuid:product_id>', methods=['GET'])
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

@reviews_bp.route('/preview-complaint', methods=['POST'])
@login_required
@role_required("customer")
def preview_complaint():
    """
    Generate a preview of the complaint text based on the review content.
    Used for showing the user what will be submitted if their review is negative.
    """
    data = request.get_json()
    content = data.get('content')
    confirmed_emotions = data.get('confirmed_emotions', [])
    
    if not content or len(content) < 20:
        return jsonify({"should_escalate": False})

    try:
        from ..ml.model_loader import get_pipeline
        from ..ml.complaint_generator import generate_complaint_text
        
        # 1. Quick sentiment check
        pipeline = get_pipeline()
        result = pipeline.process_review(content)
        
        # Overlay confirmed emotions onto sentiment check
        sentiment = result.overall_sentiment
        neg_emotions = {'Angry', 'Disappointed', 'Disgusted', 'Fearful'}
        if confirmed_emotions and any(e in neg_emotions for e in confirmed_emotions):
            sentiment = "negative"

        if sentiment == "negative":
            complaint_text = generate_complaint_text(content)
            return jsonify({
                "should_escalate": True,
                "sentiment": "negative",
                "preview_text": complaint_text
            })
            
        return jsonify({
            "should_escalate": False, 
            "sentiment": sentiment
        })
    except Exception as e:
        print(f"Preview complaint error: {e}")
        return jsonify({"should_escalate": False, "error": str(e)})
