import enum
from sqlmodel import Field, SQLModel


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class User(SQLModel, table=True):
    id: str = Field(primary_key=True, nullable=False)
    email: str = Field(unique=True, nullable=False)
    password: str = Field(nullable=False)
    role: str = Field(nullable=False, default=UserRole.USER.value)
