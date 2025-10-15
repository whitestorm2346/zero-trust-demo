from fastapi import FastAPI

app = FastAPI()

@app.get("/public")
def public():
    return {"msg": "hello from B:public"}

@app.get("/private")
def private():
    return {"msg": "secret from B:private"}
