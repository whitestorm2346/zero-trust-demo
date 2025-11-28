# onprem/gateway/security.py
from datetime import datetime, timedelta
from typing import Optional, Dict

import os
import jwt
from pydantic import BaseModel

# === User JWT ===
JWT_SECRET = os.getenv("JWT_SECRET", "dev_jwt_secret_change_me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 30

# === Service Token (Gateway <-> Service-B 共用) ===
SERVICE_SHARED_SECRET = os.getenv(
    "SERVICE_SHARED_SECRET", "dev_service_shared_secret_change_me"
)
SERVICE_TOKEN_ALGORITHM = "HS256"


class User(BaseModel):
    username: str
    role: str


def create_user_access_token(user: User) -> str:
    """產生給 user (browser/postman) 使用的 User JWT"""
    now = datetime.utcnow()
    payload = {
        "sub": user.username,
        "role": user.role,
        "iat": now,
        "exp": now + timedelta(minutes=JWT_EXPIRE_MINUTES),
        "iss": "onprem-gateway",
        "type": "user_access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_user_access_token(token: str) -> Optional[Dict]:
    """驗證 User JWT，成功回傳 payload，失敗回傳 None"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "user_access":
            return None
        return payload
    except jwt.PyJWTError:
        return None


def create_service_token(
    caller_service: str,
    target_service: str,
    user_claims: Dict,
    ttl_seconds: int = 60,
) -> str:
    """
    產生 Service Token（Gateway -> Service-B）
    - iss = caller_service
    - sub = target_service
    - 夾 user claims (role, username)
    """
    now = datetime.utcnow()
    payload = {
        "iss": caller_service,
        "sub": target_service,
        "iat": now,
        "exp": now + timedelta(seconds=ttl_seconds),
        "type": "service_token",
        "user": user_claims,
    }
    return jwt.encode(payload, SERVICE_SHARED_SECRET, algorithm=SERVICE_TOKEN_ALGORITHM)
