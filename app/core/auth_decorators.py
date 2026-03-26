from functools import wraps
from flask import request, g, current_app, abort, jsonify
from .security import decode_token
import time

def login_required(f):
    """Decorator to require authentication via JWT."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Check Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(" ")[1]
        
        # Check cookie
        if not token:
            token = request.cookies.get('access_token')
            
        if not token:
            abort(401, description="Authentication token is missing")
            
        payload = decode_token(token)
        if not payload:
            abort(401, description="Invalid or expired token")
            
        from ..models.user import User
        user = User.query.get(payload['sub'])
        if not user or not user.is_active:
            abort(401, description="User not found or inactive")
            
        g.current_user = user
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    """Decorator to require specific roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'current_user'):
                abort(401, description="Authentication required")
                
            if g.current_user.role not in roles:
                abort(403, description="Insufficient permissions")
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def rate_limit(limit=10, window=3600):
    """Decorator to rate limit requests using Redis."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from .extensions import redis_client
            
            # Use user_id if logged in, otherwise use IP
            user_id = getattr(g, 'current_user', None)
            if user_id:
                key = f"rate_limit:{user_id.id}:{f.__name__}"
            else:
                key = f"rate_limit:{request.remote_addr}:{f.__name__}"
                
            try:
                current = redis_client.get(key)
                if current and int(current) >= limit:
                    abort(429, description="Too many requests — please wait before trying again")
                    
                pipe = redis_client.pipeline()
                pipe.incr(key)
                pipe.expire(key, window)
                pipe.execute()
            except Exception as e:
                # Fallback if Redis is down (log it in a real app)
                current_app.logger.warning(f"Redis error in rate_limit: {e}")
                pass
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator
