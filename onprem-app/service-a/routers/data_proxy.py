from fastapi import APIRouter, Depends, HTTPException, status
import httpx

from core.security import get_current_user, require_role
from core.config import SERVICE_B_URL
from schemas.data import ProtectedData

router = APIRouter()


@router.get("/user-data", response_model=ProtectedData)
async def get_user_data(current_user: dict = Depends(get_current_user)):
    """
    一般使用者可存取的資料。
    這裡是由 service-a 幫忙 call service-b 取得資料，再回傳給前端。
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{SERVICE_B_URL}/data/basic",
            headers={"X-User-Name": current_user["username"], "X-User-Role": current_user["role"]},
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    return ProtectedData(source="service-b/basic", payload=resp.json())


@router.get("/admin-data", response_model=ProtectedData)
async def get_admin_data(current_user: dict = Depends(require_role("admin"))):
    """
    僅 admin 可以存取的敏感資料。
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{SERVICE_B_URL}/data/admin",
            headers={"X-User-Name": current_user["username"], "X-User-Role": current_user["role"]},
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    return ProtectedData(source="service-b/admin", payload=resp.json())
