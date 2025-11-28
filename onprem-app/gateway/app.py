# onprem/gateway/app.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import os
import requests

from security import (
    User,
    create_user_access_token,
    verify_user_access_token,
    create_service_token,
)

app = FastAPI(title="On-Prem Zero Trust Gateway")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Demo 用：假資料庫
FAKE_USERS_DB = {
    "alice": {"username": "alice", "password": "alice123", "role": "admin"},
    "bob": {"username": "bob", "password": "bob123", "role": "viewer"},
}

# 從環境變數讀 Service-B URL
SERVICE_B_BASE_URL = os.getenv("SERVICE_B_URL", "http://service-b:8000")


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    payload = verify_user_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return User(username=payload["sub"], role=payload["role"])


@app.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    user_record = FAKE_USERS_DB.get(req.username)
    if not user_record or user_record["password"] != req.password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    user = User(username=user_record["username"], role=user_record["role"])
    token = create_user_access_token(user)
    return TokenResponse(access_token=token)


@app.get("/call/local/public")
async def call_local_public(current_user: User = Depends(get_current_user)):
    """
    Gateway 代表 user 去 call Service-B /public
    - 產生 service token，涵蓋 service identity + user claims
    """
    user_claims = {"username": current_user.username, "role": current_user.role}

    service_token = create_service_token(
        caller_service="gateway",
        target_service="service-b",
        user_claims=user_claims,
    )

    try:
        r = requests.get(
            f"{SERVICE_B_BASE_URL}/public",
            headers={
                "X-Service-Id": "gateway",
                "X-Service-Token": service_token,
            },
            timeout=3,
        )
        r.raise_for_status()
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Call service-b /public failed: {e}")

    return {
        "from": "gateway",
        "user": user_claims,
        "service_b_response": r.json(),
    }


@app.get("/call/local/private")
async def call_local_private(current_user: User = Depends(get_current_user)):
    """
    Gateway 代表 user 去 call Service-B /private
    - Service-B 在那邊套用「service identity + user role」雙重授權
    """
    user_claims = {"username": current_user.username, "role": current_user.role}

    service_token = create_service_token(
        caller_service="gateway",
        target_service="service-b",
        user_claims=user_claims,
    )

    try:
        r = requests.get(
            f"{SERVICE_B_BASE_URL}/private",
            headers={
                "X-Service-Id": "gateway",
                "X-Service-Token": service_token,
            },
            timeout=3,
        )
        r.raise_for_status()
    except requests.RequestException as e:
        raise HTTPException(
            status_code=502, detail=f"Call service-b /private failed: {e}"
        )

    return {
        "from": "gateway",
        "user": user_claims,
        "service_b_response": r.json(),
    }
