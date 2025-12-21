from fastapi import APIRouter, Depends, HTTPException, status

from core.security import verify_internal_call
from schemas.data import BasicData, AdminData

router = APIRouter()


@router.get("/basic", response_model=BasicData)
async def basic_data(caller: dict = Depends(verify_internal_call)):
    """
    一般資料：所有經過 service-a 並帶正確 header 的使用者都可取得。
    """
    return BasicData(
        message="This is basic data from service-b.",
        user=caller["username"],
    )


@router.get("/admin", response_model=AdminData)
async def admin_data(caller: dict = Depends(verify_internal_call)):
    """
    高權限資料：只有 role=admin 才能存取。
    """
    if caller["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can access admin data from service-b.",
        )

    return AdminData(
        message="This is ADMIN data from service-b.",
        user=caller["username"],
        secret_flag=True,
    )
