from pydantic import BaseModel


class BasicData(BaseModel):
    message: str
    user: str


class AdminData(BaseModel):
    message: str
    user: str
    secret_flag: bool
