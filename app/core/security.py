import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from flask import current_app

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a bcrypt hashed password."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(user_id: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=current_app.config.get('JWT_EXPIRY_MINUTES', 60))
    
    to_encode = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }
    
    encoded_jwt = jwt.encode(
        to_encode, 
        current_app.config['JWT_SECRET'], 
        algorithm="HS256"
    )
    return encoded_jwt

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode a JWT access token."""
    try:
        decoded = jwt.decode(
            token, 
            current_app.config['JWT_SECRET'], 
            algorithms=["HS256"]
        )
        return decoded
    except Exception:
        return None

def encrypt_pii(value: str) -> str:
    """Encrypt PII using Fernet."""
    if not value:
        return value
    f = Fernet(current_app.config['PII_KEY'].encode())
    return f.encrypt(value.encode()).decode()

def decrypt_pii(value: str) -> str:
    """Decrypt PII using Fernet."""
    if not value:
        return value
    f = Fernet(current_app.config['PII_KEY'].encode())
    return f.decrypt(value.encode()).decode()
