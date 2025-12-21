from fastapi import FastAPI

from routers import data

app = FastAPI(
    title="On-Prem Zero Trust Demo - Service B",
    description="Service-B 提供後端受保護的資料，只接受從 service-a 轉來的請求",
    version="1.0.0",
)

app.include_router(data.router, prefix="/data", tags=["data"])
