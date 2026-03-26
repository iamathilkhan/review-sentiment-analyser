from flask import Blueprint, render_template, jsonify, request, abort
from flask_login import login_required, current_user
from ..core.database import db
from ..core.auth_decorators import role_required
from ..models.product import Product
from ..models.review import Review
from ..models.aspect_sentiment import AspectSentiment
from ..models.complaint import Complaint
from sqlalchemy import func, desc
from datetime import datetime, timedelta

seller_bp = Blueprint('seller', __name__)

@seller_bp.route('/overview')
@login_required
@role_required('seller')
def dashboard():
    """Main seller dashboard entry point."""
    products = Product.query.filter_by(seller_id=current_user.id).all()
    dashboard_data = []

    for p in products:
        # Sentiment stats
        sentiment_stats = db.session.query(
            Review.overall_sentiment,
            func.count(Review.id)
        ).filter(Review.product_id == p.id).group_by(Review.overall_sentiment).all()
        
        sentiment_breakdown = {
            'positive': next((count for sent, count in sentiment_stats if sent == 'positive'), 0),
            'negative': next((count for sent, count in sentiment_stats if sent == 'negative'), 0),
            'neutral': next((count for sent, count in sentiment_stats if sent == 'neutral'), 0)
        }
        
        # Total counts
        review_count = sum(sentiment_breakdown.values())
        complaint_count = Complaint.query.filter_by(product_id=p.id, status='open').count()
        
        # Top aspects
        aspect_stats = db.session.query(
            AspectSentiment.aspect_category,
            AspectSentiment.polarity,
            func.count(AspectSentiment.id).label('count')
        ).join(Review).filter(
            Review.product_id == p.id
        ).group_by(
            AspectSentiment.aspect_category, 
            AspectSentiment.polarity
        ).order_by(desc('count')).all()
        
        pos_aspects_all = [row.aspect_category for row in aspect_stats if row.polarity == 'positive']
        neg_aspects_all = [row.aspect_category for row in aspect_stats if row.polarity == 'negative']
        
        pos_aspects = pos_aspects_all[:3]
        neg_aspects = neg_aspects_all[:3]
        
        dashboard_data.append({
            'product': {
                'id': str(p.id),
                'name': p.name,
                'category': p.category
            },
            'review_count': review_count,
            'sentiment_breakdown': sentiment_breakdown,
            'top_positive_aspects': pos_aspects,
            'top_negative_aspects': neg_aspects,
            'complaint_count': complaint_count
        })

    return render_template('seller/dashboard.html', data=dashboard_data)

