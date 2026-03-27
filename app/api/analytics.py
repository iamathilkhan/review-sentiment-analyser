from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required, current_user
from ..core.database import db
from ..core.extensions import redis_client
from ..core.auth_decorators import role_required
from sqlalchemy import text
from datetime import datetime, timedelta
import json

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/product/<uuid:product_id>/trends')
@login_required
@role_required("seller", "admin")
def trend_analysis(product_id):
    """Aspect-level sentiment trends over time."""
    aspect_categories = request.args.get('aspect_categories', 'all')
    window = request.args.get('window', '30d')
    granularity = request.args.get('granularity', 'day')
    
    # Caching
    cache_key = f"trend:{str(product_id)}:{window}:{granularity}"
    try:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            return jsonify(json.loads(cached_data))
    except Exception:
        pass # Skip cache if Redis is down

    # SQLite compatible interval & date trunc
    # intervals: 7d, 30d, 90d, 1y
    interval_map = {'7d': '-7 days', '30d': '-30 days', '90d': '-90 days', '1y': '-1 year'}
    sqlite_interval = interval_map.get(window, '-30 days')
    
    # SQLite date formats for period grouping
    granularity_map = {
        'day': '%Y-%m-%d',
        'week': '%Y-%W', # %W is week number (00-53)
        'month': '%Y-%m'
    }
    date_fmt = granularity_map.get(granularity, '%Y-%m-%d')

    sql = text(f"""
        SELECT 
            strftime('{date_fmt}', r.created_at) as period,
            a.aspect_category,
            SUM(CASE WHEN a.polarity = 'positive' THEN 1 ELSE 0 END) as positive,
            SUM(CASE WHEN a.polarity = 'negative' THEN 1 ELSE 0 END) as negative,
            SUM(CASE WHEN a.polarity = 'neutral' THEN 1 ELSE 0 END) as neutral,
            AVG(a.confidence) as avg_confidence
        FROM aspect_sentiments a
        JOIN reviews r ON r.id = a.review_id
        WHERE r.product_id = :product_id
          AND r.created_at >= datetime('now', :window_interval)
        GROUP BY period, a.aspect_category
        ORDER BY period ASC
    """)
    
    results = db.session.execute(sql, {"product_id": str(product_id), "window_interval": sqlite_interval}).fetchall()
    
    # Process results
    data_list = []
    aspect_series = {} # For velocity calculation
    
    for row in results:
        period_data = {
            "period": row[0],
            "aspect_category": row[1],
            "positive": int(row[2] or 0),
            "negative": int(row[3] or 0),
            "neutral": int(row[4] or 0),
            "avg_confidence": float(row[5] or 0)
        }
        data_list.append(period_data)
        
        # Track positive ratio for velocity
        total = period_data['positive'] + period_data['negative'] + period_data['neutral']
        ratio = period_data['positive'] / total if total > 0 else 0
        if row[1] not in aspect_series:
            aspect_series[row[1]] = []
        aspect_series[row[1]].append(ratio)

    # Compute velocity (slope across last 3 periods)
    velocity_results = {}
    for cat, series in aspect_series.items():
        if len(series) >= 2:
            last_idx = len(series) - 1
            # If 3 or more, take (last - second_to_last) or average
            if len(series) >= 3:
                delta = (series[last_idx] - series[last_idx - 2]) / 2
            else:
                delta = series[last_idx] - series[last_idx - 1]
                
            direction = "stable"
            if delta > 0.05: direction = "improving"
            elif delta < -0.05: direction = "declining"
            
            velocity_results[cat] = {
                "direction": direction,
                "delta_pct": float(round(delta * 100, 1))
            }
        else:
            velocity_results[cat] = {"direction": "stable", "delta_pct": 0.0}

    final_result = {"data": data_list, "velocity": velocity_results}
    
    # Store in cache
    try:
        redis_client.setex(cache_key, 300, json.dumps(final_result))
    except Exception:
        pass
    
    return jsonify(final_result)

@analytics_bp.route('/product/<uuid:product_id>/heatmap')
@login_required
def heatmap_data(product_id):
    """Heatmap structure for sentiment across aspects and periods."""
    # Last 12 weeks for heatmap
    twelve_weeks_ago = datetime.utcnow() - timedelta(weeks=12)
    
    sql = text("""
        SELECT 
            strftime('%Y-W%W', r.created_at) as period,
            a.aspect_category,
            SUM(CASE WHEN a.polarity = 'positive' THEN 1 ELSE 0 END) as positive,
            COUNT(*) as total
        FROM aspect_sentiments a
        JOIN reviews r ON r.id = a.review_id
        WHERE r.product_id = :product_id
          AND r.created_at >= :since
        GROUP BY period, a.aspect_category
        ORDER BY period ASC
    """)
    
    results = db.session.execute(sql, {
        "product_id": str(product_id), 
        "since": twelve_weeks_ago.strftime('%Y-%m-%d %H:%M:%S')
    }).fetchall()
    
    periods = sorted(list(set(row[0] for row in results)))
    aspects = sorted(list(set(row[1] for row in results)))
    
    # Initialize 2D grid
    # cells[aspect_idx][period_idx] = [ratio, count]
    cells = [[[0, 0] for _ in range(len(periods))] for _ in range(len(aspects))]
    
    p_map = {p: i for i, p in enumerate(periods)}
    a_map = {a: i for i, a in enumerate(aspects)}
    
    for row in results:
        p_idx = p_map[row[0]]
        a_idx = a_map[row[1]]
        pos = int(row[2] or 0)
        tot = int(row[3] or 0)
        ratio = round((pos / tot) * 100) if tot > 0 else 0
        cells[a_idx][p_idx] = [ratio, tot]
        
    return jsonify({
        "aspects": aspects,
        "periods": periods,
        "cells": cells
    })

@analytics_bp.route('/complaints/stats')
@login_required
@role_required("admin")
def complaint_stats():
    """Aggregate complaint statistics over time."""
    window = request.args.get('window', '30d')
    interval_map = {'7d': '-7 days', '30d': '-30 days', '90d': '-90 days', '1y': '-1 year'}
    sqlite_interval = interval_map.get(window, '-30 days')

    sql = text("""
        SELECT 
            strftime('%Y-%m-%d', created_at) as period,
            severity,
            status,
            COUNT(*) as count
        FROM complaints
        WHERE created_at >= datetime('now', :window_interval)
        GROUP BY period, severity, status
        ORDER BY period ASC
    """)
    
    results = db.session.execute(sql, {"window_interval": sqlite_interval}).fetchall()
    
    data = []
    for row in results:
        data.append({
            "period": row[0],
            "severity": row[1],
            "status": row[2],
            "count": int(row[3])
        })
        
    return jsonify({"data": data})

@analytics_bp.route('/overview')
@login_required
def overview():
    """Top level analytics rendering."""
    from ..models import Product
    default_product = None
    products_list = []
    
    if current_user.role == 'admin':
        products_list = Product.query.order_by(Product.name).all()
        if products_list:
            default_product = str(products_list[0].id)
    elif current_user.role == 'seller':
        products_list = Product.query.filter_by(seller_id=current_user.id).all()
        if products_list:
            default_product = str(products_list[0].id)
            
    return render_template('seller/trends.html', 
                           product_id=default_product, 
                           products=[{'id': str(p.id), 'name': p.name} for p in products_list])
