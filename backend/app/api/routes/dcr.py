from typing import Annotated
from fastapi import Depends
from fastapi.routing import APIRouter

from app.dependencies.auth import get_user_required
from app.dependencies.oauth_client import get_oauth_client_service
from app.domain.oauth_client.oauth_client_domain import OAuthClientDomain
from app.models.user import User
from app.schemas.dcr.dcr import ClientMetadataRegister, ClientMetadataResponse
from app.services.oauth_client.ioauth_client_service import IOAuthClientService


router = APIRouter(prefix="/dcr", tags=["Dynamic Client Registration"])


@router.post("/register")
def register_client(
    current_user: Annotated[User, Depends(get_user_required)],
    oauth_client_service: Annotated[
        IOAuthClientService, Depends(get_oauth_client_service)
    ],
    payload: ClientMetadataRegister,
) -> ClientMetadataResponse:

    domain_client = OAuthClientDomain.create_new(
        payload=payload, current_user=current_user
    )

    register_response = oauth_client_service.register_client(client=domain_client)

    response = ClientMetadataResponse(
        client_id=register_response.client_id,
        client_secret=register_response.client_secret,
        issued_at=register_response.issued_at,
        client_name=register_response.client_name,
        redirect_uris=register_response.redirect_uris,
    )

    return response


@router.post("/{client_id}/rotate-secret")
def rotate_client_secret(
    client_id: str,
    current_user: Annotated[User, Depends(get_user_required)],
    oauth_client_service: Annotated[
        IOAuthClientService, Depends(get_oauth_client_service)
    ],
):
    new_secret = oauth_client_service.rotate_secret(
        client_id=client_id,
        requested_by=current_user,
    )

    return {
        "client_id": client_id,
        "client_secret": new_secret,
    }
