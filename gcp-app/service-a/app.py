from fastapi import FastAPI
import httpx, os

# 可用環境變數覆寫，方便測試
B_HOST = os.getenv("SERVICE_B_HOST", "service-b.default.svc.cluster.local")
B_PORT = os.getenv("SERVICE_B_PORT", "8080")
B = f"http://{B_HOST}:{B_PORT}"

app = FastAPI()

@app.get("/call/public")
def call_public():
    r = httpx.get(f"{B}/public", timeout=5.0)
    return {"via": "A", "status": r.status_code, "body": r.json()}

@app.get("/call/private")
def call_private():
    r = httpx.get(f"{B}/private", timeout=5.0)
    return {"via": "A", "status": r.status_code, "body": r.json()}
