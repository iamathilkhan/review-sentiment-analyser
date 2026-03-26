from flask import Blueprint

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/overview')
def overview():
    return "Analytics Overview Stub"
