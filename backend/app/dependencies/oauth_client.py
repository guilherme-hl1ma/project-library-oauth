from fastapi import Depends
from sqlmodel import Session
from app.core.database import get_session
from app.repositories.oauth_client.ioauth_client_repository import (
    IOAuthClientRepository,
)
from app.repositories.oauth_client.oauth_client_repository import OAuthClientRepository
from app.services.oauth_client.ioauth_client_service import IOAuthClientService
from app.services.oauth_client.oauth_client_service import OAuthClientService


def get_oauth_client_repository(
    session: Session = Depends(get_session),
) -> IOAuthClientRepository:
    return OAuthClientRepository(session=session)


def get_oauth_client_service(
    repo: IOAuthClientRepository = Depends(get_oauth_client_repository),
) -> IOAuthClientService:
    return OAuthClientService(repo)
