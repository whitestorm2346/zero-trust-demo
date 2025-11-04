from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

# 掛載靜態檔
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def home():
    return FileResponse("static/index.html")

# 供 service-a 呼叫的 API
@app.get("/public")
def public():
    return {"msg": "hello from B:public"}

@app.get("/private")
def private():
    return {"msg": "secret from B:private"}
