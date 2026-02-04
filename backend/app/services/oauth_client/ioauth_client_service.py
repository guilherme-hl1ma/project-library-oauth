from abc import ABC, abstractmethod

from app.domain.oauth_client.oauth_client_domain import OAuthClientDomain
from app.models.user import User


class IOAuthClientService(ABC):
    @abstractmethod
    def register_client(self, client: OAuthClientDomain) -> OAuthClientDomain:
        pass

    @abstractmethod
    def rotate_secret(self, client_id: str, requested_by: User) -> str:
        pass
