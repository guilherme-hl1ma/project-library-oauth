from pydantic import BaseModel

from app.models.user import UserRole


class UserRegistration(BaseModel):
    name: str
    email: str
    password: str
    role: str | None = UserRole.USER.value


class UserLogin(BaseModel):
    email: str
    password: str
