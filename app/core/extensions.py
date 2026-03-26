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
        import uuid
        try:
            return db.session.get(User, uuid.UUID(user_id))
        except (ValueError, TypeError, AttributeError):
            return None

    @login_manager.request_loader
    def load_user_from_request(request):
        # First, try to get the bird from the cookie
        token = request.cookies.get('access_token')
        
        # If not in cookie, try the Authorization header
        if not token:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]
        
        if token:
            from .security import decode_token
            from ..models.user import User
            import uuid
            payload = decode_token(token)
            if payload and 'sub' in payload:
                try:
                    user_id = uuid.UUID(payload['sub'])
                    return db.session.get(User, user_id)
                except (ValueError, TypeError, AttributeError):
                    return None
        return None
