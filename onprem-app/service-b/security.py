# onprem/service-b/security.py
from typing import Dict
import os
import jwt
from fastapi import HTTPException, status

SERVICE_SHARED_SECRET = os.getenv(
    "SERVICE_SHARED_SECRET", "dev_service_shared_secret_change_me"
)
SERVICE_TOKEN_ALGORITHM = "HS256"

# 哪些 service 可以 call 我
ALLOWED_CALLER_SERVICES = {"gateway"}  # 之後你想加 service-a 再加上去


def verify_service_token(
    token: str,
    expected_target: str = "service-b",
) -> Dict:
    """
    驗證 Service Token：
    - 簽章是否正確
    - type == service_token
    - iss 是否在允許的 caller list
    - sub 是否是我 (service-b)
    """
    try:
        payload = jwt.decode(
            token,
            SERVICE_SHARED_SECRET,
            algorithms=[SERVICE_TOKEN_ALGORITHM],
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid service token",
        )

    if payload.get("type") != "service_token":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    issuer = payload.get("iss")
    target = payload.get("sub")
    if issuer not in ALLOWED_CALLER_SERVICES or target != expected_target:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Caller service not allowed",
        )

    return payload


def extract_user_claims_from_service_token_payload(payload: Dict) -> Dict:
    """從 service token payload 拿出 user claims"""
    return payload.get("user", {})
