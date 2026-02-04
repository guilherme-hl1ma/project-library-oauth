import secrets
from urllib.parse import urlparse

from fastapi import HTTPException
from app.core.bcrypt_encrypter import hash_text
from app.domain.oauth_client.exceptions import InvalidRedirectURI
from app.domain.oauth_client.oauth_client_domain import OAuthClientDomain
from app.models.oauth_client import OAuthClient
from app.models.user import User
from app.repositories.oauth_client.ioauth_client_repository import (
    IOAuthClientRepository,
)
from app.services.exceptions import ClientNotFound
from app.services.oauth_client.ioauth_client_service import IOAuthClientService


class OAuthClientService(IOAuthClientService):
    def __init__(self, client_repository: IOAuthClientRepository):
        super().__init__()
        self.client_repository = client_repository

    def register_client(self, client: OAuthClientDomain) -> OAuthClientDomain:
        self._validate_metadata(client)
        return self.client_repository.save(client=client)

    def rotate_secret(self, client_id: str, requested_by: User) -> str:
        client = self.client_repository.get_by_id(client_id)

        if client is None:
            raise ClientNotFound("Client not found")

        self.client_repository.check_user_permission(client.client_id, requested_by)

        new_secret = secrets.token_urlsafe(32)
        hashed = hash_text(new_secret)

        self.client_repository.update_secret(client_id, hashed)

        return new_secret

    def _validate_metadata(self, client: OAuthClientDomain):
        if not client.redirect_uris:
            raise InvalidRedirectURI("At least one redirect_uri is required")

        for uri in client.redirect_uris:
            parsed = urlparse(uri)

            # Productive validation
            # if parsed.scheme not in ["https"] and parsed.hostname != "localhost":
            #    raise InvalidRedirectURI(f"URI {uri} must use HTTPS")

            if parsed.fragment:
                raise InvalidRedirectURI(f"URI {uri} must not contain fragments (#)")

            if not parsed.netloc:
                raise InvalidRedirectURI(f"URI {uri} must be an absolute URL")
