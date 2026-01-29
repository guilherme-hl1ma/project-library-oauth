from dataclasses import dataclass
import secrets
import time
import uuid

from app.models.user import User
from app.schemas.dcr.dcr import ClientMetadataRegister


@dataclass
class OAuthClientDomain:
    client_id: str
    client_secret: str
    redirect_uris: list[str]
    grant_types: list[str]
    user_id: str
    client_name: str | None
    issued_at: int
    registration_access_token: str | None = None
    software_id: str | None = None
    is_active: bool = True

    @classmethod
    def create_new(
        cls, payload: ClientMetadataRegister, current_user: User
    ) -> "OAuthClientDomain":
        return cls(
            client_id=str(uuid.uuid4()),
            client_secret=secrets.token_urlsafe(32),
            redirect_uris=payload.redirect_uris,
            user_id=current_user.id,
            grant_types=[gt for gt in payload.grant_types],
            client_name=payload.client_name,
            issued_at=int(time.time()),
            registration_access_token=secrets.token_urlsafe(32),
            software_id=str(uuid.uuid4()),
            is_active=True,
        )
