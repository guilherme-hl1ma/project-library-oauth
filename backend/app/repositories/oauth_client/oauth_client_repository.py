from sqlalchemy import update
from sqlmodel import Session, col, select
from app.core.bcrypt_encrypter import hash_text
from app.domain.oauth_client.oauth_client_domain import OAuthClientDomain
from app.models.oauth_client import OAuthClient
from app.models.user import User
from app.models.user_oauth_client import UserOAuthClientModel
from app.repositories.oauth_client.ioauth_client_repository import (
    IOAuthClientRepository,
)
from app.services.exceptions import ForbiddenError, InternalServerError


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

    def get_by_id(self, client_id: str) -> OAuthClient | None:
        try:
            return self.session.get(OAuthClient, client_id)
        except Exception as e:
            print(e)
            raise InternalServerError("Internal server error")

    def update_secret(self, client_id: str, hashed_secret: str):
        try:
            stmt = (
                update(OAuthClient)
                .filter_by(client_id=client_id)
                .values(client_secret=hashed_secret)
            )
            self.session.exec(stmt)
            self.session.commit()
        except Exception as e:
            print(e)
            raise InternalServerError("Internal server error")

    def check_user_permission(self, client_id: str, requested_by: User):
        stmt = select(UserOAuthClientModel).where(
            col(UserOAuthClientModel.client_id) == client_id,
            col(UserOAuthClientModel.user_id) == requested_by.id,
        )

        result = self.session.exec(stmt).first()
        if result is None:
            raise ForbiddenError("User cannot access the client.")
