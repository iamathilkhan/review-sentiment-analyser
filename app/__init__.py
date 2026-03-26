from flask import Flask
from config import config_by_name
from .core.extensions import init_extensions
from datetime import datetime

def create_app(config_name="development"):
    """Flask application factory."""
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])
    
    # Initialize extensions
    init_extensions(app)
    
    # Import models to register with SQLAlchemy metadata
    from . import models
    from .api.auth import auth_bp
    from .api.reviews import reviews_bp
    from .api.analytics import analytics_bp
    from .api.admin import admin_bp
    from .api.seller import seller_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(reviews_bp, url_prefix='/reviews')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(seller_bp, url_prefix='/seller')
    
    @app.route('/')
    def index():
        from flask import redirect, url_for
        return redirect(url_for('reviews.index'))
    
    # Jinja2 globals
    @app.context_processor
    def inject_now():
        from datetime import datetime
        return {
            'now': datetime.utcnow(),
            'current_year': datetime.utcnow().year
        }

    @app.context_processor
    def utility_processor():
        def format_datetime(value, format="%Y-%m-%d %H:%M"):
            if value is None:
                return ""
            return value.strftime(format)
        
        return {
            'current_year': datetime.utcnow().year,
            'format_datetime': format_datetime
        }
    
    return app
