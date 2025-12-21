from pydantic import BaseModel
from typing import Any


class ProtectedData(BaseModel):
    source: str
    payload: Any
