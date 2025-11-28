# onprem/service-a/app.py
from fastapi import FastAPI, Header, HTTPException
from typing import Optional

from security import verify_service_token

app = FastAPI(title="On-Prem Service A")


@app.get("/echo")
async def echo(
    x_service_id: Optional[str] = Header(None, alias="X-Service-Id"),
    x_service_token: Optional[str] = Header(None, alias="X-Service-Token"),
):
    """
    簡單示範：中間層 service
    - 驗證來自 gateway 的 service token
    - 目前只是回 echo，未串 service-b
    """
    if not x_service_id or not x_service_token:
        raise HTTPException(status_code=401, detail="Missing service identity")

    payload = verify_service_token(x_service_token, expected_target="service-a")

    return {
        "endpoint": "/echo",
        "caller_service": x_service_id,
        "token_payload": payload,
    }
