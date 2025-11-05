from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import httpx, os

B_HOST = os.getenv("SERVICE_B_HOST", "service-b.default.svc.cluster.local")
B_PORT = os.getenv("SERVICE_B_PORT", "8080")
B = f"http://{B_HOST}:{B_PORT}"

# 假裝這是資料庫查出來的帳密
USERS = {
    "alice": "pass123",
    "bob": "pass456",
}

app = FastAPI()
security = HTTPBasic()

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    username = credentials.username
    password = credentials.password
    if username in USERS and USERS[username] == password:
        return username
    raise HTTPException(status_code=401, detail="invalid credentials")


def _safe_request(url: str, method: str = "GET"):
    try:
        with httpx.Client(timeout=5.0) as client:
            if method == "GET":
                resp = client.get(url)
            else:
                resp = client.request(method, url)

        # 不管對方是 200 還是 403，都把資訊包回去
        return {
            "ok": resp.status_code == 200,
            "status_code": resp.status_code,
            "headers": dict(resp.headers),
            "body": resp.text,
            "target": url,
        }
    except Exception as e:
        # 真的連不到才是我們的 500
        return {
            "ok": False,
            "error": str(e),
            "target": url,
        }

# 掛載 /static 目錄
app.mount("/static", StaticFiles(directory="static"), name="static")

# 首頁直接回傳 static/index.html
@app.get("/")
def home():
    return FileResponse("static/index.html")

@app.get("/call/public")
def call_public():
    return _safe_request(f"{B}/public")

@app.get("/call/private")
def call_private(user: str = Depends(get_current_user)):
    # 走到這裡表示「應用層授權」已通過
    result = _safe_request(f"{B}/private")
    # 把是哪個 user 拿到的也一起回去，demo 時比較好講
    result["app_user"] = user
    return result

@app.get("/call/ext")
def call_ext():
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get("http://ext-http.ext-demo.svc.cluster.local")
        return {
            "ok": resp.status_code == 200,
            "status_code": resp.status_code,
            "body": resp.text,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}
