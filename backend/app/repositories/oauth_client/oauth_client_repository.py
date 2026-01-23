from sqlmodel import Session
from app.domain.oauth_client_domain import OAuthClient
from app.models.oauth_client import OAuthClientModel
from app.repositories.oauth_client.ioauth_client_repository import (
    IOAuthClientRepository,
)


class OAuthClientRepository(IOAuthClientRepository):
    def __init__(self, session: Session):
        self.session = session

    def save(self, client: OAuthClient) -> OAuthClient:
        oauth_client = OAuthClientModel.from_domain(client=client)
        self.session.add(oauth_client)
        return client
