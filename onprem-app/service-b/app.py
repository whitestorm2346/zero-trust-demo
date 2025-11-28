# onprem/service-b/app.py
from fastapi import FastAPI, Header, HTTPException, status
from typing import Optional

from security import (
    verify_service_token,
    extract_user_claims_from_service_token_payload,
)

app = FastAPI(title="On-Prem Service B")


@app.get("/public")
async def public_endpoint(
    x_service_id: Optional[str] = Header(None, alias="X-Service-Id"),
    x_service_token: Optional[str] = Header(None, alias="X-Service-Token"),
):
    """
    /public：
    - 仍然要求 service token（Policy #4）
    - 但不檢查 user role
    """
    if not x_service_id or not x_service_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing service identity",
        )

    payload = verify_service_token(x_service_token)
    user_claims = extract_user_claims_from_service_token_payload(payload)

    return {
        "endpoint": "/public",
        "caller_service": x_service_id,
        "user": user_claims,
        "message": "public data from service-b",
    }


@app.get("/private")
async def private_endpoint(
    x_service_id: Optional[str] = Header(None, alias="X-Service-Id"),
    x_service_token: Optional[str] = Header(None, alias="X-Service-Token"),
):
    """
    /private：
    - 需要合法的 service identity (Policy #4)
    - 還要 user role == 'admin' (Policy #5)
    """
    if not x_service_id or not x_service_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing service identity",
        )

    payload = verify_service_token(x_service_token)
    user_claims = extract_user_claims_from_service_token_payload(payload)

    role = user_claims.get("role")
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User role '{role}' is not allowed to access /private",
        )

    return {
        "endpoint": "/private",
        "caller_service": x_service_id,
        "user": user_claims,
        "message": "*** TOP SECRET *** private data from service-b",
    }
