from fastapi import Header, HTTPException, status


async def verify_internal_call(
    x_user_name: str | None = Header(default=None, alias="X-User-Name"),
    x_user_role: str | None = Header(default=None, alias="X-User-Role"),
):
    """
    驗證這個呼叫是從 service-a 來的，
    並且帶有 user 的基本資訊（角色）。
    Demo 版本用 Header 帶，之後可以改成 JWT / mTLS / SPIFFE 等。
    """
    if x_user_name is None or x_user_role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing internal identity headers",
        )
    return {"username": x_user_name, "role": x_user_role}
