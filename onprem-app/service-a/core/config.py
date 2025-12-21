import os

# 從環境變數讀取設定，沒有的話用預設值
SERVICE_B_URL = os.getenv("SERVICE_B_URL", "http://localhost:8001")
JWT_SECRET = os.getenv("JWT_SECRET", "supersecret")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
