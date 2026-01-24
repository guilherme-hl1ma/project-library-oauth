from dataclasses import dataclass


@dataclass
class OAuthClient:
    client_id: str
    client_secret: str
    redirect_uris: list[str]
    grant_types: list[str]
    client_name: str | None
    issued_at: int
    registration_access_token: str | None = None
    software_id: str | None = None
    is_active: bool = True
