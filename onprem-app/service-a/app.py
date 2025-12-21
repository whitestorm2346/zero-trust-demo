from fastapi import FastAPI

from routers import public, auth, data_proxy

app = FastAPI(
    title="On-Prem Zero Trust Demo - Service A",
    description="Service-A 作為對外入口，提供 Swagger UI、身份驗證與對 service-b 的代理",
    version="1.0.0",
)

# 路由註冊
app.include_router(public.router, prefix="/public", tags=["public"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(data_proxy.router, prefix="/data", tags=["data"])
