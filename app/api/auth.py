from flask import Blueprint, request, jsonify, make_response, current_app, render_template
from ..core.database import db
from ..core.security import hash_password, verify_password, create_access_token, encrypt_pii, decrypt_pii
from ..core.auth_decorators import login_required, role_required, rate_limit
from ..models.user import User
from datetime import timedelta

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET'])
def login_page():
    """Render the login page."""
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET'])
def register_page():
    """Render the registration page."""
    return render_template('auth/register.html')

@auth_bp.route('/register', methods=['POST'])
@rate_limit(limit=5, window=3600)
def register():
    """Register a new customer or seller."""
    data = request.get_json()
    
    # Validation
    required = ['name', 'email', 'password', 'role']
    if not all(k in data for k in required):
        return jsonify({"message": "Missing required fields"}), 400
        
    if data['role'] not in ['customer', 'seller']:
        return jsonify({"message": "Invalid role. Only customer or seller can register."}), 400
        
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"message": "Email already registered"}), 400
        
    # Create user
    user = User(
        name=data['name'],
        email=data['email'],
        hashed_password=hash_password(data['password']),
        role=data['role'],
        phone_encrypted=encrypt_pii(data.get('phone')),
        address_encrypted=encrypt_pii(data.get('address'))
    )
    
    db.session.add(user)
    db.session.commit()
    
    # Create token
    token = create_access_token(user.id, user.role)
    
    response = make_response(jsonify({
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    }), 201)
    
    # Set cookie
    response.set_cookie(
        'access_token',
        token,
        httponly=True,
        secure=not current_app.debug,
        samesite='Lax',
        max_age=3600
    )
    
    return response

@auth_bp.route('/login', methods=['POST'])
@rate_limit(limit=10, window=60)
def login():
    """Login and receive a JWT."""
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"message": "Missing email or password"}), 400
        
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not verify_password(data['password'], user.hashed_password):
        return jsonify({"message": "Invalid credentials"}), 401
        
    if not user.is_active:
        return jsonify({"message": "Account is deactivated"}), 403
        
    # Create token
    token = create_access_token(user.id, user.role)
    
    response = make_response(jsonify({
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    }))
    
    # Set cookie
    response.set_cookie(
        'access_token',
        token,
        httponly=True,
        secure=not current_app.debug,
        samesite='Lax',
        max_age=3600
    )
    
    return response

@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """Clear the access token cookie."""
    from flask import redirect, url_for, flash
    response = make_response(redirect(url_for('auth.login')))
    response.delete_cookie('access_token')
    flash("You have been logged out.", "info")
    return response

@auth_bp.route('/me', methods=['GET'])
@login_required
def me():
    """Get current user profile."""
    from flask import g
    user = g.current_user
    return jsonify({
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "phone": decrypt_pii(user.phone_encrypted),
        "address": decrypt_pii(user.address_encrypted),
        "created_at": user.created_at.isoformat()
    })

@auth_bp.route('/admin/create', methods=['POST'])
@login_required
@role_required('admin')
def create_admin():
    """Create a new admin account (Admin only)."""
    data = request.get_json()
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"message": "Email already registered"}), 400
        
    user = User(
        name=data['name'],
        email=data['email'],
        hashed_password=hash_password(data['password']),
        role='admin'
    )
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({"message": "Admin account created", "id": user.id}), 201
