from urllib.parse import urlparse
from app.domain.exceptions import InvalidRedirectURI
from app.domain.oauth_client.oauth_client_domain import OAuthClientDomain
from app.repositories.oauth_client.ioauth_client_repository import (
    IOAuthClientRepository,
)
from app.services.oauth_client.ioauth_client_service import IOAuthClientService


class OAuthClientService(IOAuthClientService):
    def __init__(self, client_repository: IOAuthClientRepository):
        super().__init__()
        self.client_repository = client_repository

    def register_client(self, client: OAuthClientDomain) -> OAuthClientDomain:
        self._validate_metadata(client)
        return self.client_repository.save(client=client)

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
