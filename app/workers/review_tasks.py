import json
import logging
from celery_app import celery
from flask import current_app
from app.core.database import db
from app.core.extensions import redis_client
from app.models.review import Review
from app.models.aspect_sentiment import AspectSentiment
from app.models.complaint import Complaint

logger = logging.getLogger(__name__)

def compute_severity(aspects: list) -> str:
    """
    Compute severity based on negative sentiment density.
    - critical: 2+ aspects with confidence > 0.7 and polarity negative
    - high: 1 negative aspect with confidence > 0.85
    - medium: 1 negative aspect with confidence 0.5–0.85
    - low: everything else
    """
    neg_high_conf = [a for a in aspects if a.polarity == "negative" and a.confidence > 0.7]
    neg_very_high_conf = [a for a in aspects if a.polarity == "negative" and a.confidence > 0.85]
    neg_medium_conf = [a for a in aspects if a.polarity == "negative" and 0.5 <= a.confidence <= 0.85]
    
    if len(neg_high_conf) >= 2:
        return "critical"
    if len(neg_very_high_conf) >= 1:
        return "high"
    if len(neg_medium_conf) >= 1:
        return "medium"
    return "low"

@celery.task(bind=True, max_retries=3, default_retry_delay=60, 
             name="workers.review_tasks.process_review_task")
def process_review_task(self, review_id: str):
    """
    Asynchronous task to process a review using the ABSA pipeline.
    """
    from wsgi import app
    with app.app_context():
        review = Review.query.get(review_id)
        if not review:
            logger.error(f"Review {review_id} not found.")
            return

        try:
            review.status = "processing"
            db.session.commit()

            # Call ABSA pipeline
            from app.ml.model_loader import get_pipeline
            pipeline = get_pipeline()
            result = pipeline.process_review(review.content)

            # Store results
            aspect_objs = []
            for aspect in result.aspects:
                aspect_objs.append(AspectSentiment(
                    review_id=review.id,
                    aspect_category=aspect.aspect_category,
                    aspect_term=aspect.aspect_term,
                    polarity=aspect.polarity,
                    confidence=aspect.confidence
                ))
            
            # Bulk-insert
            db.session.bulk_save_objects(aspect_objs)
            
            # Update review
            review.overall_sentiment = result.overall_sentiment
            review.status = "done"
            
            # Complaint logic
            severity = compute_severity(result.aspects)
            has_strong_negative = any(a.polarity == "negative" and a.confidence > 0.7 for a in result.aspects)
            
            if has_strong_negative:
                complaint = Complaint(
                    review_id=review.id,
                    user_id=review.user_id,
                    product_id=review.product_id,
                    severity=severity,
                    status="open"
                )
                db.session.add(complaint)

            db.session.commit()

            # Store result in Redis
            redis_data = {
                "status": "done",
                "overall_sentiment": result.overall_sentiment,
                "aspects": [a.model_dump() for a in result.aspects]
            }
            redis_client.setex(f"review:{review_id}:result", 3600, json.dumps(redis_data))
            
            logger.info(f"Review {review_id} processed successfully.")

        except Exception as e:
            db.session.rollback()
            review.status = "failed"
            review.processing_error = str(e)
            db.session.commit()
            
            logger.error(f"Error processing review {review_id}: {e}")
            raise self.retry(exc=e)
