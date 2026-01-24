from sqlalchemy import JSON
from sqlmodel import Column, Field, SQLModel

from app.domain.oauth_client.oauth_client_domain import OAuthClient


class OAuthClientModel(SQLModel, table=True):
    client_id: str = Field(primary_key=True, nullable=False)
    client_secret: str = Field(nullable=False)
    redirect_uris: list[str] = Field(sa_column=Column(JSON, nullable=False))
    client_name: str | None = Field(nullable=True)
    grant_types: list[str] = Field(sa_column=Column(JSON, nullable=False))
    registration_access_token: str | None = Field(nullable=True, index=True)
    issued_at: int = Field(nullable=False)
    software_id: str | None = Field(nullable=True)
    is_active: bool = Field(default=True)

    def to_domain(self) -> OAuthClient:
        return OAuthClient(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uris=self.redirect_uris,
            grant_types=self.grant_types,
            client_name=self.client_name,
            issued_at=self.issued_at,
            registration_access_token=self.registration_access_token,
            software_id=self.software_id,
            is_active=self.is_active,
        )

    @classmethod
    def from_domain(cls, client: OAuthClient) -> "OAuthClientModel":
        return cls(
            client_id=client.client_id,
            client_secret=client.client_secret,
            redirect_uris=client.redirect_uris,
            grant_types=client.grant_types,
            client_name=client.client_name,
            issued_at=client.issued_at,
            registration_access_token=client.registration_access_token,
            software_id=client.software_id,
            is_active=client.is_active,
        )
