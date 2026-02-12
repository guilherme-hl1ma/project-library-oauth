from typing import Optional
from sqlmodel import Field, SQLModel
import uuid

class Project(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str = Field(nullable=False)
    description: Optional[str] = Field(default=None)
    user_id: str = Field(foreign_key="user.id", nullable=False)
