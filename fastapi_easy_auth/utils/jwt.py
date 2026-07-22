from datetime import datetime, timedelta
from typing import Optional
from jose import jwt

def create_access_token(data: dict, secret_key: str, algorithm: str = "HS256", expires_delta: Optional[timedelta] = None) -> str:
    """Create a new JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    return encoded_jwt

def decode_token(token: str, secret_key: str, algorithm: str = "HS256") -> Optional[dict]:
    """Decode a JWT token. Returns the payload or None if invalid."""
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm], options={"verify_exp": True})
        return payload
    except Exception:
        return None
