from sqlmodel import Session
from app.core.bcrypt_encrypter import hash_text
from app.domain.oauth_client.oauth_client_domain import OAuthClientDomain
from app.models.oauth_client import OAuthClient
from app.models.user_oauth_client import UserOAuthClientModel
from app.repositories.oauth_client.ioauth_client_repository import (
    IOAuthClientRepository,
)
from app.services.exceptions import InternalServerError


class OAuthClientRepository(IOAuthClientRepository):
    def __init__(self, session: Session):
        self.session = session

    def save(self, client: OAuthClientDomain) -> OAuthClientDomain:
        try:
            model = OAuthClient.from_domain(client)

            plain_client_secret = client.client_secret
            plain_rat = client.registration_access_token

            model.client_secret = hash_text(plain_text=plain_client_secret)

            if plain_rat:
                model.registration_access_token = hash_text(plain_text=plain_rat)

            self.session.add(model)

            link = UserOAuthClientModel(
                client_id=model.client_id, user_id=client.user_id
            )
            self.session.add(link)

            self.session.commit()
            self.session.refresh(model)
            self.session.refresh(link)

            result_domain = model.to_domain(user_id=client.user_id)
            result_domain.client_secret = plain_client_secret
            result_domain.registration_access_token = plain_rat
        except Exception as e:
            print(e)
            raise InternalServerError("Internal server error")
        return result_domain
