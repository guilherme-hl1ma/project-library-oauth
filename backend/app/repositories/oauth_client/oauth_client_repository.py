from sqlmodel import Session
from app.domain.oauth_client.oauth_client_domain import OAuthClient
from app.models.oauth_client import OAuthClientModel
from app.repositories.oauth_client.ioauth_client_repository import (
    IOAuthClientRepository,
)
from app.services.exceptions import InternalServerError


class OAuthClientRepository(IOAuthClientRepository):
    def __init__(self, session: Session):
        self.session = session

    def save(self, client: OAuthClient) -> OAuthClient:
        model = OAuthClientModel.from_domain(client)
        try:
            self.session.add(model)
            self.session.commit()
            self.session.refresh(model)
        except:
            raise InternalServerError("Internal server error")
        return model.to_domain()
