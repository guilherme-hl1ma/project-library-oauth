from sqlmodel import Field, SQLModel


class UserOAuthClientModel(SQLModel, table=True):
    __tablename__ = "user_oauth_client"  # type: ignore

    client_id: str = Field(
        foreign_key="oauth_client.client_id", primary_key=True, nullable=False
    )
    user_id: str = Field(foreign_key="user.id", primary_key=True, nullable=False)
    role: str = Field(nullable=False, default="admin")
