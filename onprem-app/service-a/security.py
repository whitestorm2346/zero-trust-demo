# onprem/service-a/security.py
from typing import Dict
import os
import jwt
from fastapi import HTTPException, status

SERVICE_SHARED_SECRET = os.getenv(
    "SERVICE_SHARED_SECRET", "dev_service_shared_secret_change_me"
)
SERVICE_TOKEN_ALGORITHM = "HS256"


def verify_service_token(token: str, expected_target: str = "service-a") -> Dict:
    try:
        payload = jwt.decode(
            token, SERVICE_SHARED_SECRET, algorithms=[SERVICE_TOKEN_ALGORITHM]
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

    target = payload.get("sub")
    if target != expected_target:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token target mismatch",
        )

    return payload
