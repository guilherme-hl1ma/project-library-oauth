from abc import ABC, abstractmethod

from app.domain.oauth_client.oauth_client_domain import OAuthClient


class IOAuthClientRepository(ABC):
    @abstractmethod
    def save(self, client: OAuthClient) -> OAuthClient:
        pass
