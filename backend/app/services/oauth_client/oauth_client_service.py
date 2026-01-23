from app.domain.oauth_client_domain import OAuthClient
from app.models import oauth_client
from app.repositories.oauth_client.ioauth_client_repository import (
    IOAuthClientRepository,
)
from app.services.oauth_client.ioauth_client_service import IOAuthClientService


class OAuthClientService(IOAuthClientService):
    def __init__(self, client_repository: IOAuthClientRepository):
        super().__init__()
        self.client_repository = client_repository

    def register_client(self, client: OAuthClient) -> OAuthClient:
        oauth_client = self.client_repository.save(client)
        return oauth_client
