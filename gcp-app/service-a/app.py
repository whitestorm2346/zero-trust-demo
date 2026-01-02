from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import requests
import os
from jose import jwt

DEMO_USERS = {
    "admin": {
        "password": "admin123",
        "role": "admin",
        "email": "admin@example.com"
    },
    "user": {
        "password": "user123",
        "role": "user",
        "email": "user@example.com"
    }
}

app = FastAPI()
SERVICE_B_URL = f"http://{os.getenv('SERVICE_B_HOST')}:{os.getenv('SERVICE_B_PORT')}"

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    return FileResponse("static/index.html")


@app.get("/public")
def public_proxy():
    r = requests.get(f"{SERVICE_B_URL}/public")
    return {
        "from": "service-a",
        "access": "public",
        "service_b_response": r.json() if r.headers.get("content-type","").startswith("application/json") else r.text
    }


from fastapi import Request, HTTPException

def get_identity(request: Request):
    """
    MODE 1: Istio / Envoy 已驗 JWT（x-jwt-claim-*）
    MODE 2: Fallback demo mode，自行 decode Authorization Bearer JWT
    """

    # =========================
    # MODE 1：Istio 已驗（原設計）
    # =========================
    sub = request.headers.get("x-jwt-claim-sub")
    role = request.headers.get("x-jwt-claim-role")
    email = request.headers.get("x-jwt-claim-email")

    if sub:
        print("[AUTH] mode=ISTIO")
        return {
            "sub": sub,
            "role": role,
            "email": email,
        }

    # =========================
    # MODE 2：Fallback（demo 用）
    # =========================
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        print("[AUTH] mode=NONE")
        return {
            "sub": None,
            "role": None,
            "email": None,
        }

    token = auth.split(" ", 1)[1]

    try:
        payload = jwt.decode(
            token,
            key="",
            options={
                "verify_signature": False,  # demo：不驗簽章
                "verify_aud": False,
                "verify_iss": False,
            }
        )

        roles = payload.get("realm_access", {}).get("roles", [])

        print("[AUTH] mode=FALLBACK")
        return {
            "sub": payload.get("sub"),
            "role": roles[0] if roles else None,
            "email": payload.get("email"),
        }

    except Exception as e:
        print("[AUTH] fallback decode failed:", str(e))
        return {
            "sub": None,
            "role": None,
            "email": None,
        }

@app.get("/private")
def private(request: Request):
    user = get_identity(request)

    print(user)

    if not user["sub"]:
        raise HTTPException(status_code=401, detail="Unauthenticated")

    if user["role"] == "admin":
        level = "FULL_ACCESS"
    elif user["role"] == "user":
        level = "LIMITED_ACCESS"
    else:
        raise HTTPException(status_code=403, detail="Forbidden")

    return {
        "user": user,
        "access_level": level
    }



ONPREM_URL = "https://scores-curves-colored-von.trycloudflare.com"

@app.get("/api/onprem/data")
def get_onprem_data():
    try:
        resp = requests.get(ONPREM_URL, timeout=5)
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=str(e))

    if resp.status_code != 200:
        raise HTTPException(
            status_code=resp.status_code,
            detail=resp.text
        )

    # 如果他回 JSON
    if "application/json" in resp.headers.get("content-type", ""):
        return resp.json()

    # 如果他回純文字 / HTML
    return {"data": resp.text}