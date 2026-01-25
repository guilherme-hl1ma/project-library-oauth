from abc import ABC, abstractmethod

from app.domain.oauth_client.oauth_client_domain import OAuthClientDomain


class IOAuthClientService(ABC):
    @abstractmethod
    def register_client(self, client: OAuthClientDomain) -> OAuthClientDomain:
        pass