@seller_bp.route('/product/<uuid:product_id>/aspects')
@login_required
@role_required('seller')
def product_aspects(product_id):
    """Deep aspect analysis for a specific product."""
    product = Product.query.get_or_404(product_id)
    if product.seller_id != current_user.id:
        abort(403)
        
    aspect_metrics = db.session.query(
        AspectSentiment.aspect_category,
        AspectSentiment.polarity,
        func.count(AspectSentiment.id).label('count'),
        func.avg(AspectSentiment.confidence).label('avg_conf')
    ).join(Review).filter(Review.product_id == product_id).group_by(
        AspectSentiment.aspect_category, AspectSentiment.polarity
    ).all()
    
    # Process into flat structure
    categories = {}
    for row in aspect_metrics:
        cat = row.aspect_category
        pol = row.polarity
        count = int(row.count or 0)
        conf = float(row.avg_conf or 0)
        
        if cat not in categories:
            categories[cat] = {
                'positive': 0, 
                'negative': 0, 
                'neutral': 0, 
                'conf_sum': 0.0, 
                'count': 0
            }
        
        # Aggregate sentiment counts
        if pol in categories[cat]:
            categories[cat][pol] = count
            
        categories[cat]['conf_sum'] += (conf * count)
        categories[cat]['count'] += count
    
    # Add terms and trend
    result = []
    now = datetime.utcnow()
    last_7 = now - timedelta(days=7)
    prior_7 = now - timedelta(days=14)
    
    for cat, data in categories.items():
        # Get top terms
        term_query = db.session.query(
            AspectSentiment.aspect_term, 
            func.count(AspectSentiment.id)
        ).join(Review).filter(
            Review.product_id == product_id,
            AspectSentiment.aspect_category == cat
        ).group_by(
            AspectSentiment.aspect_term
        ).order_by(desc(func.count(AspectSentiment.id))).limit(5).all()
        
        # Recent trend (last 7 days pos ratio vs prior)
        recent_pos = db.session.query(func.count(AspectSentiment.id)).join(Review).filter(
            Review.product_id == product_id,
            AspectSentiment.aspect_category == cat,
            AspectSentiment.polarity == 'positive',
            Review.created_at >= last_7
        ).scalar() or 0
        
        recent_total = db.session.query(func.count(AspectSentiment.id)).join(Review).filter(
            Review.product_id == product_id,
            AspectSentiment.aspect_category == cat,
            Review.created_at >= last_7
        ).scalar() or 0
        
        prior_pos = db.session.query(func.count(AspectSentiment.id)).join(Review).filter(
            Review.product_id == product_id,
            AspectSentiment.aspect_category == cat,
            AspectSentiment.polarity == 'positive',
            Review.created_at.between(prior_7, last_7)
        ).scalar() or 0
        
        prior_total = db.session.query(func.count(AspectSentiment.id)).join(Review).filter(
            Review.product_id == product_id,
            AspectSentiment.aspect_category == cat,
            Review.created_at.between(prior_7, last_7)
        ).scalar() or 0
        
        recent_ratio = recent_pos / recent_total if recent_total > 0 else 0
        prior_ratio = prior_pos / prior_total if prior_total > 0 else 0
        
        trend = "stable"
        if recent_total > 0 and prior_total > 0:
            if recent_ratio > prior_ratio + 0.1: trend = "improving"
            elif recent_ratio < prior_ratio - 0.1: trend = "declining"
        
        result.append({
            'aspect_category': cat,
            'positive_count': data['positive'],
            'negative_count': data['negative'],
            'neutral_count': data['neutral'],
            'avg_confidence': data['conf_sum'] / data['count'] if data['count'] > 0 else 0,
            'sample_terms': [t[0] for t in term_query],
            'recent_trend': trend
        })
        
    return jsonify(result)

@seller_bp.route('/complaints')
@login_required
@role_required('seller')
def complaints():
    """Fetch complaints for seller's products."""
    query = Complaint.query.join(Product).filter(Product.seller_id == current_user.id)
    
    if request.headers.get('Accept') == 'application/json':
        complaints_list = query.order_by(desc(Complaint.created_at)).all()
        return jsonify([{
            'id': str(c.id),
            'product_name': c.product.name,
            'severity': c.severity,
            'status': c.status,
            'created_at': c.created_at.isoformat(),
            'review_excerpt': (c.review.content[:100] + '...') if c.review.content else ""
        } for c in complaints_list])
    
    return render_template('seller/complaints.html')

@seller_bp.route('/complaints/<uuid:complaint_id>', methods=['PATCH'])
@login_required
@role_required('seller')
def update_complaint(complaint_id):
    """Update complaint status."""
    complaint = Complaint.query.get_or_404(complaint_id)
    if complaint.product.seller_id != current_user.id:
        abort(403)
        
    data = request.get_json()
    if 'status' in data:
        if data['status'] in ['in_progress', 'resolved', 'closed']:
            complaint.status = data['status']
            if data['status'] == 'resolved':
                complaint.resolved_at = datetime.utcnow()
            db.session.commit()
            return jsonify({'success': True, 'status': complaint.status})
            
    return jsonify({'success': False, 'message': 'Invalid status'}), 400
