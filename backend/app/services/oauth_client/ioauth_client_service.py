from abc import ABC, abstractmethod

from app.domain.oauth_client_domain import OAuthClient


class IOAuthClientService(ABC):
    @abstractmethod
    def register_client(self, client: OAuthClient) -> OAuthClient:
        pass
