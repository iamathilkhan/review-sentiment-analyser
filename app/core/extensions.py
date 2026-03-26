from flask_migrate import Migrate
from flask_redis import FlaskRedis
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from .database import db

migrate = Migrate()
redis_client = FlaskRedis()
login_manager = LoginManager()
csrf = CSRFProtect()

def init_extensions(app):
    """Initialize Flask extensions."""
    db.init_app(app)
    migrate.init_app(app, db)
    redis_client.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Login manager configuration
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        from ..models.user import User
        return User.query.get(user_id)
