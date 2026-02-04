from abc import ABC, abstractmethod

from app.domain.oauth_client.oauth_client_domain import OAuthClientDomain
from app.models.oauth_client import OAuthClient
from app.models.user import User


class IOAuthClientRepository(ABC):
    @abstractmethod
    def save(self, client: OAuthClientDomain) -> OAuthClientDomain:
        pass

    @abstractmethod
    def get_by_id(self, client_id: str) -> OAuthClient | None:
        pass

    @abstractmethod
    def update_secret(self, client_id: str, hashed_secret: str):
        pass

    @abstractmethod
    def check_user_permission(self, client_id: str, requested_by: User):
        pass
