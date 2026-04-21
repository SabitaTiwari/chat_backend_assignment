from pydantic import BaseModel
from typing import Literal


class SignupRequest(BaseModel):
    username: str
    email: str
    password: str
    role: Literal["admin", "user"] = "user"


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str