from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import requests
import os
from datetime import datetime, timedelta, timezone

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
    return {
        "sub": request.headers.get("x-jwt-claim-sub"),
        "role": request.headers.get("x-jwt-claim-role"),
        "email": request.headers.get("x-jwt-claim-email"),
    }

@app.get("/private")
def private(request: Request):
    user = get_identity(request)

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



